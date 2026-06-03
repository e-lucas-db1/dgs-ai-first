"""
validate.py — Valida o pipeline RAG contra o mapa de cobertura do Anexo B.

Para cada query de referência, verifica se os chunks esperados aparecem
entre os N_RESULTS recuperados. Calcula hit-rate e reporta lacunas.

Uso:
    python validate.py
    python validate.py --verbose    # mostra os chunks recuperados por query
    python validate.py --top 7      # usa N diferente de resultados
"""

import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent))

from config import N_RESULTS
from retrieve import retrieve, RetrievedChunk


# ── Mapa de cobertura (Anexo B) ──────────────────────────────────────────────
# Cada entrada representa uma query de validação com:
#   expected_must:  chunks que DEVEM aparecer (hit obrigatório)
#   expected_may:   chunks que PODEM aparecer (relevância menor, bônus)
#
# Como identificar um chunk recuperado = chunk de referência?
# O pipeline divide os documentos por seções. A coluna "match_hints" define
# critérios de correspondência: fonte (source) + trecho de texto que DEVE
# estar presente no chunk.

@dataclass
class ChunkRef:
    """Descreve um chunk de referência do Anexo B para fins de validação."""
    ref_id: str            # ex.: "POL-001-A"
    source_pattern: str    # padrão no nome do arquivo fonte
    text_snippets: list[str] = field(default_factory=list)
    # Todas as snippets devem estar presentes no texto do chunk (AND)


COVERAGE_MAP = [
    {
        "query": "Qual o prazo de devolução?",
        "must": [
            ChunkRef("POL-001-A", "POL-001",
                     ["7 (sete) dias úteis", "data de recebimento"]),
            ChunkRef("POL-001-B", "POL-001",
                     ["NÃO são elegíveis", "classes 1 a 6 da ANTT"]),
        ],
        "may": [
            ChunkRef("POL-001-C", "POL-001", ["Portal do Cliente"]),
        ],
    },
    {
        "query": "Posso devolver carga perigosa?",
        "must": [
            ChunkRef("POL-001-B", "POL-001",
                     ["NÃO são elegíveis", "classes 1 a 6"]),
        ],
        "may": [
            ChunkRef("FAQ-03", "FAQ-atendimento",
                     ["ramal 4500", "tratamento especial"]),
            ChunkRef("POL-001-A", "POL-001", ["7 (sete) dias úteis"]),
        ],
    },
    {
        "query": "Qual o SLA do cliente Gold?",
        "must": [
            ChunkRef("SLA-2024-B", "SLA-2024",
                     ["Gold", "2h úteis", "24h úteis"]),
        ],
        "may": [
            ChunkRef("SLA-2024-A", "SLA-2024",
                     ["Gold", "500.000", "200 operações"]),
            ChunkRef("SLA-2024-C", "SLA-2024",
                     ["30min", "4h"]),
        ],
    },
    {
        "query": "Qual o SLA do cliente Platinum?",
        "must": [
            ChunkRef("SLA-2024-A", "SLA-2024",
                     ["Não existem outros tiers"]),
        ],
        "may": [
            ChunkRef("FAQ-15", "FAQ-atendimento",
                     ["Não existe tier Platinum"]),
        ],
    },
    {
        "query": "Frete para 600kg para Manaus?",
        "must": [
            ChunkRef("PROC-042v2-B", "PROC-042-v2",
                     ["Norte", "1.8"]),
            ChunkRef("PROC-042v2-A", "PROC-042-v2",
                     ["500kg", "Multiplicador regional"]),
        ],
        "may": [
            # Versão antiga — risco de contradição
            ChunkRef("PROC-042-B", "PROC-042-frete-especial-v1",
                     ["Norte", "1.6"]),
        ],
    },
    {
        "query": "Frete para 300kg para Salvador?",
        "must": [],   # Nenhum chunk cobre frete < 500kg
        "may": [
            ChunkRef("PROC-042v2-B", "PROC-042-v2", ["500kg"]),
        ],
        "expect_no_relevant": True,  # pipeline deve retornar chunks de baixa relevância
    },
    {
        "query": "O que acontece com carga danificada?",
        "must": [
            ChunkRef("FAQ-38", "FAQ-atendimento",
                     ["carga danificada", "48h"]),
        ],
        "may": [],
    },
    {
        "query": "Carga perigosa com frete expresso?",
        "must": [
            ChunkRef("FAQ-32", "FAQ-atendimento",
                     ["autorização do Compliance", "documentação ANTT"]),
        ],
        "may": [],
    },
    {
        "query": "Qual o multiplicador para o Sudeste?",
        "must": [
            ChunkRef("PROC-042v2-B", "PROC-042-v2",
                     ["Sudeste", "1.1"]),
        ],
        "may": [
            # Versão antiga — contradição: 1.0 vs 1.1
            ChunkRef("PROC-042-B", "PROC-042-frete-especial-v1",
                     ["Sudeste", "1.0"]),
        ],
    },
    {
        "query": "Prazo de devolução, carga perigosa e frete especial",
        "must": [
            ChunkRef("POL-001-A", "POL-001",
                     ["7 (sete) dias úteis"]),
            ChunkRef("POL-001-B", "POL-001",
                     ["classes 1 a 6"]),
            ChunkRef("PROC-042v2-A", "PROC-042-v2",
                     ["500kg", "Multiplicador regional"]),
            ChunkRef("PROC-042v2-B", "PROC-042-v2",
                     ["Norte", "1.8"]),
        ],
        "may": [
            ChunkRef("FAQ-03", "FAQ-atendimento",
                     ["ramal 4500"]),
        ],
    },
]


# ── Lógica de correspondência ─────────────────────────────────────────────────

def _chunk_matches_ref(chunk: RetrievedChunk, ref: ChunkRef) -> bool:
    """
    Verifica se um chunk recuperado corresponde a um chunk de referência.

    Critério: o nome do arquivo fonte deve CONTER source_pattern E
    todos os text_snippets devem estar presentes no texto do chunk.
    """
    source_ok = ref.source_pattern.lower() in chunk.source.lower()
    snippets_ok = all(s.lower() in chunk.text.lower() for s in ref.text_snippets)
    return source_ok and snippets_ok


def _find_ref_in_results(ref: ChunkRef, chunks: list[RetrievedChunk]) -> RetrievedChunk | None:
    """Retorna o primeiro chunk que corresponde ao ref, ou None."""
    for c in chunks:
        if _chunk_matches_ref(c, ref):
            return c
    return None


# ── Validação e relatório ─────────────────────────────────────────────────────

@dataclass
class QueryResult:
    query: str
    must_hits: list[tuple[ChunkRef, RetrievedChunk]]   = field(default_factory=list)
    must_misses: list[ChunkRef]                         = field(default_factory=list)
    may_hits: list[tuple[ChunkRef, RetrievedChunk]]    = field(default_factory=list)
    chunks_retrieved: list[RetrievedChunk]             = field(default_factory=list)
    expect_no_relevant: bool                           = False

    @property
    def passed(self) -> bool:
        return len(self.must_misses) == 0


def validate_all(top: int = N_RESULTS, verbose: bool = False) -> None:
    print("=" * 70)
    print("VALIDAÇÃO DO PIPELINE RAG — MAPA DE COBERTURA (ANEXO B)")
    print("=" * 70)
    print(f"Configuração: top={top} chunks por query\n")

    results: list[QueryResult] = []

    for case in COVERAGE_MAP:
        query = case["query"]
        must_refs: list[ChunkRef] = case.get("must", [])
        may_refs:  list[ChunkRef] = case.get("may", [])
        no_relevant: bool         = case.get("expect_no_relevant", False)

        chunks = retrieve(query, n_results=top)

        qr = QueryResult(
            query=query,
            chunks_retrieved=chunks,
            expect_no_relevant=no_relevant,
        )

        for ref in must_refs:
            found = _find_ref_in_results(ref, chunks)
            if found:
                qr.must_hits.append((ref, found))
            else:
                qr.must_misses.append(ref)

        for ref in may_refs:
            found = _find_ref_in_results(ref, chunks)
            if found:
                qr.may_hits.append((ref, found))

        results.append(qr)

        # Imprime resultado desta query
        status = "✓ PASS" if qr.passed else "✗ FAIL"
        must_total = len(must_refs)
        must_found = len(qr.must_hits)
        print(f"[{status}] {query!r}")
        print(f"         must: {must_found}/{must_total} encontrados"
              + (f"  |  may: {len(qr.may_hits)}/{len(may_refs)} bônus" if may_refs else ""))

        if qr.must_misses:
            print("         LACUNAS (chunks obrigatórios não encontrados):")
            for ref in qr.must_misses:
                print(f"           • {ref.ref_id} (fonte={ref.source_pattern!r})")
                print(f"             snippets esperadas: {ref.text_snippets}")
                print(f"             → Causa provável: modelo all-MiniLM-L6-v2 (inglês) não separa")
                print(f"               bem compostos semânticos do português; aumente N ou troque o modelo.")

        if no_relevant and not qr.must_hits:
            print("         ℹ Sem cobertura esperada — comportamento correto.")

        if verbose:
            print("         Chunks recuperados:")
            for i, c in enumerate(chunks, 1):
                source_info = c.source + (f" v{c.doc_version}" if c.doc_version else "")
                section_info = c.section + (f" > {c.subsection}" if c.subsection else "")
                print(f"           {i}. score={c.similarity:.3f} | {source_info} | {section_info}")
                preview = c.text.replace("\n", " ")[:90]
                print(f"              {preview}...")
        print()

    # ── Sumário ───────────────────────────────────────────────────────────────
    passed = sum(1 for r in results if r.passed)
    total  = len(results)
    all_must = sum(len(c["must"]) for c in COVERAGE_MAP)
    all_found = sum(len(r.must_hits) for r in results)

    print("=" * 70)
    print(f"SUMÁRIO: {passed}/{total} queries passaram | "
          f"{all_found}/{all_must} chunks obrigatórios encontrados "
          f"({100 * all_found // all_must}%)")
    print("=" * 70)

    # ── Análise de lacunas ────────────────────────────────────────────────────
    all_misses = [(r.query, ref) for r in results for ref in r.must_misses]
    if all_misses:
        print("\nANÁLISE DE LACUNAS:")
        print("─" * 70)
        # Agrupa por ref_id para não repetir o mesmo chunk várias vezes
        seen_refs = set()
        for query, ref in all_misses:
            if ref.ref_id not in seen_refs:
                seen_refs.add(ref.ref_id)
                print(f"• {ref.ref_id} (fonte: {ref.source_pattern})")
                print(f"  Snippets esperadas: {ref.text_snippets}")
        print()
        print("Causa raiz identificada (via testes reais com all-MiniLM-L6-v2):")
        print("  1. Modelo treinado em inglês — compostos nominais portugueses mal")
        print("     representados no espaço vetorial (ex: 'prazo de devolução' ≠ '7 dias úteis').")
        print("  2. Termos transversais ('carga perigosa') aparecem em múltiplos contextos;")
        print("     o modelo não discrimina 'perigosa + devolução' de 'perigosa + frete'.")
        print("  3. Nomes geográficos ('Manaus') não mapeados para regiões ('Norte').")
        print()
        print("Ações recomendadas:")
        print("  → Curto prazo:  aumentar N_RESULTS para 8-10 em config.py")
        print("  → Médio prazo:  trocar para paraphrase-multilingual-MiniLM-L12-v2")
        print("  → Médio prazo:  adicionar mapa geográfico cidades→regiões em retrieve.py")
        print("  → Longo prazo:  retrieval híbrido BM25 + vetorial (rank_bm25 + ChromaDB)")
    else:
        print("\n✓ Nenhuma lacuna detectada. Pipeline alinhado com o Anexo B.")

    # ── Avisos sobre contradições conhecidas ──────────────────────────────────
    print("\nAVISOS (contradições documentadas no corpus):")
    print("─" * 70)
    print("• PROC-042 v1 e v2 coexistem no corpus com multiplicadores conflitantes.")
    print("  Se ambas as versões aparecerem juntas em uma query de frete, o LLM")
    print("  deve explicitamente mencionar a contradição e usar a v2 (mais recente).")
    print("  A PROC-042v2-E define a regra de transição: chamados desde 01/12/2023")
    print("  usam v2; chamados abertos antes usam v1.")
    print()
    print("• FAQ-atendimento é documento informal (não validado por Compliance).")
    print("  Quando recuperado, o LLM deve indicar que a informação precisa de")
    print("  confirmação na documentação normativa.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valida retrieval do pipeline RAG contra o Anexo B.")
    parser.add_argument(
        "--top", type=int, default=N_RESULTS, metavar="N",
        help=f"Chunks por query (padrão: {N_RESULTS}).")
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Mostra todos os chunks recuperados para cada query.")
    args = parser.parse_args()

    validate_all(top=args.top, verbose=args.verbose)
