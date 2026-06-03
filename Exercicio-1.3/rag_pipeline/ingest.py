"""
ingest.py — Ingere documentos markdown da NovaTech no ChromaDB.

Estratégia de chunking: divisão por cabeçalhos markdown
─────────────────────────────────────────────────────────
1. Cada arquivo .md é dividido primeiramente em seções (## headers).
2. Seções que contêm sub-seções (### headers) são divididas novamente:
   o conteúdo ANTES do primeiro ### vira um chunk próprio (quando suficiente),
   e cada ### vira um chunk independente.
3. Seções sem ### ficam como um único chunk. Se o texto exceder CHUNK_SIZE
   caracteres, uma janela deslizante com sobreposição CHUNK_OVERLAP é aplicada.

Por que esta estratégia?
  - Os chunks de referência do Anexo B correspondem exatamente a sub-seções
    do documento (ex.: POL-001-A = seção 3.1, PROC-042v2-B = seção 2.1).
  - Manter seções completas preserva coerência semântica: tabelas de
    multiplicadores regionais ficam inteiras em um chunk.
  - O modelo all-MiniLM-L6-v2 tem limite de 256 tokens — CHUNK_SIZE=800 chars
    ≈ 150 palavras ≈ ~200 tokens, ficando bem abaixo do limite.

Uso:
    python ingest.py            # ingere tudo
    python ingest.py --reset    # limpa a coleção antes de reingerir
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import Generator

# Garante que o pacote pode ser executado como script ou importado
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DOCS_DIR,
    EMBEDDING_MODEL,
    EXCLUDED_FILES,
    MIN_CHUNK_CHARS,
)


# ── Tipos auxiliares ─────────────────────────────────────────────────────────

class Chunk:
    """Representa um fragmento de texto pronto para indexação."""

    def __init__(self, text: str, source: str, section: str, subsection: str,
                 doc_version: str, doc_title: str) -> None:
        self.text = text.strip()
        self.source = source          # nome do arquivo (sem caminho)
        self.section = section        # cabeçalho ## pai
        self.subsection = subsection  # cabeçalho ### (vazio se não houver)
        self.doc_version = doc_version
        self.doc_title = doc_title

    def chunk_id(self) -> str:
        """ID estável baseado em hash do conteúdo (reproduzível entre runs)."""
        key = f"{self.source}::{self.section}::{self.subsection}::{self.text[:80]}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def metadata(self) -> dict:
        return {
            "source":     self.source,
            "section":    self.section,
            "subsection": self.subsection,
            "version":    self.doc_version,
            "doc_title":  self.doc_title,
        }


# ── Parsing de markdown ──────────────────────────────────────────────────────

def _extract_doc_metadata(raw: str) -> dict:
    """Extrai metadados do bloco de cabeçalho do documento (Version, etc.)."""
    meta = {"version": "", "title": ""}
    lines = raw.splitlines()

    # Título: primeira linha com # (nível 1)
    for line in lines[:5]:
        if line.startswith("# "):
            meta["title"] = line.lstrip("# ").strip()
            break

    # Versão: linha no formato **Versão:** X.X
    for line in lines[:15]:
        m = re.search(r"\*\*Versão:\*\*\s*(.+)", line)
        if m:
            meta["version"] = m.group(1).strip()
            break

    return meta


# ── M5: Conversão de tabelas markdown para prosa indexável ───────────────────

_TABLE_HEADER_RE = re.compile(r"^\|(.+)\|$")
_TABLE_SEPARATOR_RE = re.compile(r"^\|[\s\-|:]+\|$")


def _table_to_prose_prefix(text: str) -> str:
    """
    Gera um prefixo em prosa para blocos de texto que contêm tabelas markdown.

    Tabelas têm baixa densidade semântica quando codificadas diretamente por
    modelos de embedding: os separadores "|" quebram o contexto entre
    cabeçalho e valor, prejudicando a recuperação de chunks tabulares como
    a "Tabela de SLAs" (SLA-2024, seção 2).

    Estratégia: para cada linha de dados da tabela, gera uma sentença no
    formato "Header1: Valor1; Header2: Valor2." que o modelo consegue associar
    semanticamente a queries como "Qual o SLA do Gold?".

    O texto original da tabela é preservado integralmente após o prefixo.
    """
    lines = text.splitlines()
    prose_lines: list[str] = []
    i = 0
    has_tables = False

    while i < len(lines):
        stripped = lines[i].strip()

        # Detecta início de tabela: linha de cabeçalho seguida de separador
        if (
            _TABLE_HEADER_RE.match(stripped)
            and i + 1 < len(lines)
            and _TABLE_SEPARATOR_RE.match(lines[i + 1].strip())
        ):
            has_tables = True
            headers = [h.strip() for h in stripped.strip("|").split("|")]
            i += 2  # pula cabeçalho e separador

            while i < len(lines) and _TABLE_HEADER_RE.match(lines[i].strip()):
                cells = [c.strip() for c in lines[i].strip("|").split("|")]
                pairs = []
                for j, cell in enumerate(cells):
                    if j < len(headers) and cell and cell not in ("", "---"):
                        pairs.append(f"{headers[j]}: {cell}")
                if pairs:
                    prose_lines.append("; ".join(pairs) + ".")
                i += 1
        else:
            i += 1

    if has_tables and prose_lines:
        return "[Resumo da tabela] " + " ".join(prose_lines) + "\n\n" + text

    return text


def _sliding_window(text: str, section_label: str, subsection_label: str,
                    source: str, doc_meta: dict) -> Generator[Chunk, None, None]:
    """Divide texto longo em janelas sobrepostas quando excede CHUNK_SIZE."""
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        piece = text[start:end]
        if len(piece.strip()) >= MIN_CHUNK_CHARS:
            yield Chunk(
                text=piece,
                source=source,
                section=section_label,
                subsection=subsection_label,
                doc_version=doc_meta["version"],
                doc_title=doc_meta["title"],
            )
        start += CHUNK_SIZE - CHUNK_OVERLAP
        if start >= len(text):
            break


def _make_chunk(text: str, section_label: str, subsection_label: str,
                source: str, doc_meta: dict) -> Generator[Chunk, None, None]:
    """Cria um ou mais chunks a partir de um bloco de texto."""
    text = text.strip()
    if len(text) < MIN_CHUNK_CHARS:
        return
    # M5: converte tabelas para prosa indexável antes de embutir
    text = _table_to_prose_prefix(text)
    # M9: injeta o enunciado da pergunta FAQ no início do chunk.
    # Motivação: itens de FAQ têm o enunciado da pergunta apenas no
    # label de sub-seção (metadata), não no corpo da resposta. Sem a
    # pergunta no texto embeddado, queries como "Carga perigosa com
    # frete expresso?" não encontram o chunk porque o texto começa
    # direto com a resposta.
    # Restrição: aplica-se APENAS a padrões "Item N — ...", para não
    # contaminar chunks de documentos normativos com prefixos indevidos.
    if subsection_label:
        m = re.search(r'Item\s+\d+\s*[—–-]\s*"?(.+?)"?\s*$', subsection_label)
        if m:
            question = m.group(1).strip().rstrip('"')
            text = f"Pergunta: {question}\n{text}"
    if len(text) <= CHUNK_SIZE:
        yield Chunk(
            text=text,
            source=source,
            section=section_label,
            subsection=subsection_label,
            doc_version=doc_meta["version"],
            doc_title=doc_meta["title"],
        )
    else:
        yield from _sliding_window(text, section_label, subsection_label, source, doc_meta)


def parse_chunks(filepath: Path) -> list[Chunk]:
    """
    Converte um arquivo .md em lista de Chunks usando divisão por cabeçalhos.

    Fluxo:
      raw text → split ## → para cada seção → split ### → chunks
    """
    raw = filepath.read_text(encoding="utf-8")
    doc_meta = _extract_doc_metadata(raw)
    source = filepath.name
    chunks: list[Chunk] = []

    # Remove conteúdo antes do primeiro ## (cabeçalho do documento)
    # Esse conteúdo é metadado, não conhecimento para retrieval
    body_start = re.search(r"\n## ", raw)
    if body_start is None:
        # Documento sem seções ##: trata o documento inteiro como um chunk
        chunks.extend(_make_chunk(raw, "documento", "", source, doc_meta))
        return chunks

    # Divide em seções pelo ## header
    # re.split com grupo captura mantém o delimitador no resultado
    raw_sections = re.split(r"\n(## [^\n]+)", raw[body_start.start():])

    # raw_sections alterna: [prefix?, header1, body1, header2, body2, ...]
    # O primeiro elemento pode ser vazio ou lixo antes do primeiro ##
    it = iter(raw_sections)
    next(it)  # descarta o prefixo antes do primeiro ##

    for header_line, body in zip(it, it):
        section_label = header_line.lstrip("# ").strip()

        # Verifica se há sub-seções ### dentro desta seção
        subsection_splits = re.split(r"\n(### [^\n]+)", body)

        if len(subsection_splits) == 1:
            # Seção sem sub-seções
            chunks.extend(_make_chunk(body, section_label, "", source, doc_meta))
        else:
            # Há sub-seções; o primeiro elemento é o conteúdo antes do 1º ###
            prefix_content = subsection_splits[0].strip()
            if len(prefix_content) >= MIN_CHUNK_CHARS:
                chunks.extend(_make_chunk(
                    prefix_content, section_label, "", source, doc_meta))

            # Itera sobre pares (### header, conteúdo)
            sub_it = iter(subsection_splits[1:])
            for sub_header, sub_body in zip(sub_it, sub_it):
                subsection_label = sub_header.lstrip("# ").strip()
                chunks.extend(_make_chunk(
                    sub_body, section_label, subsection_label, source, doc_meta))

    return chunks


# ── Ingestão no ChromaDB ─────────────────────────────────────────────────────

def ingest(reset: bool = False) -> None:
    """Processa todos os documentos do corpus e armazena embeddings no ChromaDB."""
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"[ERRO] Dependência não instalada: {e}")
        print("Execute: pip install chromadb sentence-transformers")
        sys.exit(1)

    # ── Verifica documentos disponíveis ─────────────────────────────────────
    doc_files = [
        f for f in sorted(DOCS_DIR.glob("*.md"))
        if f.name not in EXCLUDED_FILES
    ]
    if not doc_files:
        print(f"[ERRO] Nenhum arquivo .md encontrado em: {DOCS_DIR}")
        sys.exit(1)

    print(f"Documentos encontrados ({len(doc_files)}):")
    for f in doc_files:
        print(f"  • {f.name}")

    # ── Chunking ─────────────────────────────────────────────────────────────
    print("\n[1/3] Gerando chunks...")
    all_chunks: list[Chunk] = []
    for doc_file in doc_files:
        doc_chunks = parse_chunks(doc_file)
        print(f"  {doc_file.name}: {len(doc_chunks)} chunks")
        all_chunks.extend(doc_chunks)

    print(f"  Total: {len(all_chunks)} chunks")

    # ── Embeddings ───────────────────────────────────────────────────────────
    print(f"\n[2/3] Gerando embeddings (modelo: {EMBEDDING_MODEL})...")
    print("  (Primeira execução faz download do modelo ~22MB — aguarde)")
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [c.text for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = embeddings.tolist()  # numpy array → list (compatível com ChromaDB)
    print(f"  Embeddings gerados: {len(embeddings)} vetores de {len(embeddings[0])} dimensões")

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    print(f"\n[3/3] Armazenando no ChromaDB em: {CHROMA_DIR}")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  Coleção '{COLLECTION_NAME}' removida (--reset solicitado)")
        except Exception:
            pass  # coleção ainda não existia — normal na primeira execução

    # get_or_create garante idempotência: re-ingerir não duplica
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        # ChromaDB usa distância de cosseno por padrão com embeddings normalizados
        metadata={"hnsw:space": "cosine"},
    )

    # Upsert em lotes para evitar problemas com coleções grandes
    BATCH_SIZE = 100
    ids        = [c.chunk_id() for c in all_chunks]
    metadatas  = [c.metadata()  for c in all_chunks]

    for i in range(0, len(all_chunks), BATCH_SIZE):
        collection.upsert(
            ids=ids[i : i + BATCH_SIZE],
            documents=texts[i : i + BATCH_SIZE],
            embeddings=embeddings[i : i + BATCH_SIZE],
            metadatas=metadatas[i : i + BATCH_SIZE],
        )

    print(f"\n✓ Ingestão concluída: {collection.count()} chunks no ChromaDB")
    print("  Execute 'python retrieve.py \"<sua pergunta>\"' para testar.")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingere documentos NovaTech no ChromaDB.")
    parser.add_argument(
        "--reset", action="store_true",
        help="Remove a coleção existente antes de re-ingerir (útil após mudanças de config).")
    args = parser.parse_args()
    ingest(reset=args.reset)
