"""
Configurações centralizadas do pipeline RAG NovaTech.
Edite aqui para ajustar comportamento sem modificar os scripts principais.
"""
from pathlib import Path

# ── Modelo de embeddings ─────────────────────────────────────────────────────
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
# Modelo multilíngue treinado em 50+ idiomas via knowledge distillation.
# 384 dimensões (mesmas do all-MiniLM-L6-v2 — ChromaDB compatível sem re-schema).
# Melhoria sobre all-MiniLM-L6-v2: MTEB PT ~65 vs ~52; distingue melhor compostos
# nominais em português ("prazo de devolução", "carga perigosa + devolução").
# Tamanho: ~470 MB (download único). Re-ingestão obrigatória ao trocar de modelo.

# ── ChromaDB ─────────────────────────────────────────────────────────────────
COLLECTION_NAME = "novatech_docs"

# ── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE = 800
# Tamanho máximo em caracteres por chunk antes de acionar divisão por janela
# deslizante. 800 chars ≈ 150 palavras ≈ bem abaixo do limite de 256 tokens
# do all-MiniLM-L6-v2, garantindo que nenhum chunk seja truncado pelo encoder.

CHUNK_OVERLAP = 150
# Sobreposição em caracteres entre chunks produzidos pela janela deslizante.
# Evita perda de contexto em fronteiras artificiais.

MIN_CHUNK_CHARS = 60
# Chunks menores que isso são descartados (ex.: cabeçalhos sem conteúdo).

# ── Retrieval ────────────────────────────────────────────────────────────────
N_RESULTS = 8
# Número de chunks recuperados por query. Aumentado de 5 para 8 após validação
# com Anexo B: chunks obrigatórios frequentemente apareciam nas posições 6–8.
# N=8 adiciona ~1.600 tokens extras de contexto — aceitável para modelos 100k+.

MIN_SCORE_THRESHOLD = 0.30
# Chunks com similaridade abaixo deste valor são descartados como ruído.
# Valor calibrado na v2: scores < 0.30 eram invariavelmente irrelevantes nas
# análises de Q1–Q10. Ajuda a liberar slots para chunks mais relevantes em
# queries com N_RESULTS fixo.

DEDUPLICATE_VERSIONS = True
# Quando True, remove chunks de versões mais antigas de um documento quando
# a versão mais nova do mesmo documento retorna o chunk equivalente da mesma
# seção. Reduz ruído de PROC-042 v1 duplicando resultados de PROC-042 v2.

# Famílias de versões: mapeamento (nome_arquivo → (família, preferência))
# "preferência" = arquivo mais recente a manter em caso de deduplicação.
VERSION_FAMILIES: dict[str, tuple[str, str]] = {
    "PROC-042-frete-especial-v1.md": (
        "PROC-042",
        "PROC-042-v2-frete-especial-revisado.md",
    ),
    "PROC-042-v2-frete-especial-revisado.md": (
        "PROC-042",
        "PROC-042-v2-frete-especial-revisado.md",
    ),
}

# ── Expansão de termos de domínio ─────────────────────────────────────────────
# Pares (termo_detectado_na_query → termos_adicionais_injetados).
# Complementa a expansão geográfica para cobrir vocabulário especializado que
# não aparece literalmente nos documentos do corpus.
DOMAIN_TERM_EXPANSIONS: dict[str, str] = {
    "expresso":  "urgente prioritário modalidade expressa autorização compliance ANTT frete expresso",
    "express":   "urgente prioritário modalidade expressa autorização compliance",
    "urgente":   "expresso prioritário modalidade urgência",
    "sla":       "tempo resposta resolução prazo atendimento chamado",
    "prazo":     "dias úteis tempo limite vencimento",
    "tier":      "classificação cliente gold silver standard",
    "nivel":     "classificação cliente gold silver standard tier",
}

# ── Caminhos (resolvidos relativamente ao projeto) ───────────────────────────
# Estrutura esperada:
#   dgs-ai-first/
#     Contexto/          ← documentos do corpus
#     Exercicio-1.3/
#       rag_pipeline/    ← este pacote
#         chroma_db/     ← criado automaticamente pelo ChromaDB

_PIPELINE_DIR = Path(__file__).parent          # .../Exercicio-1.3/rag_pipeline/
_EXERCISE_DIR = _PIPELINE_DIR.parent           # .../Exercicio-1.3/
PROJECT_ROOT   = _EXERCISE_DIR.parent          # .../dgs-ai-first/

DOCS_DIR   = PROJECT_ROOT / "Contexto"
CHROMA_DIR = _PIPELINE_DIR / "chroma_db"

# Arquivos do Contexto/ que NÃO fazem parte do corpus de conhecimento NovaTech
# (são meta-documentos do exercício — incluí-los polui o retrieval)
EXCLUDED_FILES = {
    "exercicio-fase-1-entendimento.md",
    "anexo-a-documentacao-simulada-novatech.md",
    "anexo-b-chunks-referencia-rag.md",
}
