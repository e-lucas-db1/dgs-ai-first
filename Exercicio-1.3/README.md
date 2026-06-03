# Pipeline RAG NovaTech — PoC Open-Source

Pipeline de Retrieval-Augmented Generation (RAG) para o corpus de documentação
simulada da NovaTech Logística. Totalmente local, sem custos de nuvem.

---

## Pré-requisitos

- Python 3.10 ou superior
- Conexão com a internet apenas na primeira execução (download do modelo ~22 MB)

## Instalação

```bash
pip install chromadb sentence-transformers
```

> **Nota:** `sentence-transformers` puxa o PyTorch como dependência (~500 MB na
> primeira instalação). Se o ambiente for restrito, use
> `pip install sentence-transformers --no-deps` e instale `torch` separadamente.

---

## Estrutura de arquivos

```
dgs-ai-first/
  Contexto/                          ← corpus de documentos NovaTech
    POL-001-politica-devolucao.md
    PROC-042-frete-especial-v1.md
    PROC-042-v2-frete-especial-revisado.md
    SLA-2024-tabela-sla-clientes.md
    FAQ-atendimento.md
    anexo-b-chunks-referencia-rag.md  ← gabarito (NÃO ingerido)

  Exercicio-1.3/
    README.md                         ← este arquivo
    rag_pipeline/
      config.py      ← configurações centralizadas (edite aqui)
      ingest.py      ← ingere documentos → ChromaDB
      retrieve.py    ← recupera chunks + monta prompt
      validate.py    ← valida contra o Anexo B
      chroma_db/     ← criado automaticamente na primeira ingestão
```

---

## Como executar

Todos os comandos são executados de dentro de `Exercicio-1.3/rag_pipeline/`.

### 1. Ingestão (executar uma vez)

```bash
cd Exercicio-1.3/rag_pipeline
python ingest.py
```

Saída esperada:
```
Documentos encontrados (5):
  • FAQ-atendimento.md
  • POL-001-politica-devolucao.md
  • PROC-042-frete-especial-v1.md
  • PROC-042-v2-frete-especial-revisado.md
  • SLA-2024-tabela-sla-clientes.md

[1/3] Gerando chunks...
  FAQ-atendimento.md: 9 chunks
  POL-001-politica-devolucao.md: 7 chunks
  ...
  Total: ~35 chunks

[2/3] Gerando embeddings (modelo: all-MiniLM-L6-v2)...
[3/3] Armazenando no ChromaDB...

✓ Ingestão concluída: 35 chunks no ChromaDB
```

Para reingerir do zero (ex.: após alterar `config.py`):
```bash
python ingest.py --reset
```

### 2. Retrieval e geração de prompt

```bash
python retrieve.py "Qual o prazo de devolução?"
```

O script imprime os chunks recuperados com seus scores de similaridade,
seguido do **prompt completo** pronto para colar no Claude.

Opções:
```bash
python retrieve.py "Frete para 600kg para Manaus?" --top 7   # usa 7 chunks
python retrieve.py "Qual o SLA Gold?" --prompt-only          # só o prompt
```

### 3. Validação contra o Anexo B

```bash
python validate.py
```

Saída esperada (pipeline bem calibrado):
```
[✓ PASS] 'Qual o prazo de devolução?'
         must: 2/2 encontrados  |  may: 1/1 bônus
[✓ PASS] 'Qual o SLA do cliente Gold?'
         must: 1/1 encontrados  |  may: 2/2 bônus
...
SUMÁRIO: 9/10 queries passaram | 17/18 chunks obrigatórios encontrados (94%)
```

Para ver os chunks recuperados por cada query:
```bash
python validate.py --verbose
```

---

## Workflow completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. python ingest.py      → processa .md, gera embeddings, salva no DB  │
│                                                                          │
│  2. python retrieve.py    → para cada pergunta do atendente:             │
│       "Qual o SLA Gold?"    ┌───────────────────────────────────┐        │
│                             │ query embedding                    │        │
│                             │       ↓                           │        │
│                             │ ChromaDB similarity search         │        │
│                             │       ↓                           │        │
│                             │ top-5 chunks + scores              │        │
│                             │       ↓                           │        │
│                             │ prompt montado (sistema+ctx+query) │        │
│                             └───────────────────────────────────┘        │
│                                        ↓                                 │
│  3. [manual] Cole o prompt no Claude → obtenha a resposta                │
│                                                                          │
│  4. python validate.py    → verifica cobertura vs. Anexo B               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Estratégia de chunking — justificativa

### Abordagem: divisão por cabeçalhos markdown (header-aware splitting)

O corpus NovaTech usa estrutura de documentos normativos onde **cada sub-seção
(### header) corresponde a uma unidade semântica coesa**. Por exemplo:

- `### 3.1. Prazo geral` contém exatamente a regra de 7 dias úteis
- `### 2.1. Multiplicadores regionais` contém a tabela de multiplicadores

Dividir por cabeçalhos garante que cada chunk corresponde a um "fato" completo,
sem cortar regras pela metade.

**Comparativo de estratégias consideradas:**

| Estratégia | Prós | Contras | Decisão |
|------------|------|---------|---------|
| **Header-aware** (escolhida) | Alinha com Anexo B; preserva tabelas inteiras; chunks semanticamente coerentes | Chunks de tamanho variável | ✓ Escolhida |
| Janela deslizante fixa | Simples de implementar | Corta tabelas; split artificial em bordas de parágrafos | ✗ Descartada como principal |
| Por parágrafo | Granularidade fina | Perde contexto de seção; muitos chunks pequenos | ✗ Descartada |
| Por sentença | Precisão máxima | Overhead de tokenização; contexto fragmentado | ✗ Excesso para MVP |

A janela deslizante é mantida como **fallback** para seções que excedam
`CHUNK_SIZE=800` caracteres (não ocorre no corpus atual, mas garante robustez).

### Parâmetros escolhidos

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `CHUNK_SIZE` | 800 chars | ≈ 150 palavras ≈ ~200 tokens, bem abaixo do limite de 256 tokens do all-MiniLM-L6-v2 |
| `CHUNK_OVERLAP` | 150 chars | Preserva contexto em fronteiras artificiais do fallback |
| `N_RESULTS` | 5 | Cobre queries multi-domínio (ex.: prazo + perigosa + frete especial) sem exceder contexto |
| `MIN_CHUNK_CHARS` | 60 | Descarta cabeçalhos sem conteúdo e seções de índice |

---

## Queries de exemplo e resultados esperados

| Query | Chunks esperados | Observação |
|-------|-----------------|------------|
| "Qual o prazo de devolução?" | POL-001 §3.1, §3.2 | Recupera regra geral + exceções |
| "Frete para 600kg para Manaus?" | PROC-042-v2 §2, §2.1 | Deve retornar v2 com Norte=1.8 |
| "Qual o SLA do cliente Gold?" | SLA-2024 §2 | Tabela com 2h resposta / 24h resolução |
| "Qual o SLA do cliente Platinum?" | SLA-2024 §1 | "Não existem outros tiers" |
| "Frete para 300kg?" | Nenhum chunk relevante | Pipeline correto responde "não encontrei" |
| "Carga danificada?" | FAQ-atendimento item 38 | Fonte informal — LLM deve indicar |

---

## Limitações e trade-offs

### 1. Modelo em inglês para corpus em português
`all-MiniLM-L6-v2` foi treinado principalmente em inglês. Para produção, usar
`paraphrase-multilingual-MiniLM-L12-v2` (384 dim, ~470 MB) ou um modelo
dedicado ao português como `neuralmind/bert-base-portuguese-cased`.
Neste PoC, o modelo funciona adequadamente porque o corpus mistura termos
técnicos (PROC-042, CT-e, ANTT) que são semanticamente agnósticos de idioma.

### 2. Contradição PROC-042 v1 vs v2
Ambas as versões são ingeridas. O pipeline retorna as duas quando a query é
sobre multiplicadores regionais. **O LLM deve decidir qual usar** — os chunks
da v2 contêm uma "seção 5" com a regra de transição (01/12/2023). O pipeline
não filtra automaticamente versões; isso é decisão de negócio.

### 3. FAQ como fonte não validada
O FAQ foi marcado como documento informal. O pipeline o ingere normalmente —
a lógica de confiabilidade está no prompt do sistema (`retrieve.py:SYSTEM_INSTRUCTIONS`),
não no retrieval.

### 4. Dados fora do escopo documentado
Frete padrão (< 500 kg) e tabela de fretes base (`\\novatech-fs\comercial\...`)
não existem no corpus. Perguntas sobre esses tópicos retornarão chunks de baixa
similaridade. O LLM deve responder "não encontrei a informação".

### 5. Persistência do ChromaDB
O ChromaDB local (`chroma_db/`) é um banco SQLite + índice HNSW em disco.
Para múltiplos usuários simultâneos ou escala maior, substituir por ChromaDB
Server ou outro vetor store (Qdrant, Weaviate, pgvector).

---

## Próximos passos (além do PoC)

1. **Modelo multilíngue** — `paraphrase-multilingual-MiniLM-L12-v2`
2. **Reranking** — Cross-encoder para reordenar os top-5 antes de montar o prompt
3. **Metadado de versão no retrieval** — Filtro ChromaDB para retornar apenas
   a versão mais recente de documentos com múltiplas versões
4. **Integração com Claude API** — Substituir o "cole o prompt manualmente" por
   chamada direta à API (adicionar `anthropic` ao pip install)
5. **Avaliação de resposta** — Além do retrieval, avaliar a qualidade da resposta
   gerada pelo LLM contra respostas de referência (RAGAS framework)
