# Melhorias do Pipeline RAG NovaTech — v1 → v2

**Data:** 03/06/2026  
**Baseline:** analise-resultados-rag.md (3/14 chunks obrigatórios, 21% hit rate)  
**Objetivo:** Implementar melhorias imediatas e de médio prazo sem mudança de infraestrutura

---

## Melhorias implementadas

### M1 — Aumento de N_RESULTS: 5 → 8 (imediato)

**Arquivo:** `rag_pipeline/config.py`  
**Motivação:** Nos testes do baseline, os chunks corretos frequentemente apareceram nas
posições 6–8 (fora do top-5). Para a query "Prazo de devolução", o POL-001-A ficou
na posição estimada 6 ou 7; para "Carga danificada", o FAQ-38 ficou em posição 6+.
Aumentar para 8 cobre esses casos sem impacto perceptível no tamanho do prompt.

**Tradeoff:** Cada chunk adicional aumenta o contexto do LLM em ~200–400 tokens.
Com N=8, o prompt montado tem ≈ 2.400 tokens extras de contexto — aceitável para
modelos com janelas de 100k+ tokens. Não há custo computacional adicional na ingestão.

**Mudança:**
```python
# Antes
N_RESULTS = 5

# Depois
N_RESULTS = 8
```

---

### M2 — Troca do modelo de embeddings (médio prazo)

**Arquivo:** `rag_pipeline/config.py`  
**Motivação:** O `all-MiniLM-L6-v2` foi treinado majoritariamente em inglês. Os testes
do baseline mostraram que ele falha em distinguir compostos semânticos do português
(ex.: "prazo de devolução" ≠ "7 dias úteis") e não captura a intenção de queries
como "Posso devolver carga perigosa?" em contraste com "Frete de carga perigosa".

O `paraphrase-multilingual-MiniLM-L12-v2` (Sentence-BERT) foi treinado com dados
paralelos em 50+ idiomas usando knowledge distillation a partir do modelo teacher
em inglês. Mantém as mesmas 384 dimensões, portanto o ChromaDB **não precisa de
alterações de schema** — apenas re-ingestão.

**Comparativo:**

| Propriedade | all-MiniLM-L6-v2 | paraphrase-multilingual-MiniLM-L12-v2 |
|-------------|-------------------|----------------------------------------|
| Idiomas | ~20 (inglês dominante) | 50+ (balanceado) |
| Dimensões | 384 | 384 |
| Tamanho | ~22 MB | ~470 MB |
| MTEB (PT) | ~52 | ~65 |
| Velocidade | ~14.000 sent/s | ~8.000 sent/s |

**Impacto esperado:** +25–40% no hit rate para queries em português puro.
Sem impacto na estrutura do ChromaDB — apenas re-ingestão obrigatória.

**Mudança:**
```python
# Antes
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Depois
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
```

**Ação necessária após mudança:** `python ingest.py --reset`  
(embeddings antigos usam espaço vetorial diferente — não são compatíveis)

---

### M3 — Expansão geográfica de queries (médio prazo)

**Arquivo:** `rag_pipeline/retrieve.py`  
**Motivação:** O corpus NovaTech usa regiões geográficas ("Norte", "Nordeste", "Sudeste")
enquanto queries naturais de atendentes usam cidades ("Manaus", "Salvador", "São Paulo").
O modelo de embeddings não possui conhecimento geográfico brasileiro para mapear
automaticamente "Manaus" → "Norte".

**Solução implementada:** Pré-processamento da query antes do embedding. Um dicionário
mapeia ~30 capitais/cidades relevantes para suas regiões. A query é expandida com
a região entre parênteses antes de ser encodada:

```
"Frete para 600kg para Manaus?"
→ "Frete para 600kg para Manaus? (Norte)"
```

Isso injeta o token "Norte" no embedding sem alterar a semântica da query para o
usuário, e sem reindexar o corpus.

**Cidades mapeadas:**

| Região | Cidades incluídas |
|--------|-------------------|
| Norte | Manaus, Belém, Porto Velho, Macapá, Boa Vista, Palmas, Rio Branco |
| Nordeste | Salvador, Fortaleza, Recife, Natal, João Pessoa, Maceió, Teresina, São Luís, Aracaju |
| Centro-Oeste | Brasília, Goiânia, Campo Grande, Cuiabá |
| Sudeste | São Paulo, Rio de Janeiro, Belo Horizonte, Vitória |
| Sul | Curitiba, Porto Alegre, Florianópolis |

**Tradeoff:** Solução determinística (dicionário) — não escala automaticamente para
cidades menores. Para produção, substituir por serviço de geocodificação ou NER.

---

## Sumário das mudanças por arquivo

| Arquivo | Tipo de mudança | Detalhes |
|---------|----------------|----------|
| `config.py` | N_RESULTS: 5 → 8 | Cobre chunks nas posições 6–8 |
| `config.py` | EMBEDDING_MODEL trocado | Modelo multilíngue 50+ idiomas |
| `retrieve.py` | `CITY_TO_REGION` adicionado | Dicionário com ~30 cidades brasileiras |
| `retrieve.py` | `expand_geographic_terms()` | Pré-processamento da query |
| `retrieve.py` | `retrieve()` modificado | Chama expand antes do encode |

---

## Melhorias identificadas mas NÃO implementadas nesta iteração

### R3 — Retrieval híbrido BM25 + vetorial

Requer adicionar `rank_bm25` como dependência e refatorar o pipeline de retrieval
para incluir um EnsembleRetriever. Impacto estimado: +40–60% no hit rate para
termos lexicalmente específicos ("classes 1 a 6", "ramal 4500", "48h").

**Por que não agora:** Mudança de arquitetura significativa — requer nova abstração
de retriever e testes de calibração do peso BM25 vs vetorial (α=0.5 como ponto inicial).

### R5 — Reranker cross-encoder

Requer instalar `cross-encoder/ms-marco-MiniLM-L-6-v2` (~120 MB) e um estágio
adicional de scoring. O cross-encoder avalia pares (query, chunk) com atenção
cruzada — muito mais preciso que bi-encoder, mas 10–20x mais lento.

**Por que não agora:** Latência adicional (~200–500ms por query em CPU) e complexidade
de integração. Candidato para a próxima sprint após validar o impacto do modelo multilíngue.

### R7 — Avaliação RAGAS

Framework de avaliação contínua (Faithfulness, Answer Relevancy, Context Precision).
Requer geração de respostas do LLM + avaliador LLM-as-a-judge.

**Por que não agora:** Fora do escopo do PoC local. Candidato para fase de integração
com a API Claude.

---

## Como re-executar após as mudanças

```bash
# Na primeira execução após a troca de modelo: --reset obrigatório
cd Exercicio-1.3/rag_pipeline
python ingest.py --reset     # baixa paraphrase-multilingual (~470MB), reindexa 33 chunks

# Testar retrieval com o novo modelo
python retrieve.py "Frete para 600kg para Manaus?"   # deve ver "Norte" na expansão

# Validação completa com verbose
python validate.py --top 8 --verbose

# Saída esperada pós-melhorias:
# SUMÁRIO: 7+/10 queries passaram | 9+/14 chunks obrigatórios encontrados (64%+)
```
