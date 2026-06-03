"""
retrieve.py — Recupera chunks relevantes e monta o prompt para o Claude.

Uso como CLI:
    python retrieve.py "Qual o prazo de devolução?"
    python retrieve.py "Frete para 600kg para Manaus?" --top 5
    python retrieve.py "Qual o SLA do cliente Gold?" --prompt-only

Uso como módulo:
    from retrieve import retrieve, assemble_prompt
    chunks = retrieve("Qual o prazo de devolução?")
    print(assemble_prompt("Qual o prazo de devolução?", chunks))
"""

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).parent))

import re

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    DEDUPLICATE_VERSIONS,
    DOMAIN_TERM_EXPANSIONS,
    EMBEDDING_MODEL,
    MIN_SCORE_THRESHOLD,
    N_RESULTS,
    VERSION_FAMILIES,
)


# ── Expansão geográfica ───────────────────────────────────────────────────────
# O corpus usa regiões ("Norte", "Sudeste") mas queries naturais usam cidades.
# Este mapa expande a query ANTES do embedding para melhorar o recall.

_CITY_TO_REGION: dict[str, str] = {
    # Norte
    "manaus": "Norte", "belém": "Norte", "belem": "Norte",
    "porto velho": "Norte", "macapá": "Norte", "macapa": "Norte",
    "boa vista": "Norte", "palmas": "Norte", "rio branco": "Norte",
    # Nordeste
    "salvador": "Nordeste", "fortaleza": "Nordeste", "recife": "Nordeste",
    "natal": "Nordeste", "joão pessoa": "Nordeste", "joao pessoa": "Nordeste",
    "maceió": "Nordeste", "maceio": "Nordeste", "teresina": "Nordeste",
    "são luís": "Nordeste", "sao luis": "Nordeste", "aracaju": "Nordeste",
    # Centro-Oeste
    "brasília": "Centro-Oeste", "brasilia": "Centro-Oeste",
    "goiânia": "Centro-Oeste", "goiania": "Centro-Oeste",
    "campo grande": "Centro-Oeste", "cuiabá": "Centro-Oeste", "cuiaba": "Centro-Oeste",
    # Sudeste
    "são paulo": "Sudeste", "sao paulo": "Sudeste",
    "rio de janeiro": "Sudeste", "belo horizonte": "Sudeste",
    "vitória": "Sudeste", "vitoria": "Sudeste",
    # Sul
    "curitiba": "Sul", "porto alegre": "Sul",
    "florianópolis": "Sul", "florianopolis": "Sul",
}


def _expand_geographic_terms(query: str) -> str:
    """
    Injeta regiões geográficas na query quando cidades brasileiras são detectadas.

    Exemplo: "Frete para Manaus?" → "Frete para Manaus? (Norte)"
    A expansão melhora o recall para queries geográficas sem alterar a semântica.
    """
    query_lower = query.lower()
    expansions: list[str] = []
    for city, region in _CITY_TO_REGION.items():
        if city in query_lower and region.lower() not in query_lower:
            if region not in expansions:
                expansions.append(region)
    if expansions:
        return f"{query} ({', '.join(expansions)})"
    return query


# ── M4: Expansão de termos de domínio ────────────────────────────────────────

def _expand_domain_terms(query: str) -> str:
    """
    Injeta termos complementares na query quando vocábulos especializados são
    detectados, cobrindo gaps de vocabulário entre queries naturais e corpus.

    Exemplos:
      "Carga perigosa com frete expresso?" →
        "... [urgente prioritário modalidade expressa autorização compliance]"
      "Qual o SLA do cliente Gold?" →
        "... [tempo resposta resolução prazo atendimento chamado]"
    """
    query_lower = query.lower()
    injections: list[str] = []
    for term, expansion in DOMAIN_TERM_EXPANSIONS.items():
        if term in query_lower:
            injections.append(expansion)
    if injections:
        return f"{query} [{' '.join(injections)}]"
    return query


def _expand_query(query: str) -> str:
    """Aplica todas as expansões de query (geográfica + domínio) em sequência."""
    q = _expand_geographic_terms(query)
    q = _expand_domain_terms(q)
    return q


# ── M8: Decomposição de queries compostas ────────────────────────────────────

# Padrões que indicam uma query multi-tópico
_COMPOUND_SEPARATORS = re.compile(
    r",\s*|\s+e\s+|\s+;\s*",
    re.IGNORECASE,
)
# Palavras-chave de tópicos NovaTech — presença em 2+ segmentos indica composição
_TOPIC_KEYWORDS = re.compile(
    r"\b(devoluc\w+|prazo|SLA|frete|carga\s+perigosa|perigosa|multiplicador|"
    r"reembolso|cancelamento|rastreamento)\b",
    re.IGNORECASE,
)


def _decompose_query(query: str) -> list[str]:
    """
    Detecta queries com múltiplos tópicos e as divide em sub-queries.

    Critério: a query é considerada composta se contém pelo menos dois
    segmentos (separados por vírgula, " e " ou ";") em que cada segmento
    cobre um tópico NovaTech distinto.

    Retorna lista com sub-queries individuais (ou [query] para queries simples).
    """
    parts = _COMPOUND_SEPARATORS.split(query)
    parts = [p.strip() for p in parts if len(p.strip()) > 8]
    if len(parts) < 2:
        return [query]
    # Verifica se cada segmento tem pelo menos uma palavra-chave de tópico
    topic_parts = [p for p in parts if _TOPIC_KEYWORDS.search(p)]
    if len(topic_parts) >= 2:
        return topic_parts
    return [query]


# ── Tipos ────────────────────────────────────────────────────────────────────

class RetrievedChunk(NamedTuple):
    text: str
    source: str
    section: str
    subsection: str
    doc_version: str
    doc_title: str
    similarity: float   # 1 = idêntico, 0 = ortogonal (convertido de distância coseno)


# ── M6: Deduplicação de versões de documentos ─────────────────────────────────

def _deduplicate_by_version(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """
    Remove chunks redundantes de versões mais antigas quando a versão preferida
    do mesmo documento contém o chunk equivalente da mesma seção.

    Motivação: PROC-042 v1 e v2 possuem seções idênticas (ex.: "2. Fórmula de
    cálculo", "4. Condições especiais"). Quando ambas aparecem nos resultados,
    os slots de v1 consomem espaço que poderia ser ocupado por chunks de
    documentos totalmente distintos — aumentando ruído e reduzindo diversidade.

    Se DEDUPLICATE_VERSIONS=False em config.py, retorna a lista original.
    """
    if not DEDUPLICATE_VERSIONS:
        return chunks

    result: list[RetrievedChunk] = []
    # Rastreia (família, seção, subseção) → arquivo preferido já adicionado
    seen: dict[str, str] = {}  # chave → source do chunk na lista resultado

    for chunk in chunks:
        info = VERSION_FAMILIES.get(chunk.source)
        if info is None:
            # Documento sem família de versões — não deduplica
            result.append(chunk)
            continue

        family, preferred = info
        key = f"{family}::{chunk.section}::{chunk.subsection}"

        if key not in seen:
            seen[key] = chunk.source
            result.append(chunk)
        else:
            existing_source = seen[key]
            if existing_source != preferred and chunk.source == preferred:
                # Substitui a versão antiga pela preferida
                result = [c for c in result if not (
                    VERSION_FAMILIES.get(c.source, (None,))[0] == family
                    and c.section == chunk.section
                    and c.subsection == chunk.subsection
                )]
                result.append(chunk)
                seen[key] = chunk.source
            # Se a versão existente já é a preferida (ou o mesmo arquivo), ignora

    return result


# ── M7: Filtragem por limiar mínimo de score ──────────────────────────────────

def _filter_by_score(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """
    Remove chunks com score abaixo de MIN_SCORE_THRESHOLD.

    Chunks de baixo score são invariavelmente ruído (confirmado na análise v2:
    nenhum chunk obrigatório apareceu abaixo de 0.30 nas queries de referência).
    """
    return [c for c in chunks if c.similarity >= MIN_SCORE_THRESHOLD]


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, n_results: int = N_RESULTS) -> list[RetrievedChunk]:
    """
    Retorna os N chunks mais similares à query, ordenados por similaridade.

    Pipeline v3:
      query → decomposição (M8) → sub-queries
      → para cada sub-query: expansão (M4) → embedding → ChromaDB
      → merge + deduplicação por versão (M6) + filtragem por score (M7)
      → retorna top-N re-ranqueados
    """
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise RuntimeError(
            f"Dependência não instalada: {e}\n"
            "Execute: pip install chromadb sentence-transformers"
        ) from e

    if not CHROMA_DIR.exists():
        raise RuntimeError(
            f"ChromaDB não encontrado em {CHROMA_DIR}.\n"
            "Execute primeiro: python ingest.py"
        )

    model = SentenceTransformer(EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    # M8: decompõe a query em sub-queries para queries compostas
    sub_queries = _decompose_query(query)

    # Para cada sub-query, recupera chunks individualmente
    all_chunks: list[RetrievedChunk] = []
    seen_ids: set[str] = set()  # evita duplicatas ao mesclar sub-queries

    for sub_q in sub_queries:
        expanded = _expand_query(sub_q)
        embedding = model.encode(expanded).tolist()

        # Solicita mais chunks por sub-query para compensar deduplicação posterior
        fetch_n = min(n_results, collection.count())
        results = collection.query(
            query_embeddings=[embedding],
            n_results=fetch_n,
            include=["documents", "metadatas", "distances"],
        )

        for doc, meta, dist in zip(
            results["documents"][0],    # type: ignore[index]
            results["metadatas"][0],    # type: ignore[index]
            results["distances"][0],    # type: ignore[index]
        ):
            chunk_key = f"{meta.get('source','')}::{meta.get('section','')}::{meta.get('subsection','')}::{doc[:60]}"
            if chunk_key in seen_ids:
                continue
            seen_ids.add(chunk_key)

            similarity = round(1.0 - dist, 4)
            all_chunks.append(RetrievedChunk(
                text=doc,
                source=str(meta.get("source", "")),
                section=str(meta.get("section", "")),
                subsection=str(meta.get("subsection", "")),
                doc_version=str(meta.get("version", "")),
                doc_title=str(meta.get("doc_title", "")),
                similarity=similarity,
            ))

    # M7: filtra por score mínimo
    all_chunks = _filter_by_score(all_chunks)

    # M6: remove versões duplicadas (mantém a versão preferida por seção)
    all_chunks = _deduplicate_by_version(all_chunks)

    # Re-ordena por similaridade e retorna os top-N
    all_chunks.sort(key=lambda c: c.similarity, reverse=True)
    return all_chunks[:n_results]


# ── Montagem de prompt ────────────────────────────────────────────────────────

SYSTEM_INSTRUCTIONS = """\
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder \
perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos \
trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa \
informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente \
e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier \
(ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser \
feita na documentação normativa (POL, PROC, SLA).\
"""


def assemble_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    """
    Monta o prompt completo pronto para colar no Claude (ou outro LLM).

    Estrutura:
      [SISTEMA] instruções do assistente
      [CONTEXTO] chunks recuperados, numerados, com fonte e similaridade
      [PERGUNTA] query original do atendente
    """
    lines: list[str] = []

    # ── Bloco SISTEMA ────────────────────────────────────────────────────────
    lines.append("=" * 70)
    lines.append("SISTEMA (instruções do assistente)")
    lines.append("=" * 70)
    lines.append(SYSTEM_INSTRUCTIONS)
    lines.append("")

    # ── Bloco CONTEXTO ───────────────────────────────────────────────────────
    lines.append("=" * 70)
    lines.append(f"CONTEXTO ({len(chunks)} trechos recuperados por similaridade semântica)")
    lines.append("=" * 70)

    for i, chunk in enumerate(chunks, start=1):
        source_label = chunk.source
        if chunk.doc_version:
            source_label += f" (versão {chunk.doc_version})"
        section_label = chunk.section
        if chunk.subsection:
            section_label += f" > {chunk.subsection}"

        lines.append(f"\n--- Trecho {i} | Fonte: {source_label} | Seção: {section_label} | Score: {chunk.similarity:.3f} ---")
        lines.append(chunk.text)

    lines.append("")

    # ── Bloco PERGUNTA ───────────────────────────────────────────────────────
    lines.append("=" * 70)
    lines.append("PERGUNTA DO ATENDENTE")
    lines.append("=" * 70)
    lines.append(query)
    lines.append("")
    lines.append("─" * 70)
    lines.append("↑ Copie TUDO acima e cole no Claude para obter a resposta.")

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_retrieval_results(query: str, chunks: list[RetrievedChunk]) -> None:
    print(f"\nQuery: {query!r}")
    print(f"Chunks recuperados: {len(chunks)}\n")
    for i, c in enumerate(chunks, 1):
        source_label = c.source
        if c.doc_version:
            source_label += f" v{c.doc_version}"
        section = f"{c.section}" + (f" > {c.subsection}" if c.subsection else "")
        print(f"  [{i}] Score={c.similarity:.3f} | {source_label} | {section}")
        # Mostra as primeiras 120 chars do chunk como preview
        preview = c.text.replace("\n", " ")[:120]
        print(f"       {preview}...")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recupera chunks relevantes e monta prompt para o Claude.")
    parser.add_argument("query", help="Pergunta do atendente em linguagem natural.")
    parser.add_argument(
        "--top", type=int, default=N_RESULTS, metavar="N",
        help=f"Número de chunks a recuperar (padrão: {N_RESULTS}).")
    parser.add_argument(
        "--prompt-only", action="store_true",
        help="Imprime apenas o prompt montado (sem o relatório de retrieval).")
    args = parser.parse_args()

    chunks = retrieve(args.query, n_results=args.top)

    if not args.prompt_only:
        _print_retrieval_results(args.query, chunks)
        print("\n" + "─" * 70)
        print("PROMPT MONTADO (pronto para colar no Claude):")
        print("─" * 70 + "\n")

    print(assemble_prompt(args.query, chunks))
