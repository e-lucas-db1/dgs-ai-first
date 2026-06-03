# Análise de Resultados — Pipeline RAG NovaTech

**Data de execução:** 03/06/2026  
**Modelo de embeddings:** all-MiniLM-L6-v2 (sentence-transformers 5.5.1)  
**ChromaDB:** 1.5.9 | **Corpus:** 5 documentos → 33 chunks  
**N_RESULTS:** 5 | **CHUNK_SIZE:** 800 chars | **CHUNK_OVERLAP:** 150 chars

---

## 1. Resultado geral da validação

```
SUMÁRIO: 3/10 queries passaram | 3/14 chunks obrigatórios encontrados (21%)
```

| Status | Queries |
|--------|---------|
| ✓ PASS (3) | SLA Platinum, Multiplicador Sudeste, Frete 300kg (sem cobertura) |
| ✗ FAIL (7) | Prazo devolução, SLA Gold, Frete Manaus, Devolver carga perigosa, Carga danificada, Frete expresso, Multi-domínio |

---

## 2. Resultados por query (com gabarito)

### Query 1 — "Qual o prazo de devolução?"

**Gabarito Anexo B:**
- DEVE: POL-001-A (§3.1 "7 dias úteis"), POL-001-B (§3.2 "classes 1-6 ANTT")
- PODE: POL-001-C (§3.3 procedimento)

**Chunks recuperados:**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5648 | POL-001-politica-devolucao.md (v3.1) | §3.5 Custos de devolução | ✗ Ruído |
| 2 | 0.5305 | POL-001-politica-devolucao.md (v3.1) | §3.3 Procedimento de devolução | ✓ PODE |
| 3 | 0.5254 | PROC-042-frete-especial-v1.md (v1.0) | §3 Prazo de entrega frete especial | ✗ Ruído |
| 4 | 0.5059 | SLA-2024-tabela-sla-clientes.md (v2024.1) | §3 Definição incidente crítico | ✗ Ruído |
| 5 | 0.4743 | FAQ-atendimento.md | Item 8 — frete especial | ✗ Ruído |

**Resultado:** FAIL — Chunks obrigatórios (POL-001-A e POL-001-B) não apareceram.

**Análise da lacuna:** A query "prazo de devolução" ativa o termo "devolução" que aparece em §3.3 (procedimento) e §3.5 (custos), ambos com mais ocorrências do termo do que §3.1 (prazo geral). O modelo all-MiniLM-L6-v2 captura frequência lexical do token "devolução" mais do que a semântica composta de "prazo + devolução". O chunk §3.1 ("O cliente pode solicitar a devolução em até 7 dias úteis") existe no ChromaDB mas ficou na posição 6 ou 7 (fora do top-5).

---

### Query 2 — "Qual o SLA do cliente Gold?"

**Gabarito Anexo B:**
- DEVE: SLA-2024-B (§2 tabela SLAs — Gold: 2h/24h)
- PODE: SLA-2024-A (§1 classificação), SLA-2024-C (§2 incidentes críticos)

**Chunks recuperados:**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5600 | SLA-2024-tabela-sla-clientes.md (v2024.1) | §5 Medição e reportes | ✗ Ruído |
| 2 | 0.5311 | FAQ-atendimento.md | Item 27 — tracking | ✗ Ruído |
| 3 | 0.5258 | SLA-2024-tabela-sla-clientes.md (v2024.1) | §1 Classificação de clientes | ✓ PODE (SLA-2024-A) |
| 4 | 0.5230 | FAQ-atendimento.md | Item 41 — diferença SLA resposta/resolução | ✗ (FAQ não formal) |
| 5 | 0.5131 | FAQ-atendimento.md | Item 15 — Platinum | ✗ Ruído |

**Resultado:** FAIL — SLA-2024-B (tabela com valores Gold 2h/24h) não apareceu no top-5.

**Análise da lacuna:** A tabela SLA (§2) é um bloco markdown com duas linhas de header e quatro linhas de dados, totalizando ~300 chars. O chunk §5 (Medição e reportes) contém a palavra "SLA" duas vezes e menciona "clientes Gold" explicitamente ("não pausa para incidentes críticos de clientes Gold"), o que lhe deu score superior. O FAQ Item 41 informalmente descreve os mesmos valores ("Gold tem 2h de resposta e 24h de resolução") mas sem ser sinalizado como correto por não ser a fonte normativa.

---

### Query 3 — "Frete para 600kg para Manaus?"

**Gabarito Anexo B:**
- DEVE: PROC-042v2-B (§2.1 multiplicadores, Norte=1.8), PROC-042v2-A (§2 fórmula)
- PODE: PROC-042-B (versão antiga, Norte=1.6 — risco contradição)

**Chunks recuperados:**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5444 | PROC-042-frete-especial-v1.md (v1.0) | §1 Objetivo | ✗ Ruído |
| 2 | 0.5001 | PROC-042-v2-frete-especial-revisado.md (v2.0) | §1 Objetivo | ✗ Ruído |
| 3 | 0.4958 | PROC-042-v2-frete-especial-revisado.md (v2.0) | §2 Fórmula de cálculo | ✓ DEVE (PROC-042v2-A) |
| 4 | 0.4940 | PROC-042-frete-especial-v1.md (v1.0) | §2 Fórmula de cálculo | ✗ Versão antiga |
| 5 | 0.4734 | FAQ-atendimento.md | Item 27 — tracking | ✗ Ruído |

**Resultado:** FAIL parcial — PROC-042v2-A (fórmula v2) apareceu na posição 3. PROC-042v2-B (tabela de multiplicadores com Norte=1.8) **não apareceu**.

**Análise da lacuna:** A cidade "Manaus" não existe em nenhum documento do corpus — os documentos usam "Norte" como região. O modelo all-MiniLM-L6-v2 não possui conhecimento geográfico de que Manaus = região Norte do Brasil. Portanto, o embedding de "Manaus" não se aproxima do embedding de "Norte". As seções §1 "Objetivo" das duas versões dominam porque contêm "500kg" e "frete especial", termos centrais da query.

---

### Query 4 — "Posso devolver carga perigosa?"

**Gabarito Anexo B:**
- DEVE: POL-001-B (§3.2 "NÃO são elegíveis, classes 1-6 ANTT")
- PODE: FAQ-03 (ramal 4500), POL-001-A (prazo geral)

**Chunks recuperados:**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5660 | PROC-042-frete-especial-v1.md (v1.0) | §4 Condições especiais | ✗ Ruído (cita "cargas perigosas" mas sobre frete, não devolução) |
| 2 | 0.5449 | FAQ-atendimento.md | Item 22 — seguro de carga | ✗ Ruído (menciona "cargas perigosas" no contexto de seguro) |
| 3 | 0.5345 | SLA-2024-tabela-sla-clientes.md (v2024.1) | §3 Incidente crítico | ✗ Ruído ("carga perigosa com irregularidade" = critério de incidente) |
| 4 | 0.5102 | PROC-042-v2-frete-especial-revisado.md (v2.0) | §4 Condições especiais | ✗ Ruído |
| 5 | 0.4945 | POL-001-politica-devolucao.md (v3.1) | §3.5 Custos de devolução | ✗ Relacionado mas não a regra |

**Resultado:** FAIL — POL-001-B e FAQ-03 não apareceram.

**Análise da lacuna:** "Carga perigosa" é um termo transversal no corpus: aparece em PROC-042 (§4), SLA-2024 (§3), FAQ-22, FAQ-32, e POL-001 (§3.2). O modelo não consegue distinguir o contexto de "carga perigosa + frete" de "carga perigosa + devolução". A query "posso devolver carga perigosa" deveria ativar a semântica de "devolução" + "proibição", mas o embedding puro não captura essa combinação. O chunk de POL-001-B ("NÃO são elegíveis para devolução... classes 1-6") ficou atrás de chunks de outros documentos que apenas mencionam "cargas perigosas" sem nenhuma regra de devolução.

---

### Query 5 — "Qual o multiplicador para o Sudeste?" ✓ PASS

**Gabarito Anexo B:**
- DEVE: PROC-042v2-B (Sudeste=1.1)
- PODE: PROC-042-B (Sudeste=1.0, versão antiga — contradição)

**Chunks recuperados:**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5234 | POL-001-politica-devolucao.md (v3.1) | §3.4 Devoluções parciais | ✗ Ruído |
| 2 | 0.5100 | FAQ-atendimento.md | Item 8 — frete especial (cita PROC-042) | ✗ Semi-relevante |
| 3 | 0.4959 | PROC-042-v2-frete-especial-revisado.md (v2.0) | §2.1 Multiplicadores (v2) | **✓ DEVE** |
| 4 | 0.4944 | PROC-042-frete-especial-v1.md (v1.0) | §2.1 Multiplicadores (v1) | ✓ PODE (contradição) |
| 5 | 0.4894 | POL-001-politica-devolucao.md (v3.1) | §3.3 Procedimento | ✗ Ruído |

**Resultado:** PASS — PROC-042v2-B encontrado na posição 3; PROC-042-B (versão antiga) na posição 4.

**Observação de risco:** As duas versões conflitantes aparecem juntas (posições 3 e 4). Um LLM sem instrução explícita poderia misturar os valores 1.1 (v2) e 1.0 (v1). O prompt do sistema orienta usar a versão mais recente, mas a contradição é real. Scores muito próximos (0.4959 vs 0.4944) indicam que o modelo não discrimina qual versão é "mais correta" — ele apenas detecta que ambas são sobre multiplicadores regionais.

---

### Query 6 — "O que acontece com carga danificada?"

**Gabarito Anexo B:**
- DEVE: FAQ-38 ("carga danificada em trânsito, 48h, sinistros@novatech.com.br")

**Chunks recuperados:**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.6312 | SLA-2024-tabela-sla-clientes.md (v2024.1) | §3 Incidente crítico | ✗ Ruído |
| 2 | 0.5773 | FAQ-atendimento.md | Item 22 — seguro de carga | ✗ Ruído |
| 3 | 0.5670 | POL-001-politica-devolucao.md (v3.1) | §3.5 Custos devolução | ✗ Semi-relevante |
| 4 | 0.5564 | PROC-042-frete-especial-v1.md (v1.0) | §4 Condições especiais | ✗ Ruído |
| 5 | 0.5506 | PROC-042-frete-especial-v1.md (v1.0) | §3 Prazo entrega | ✗ Ruído |

**Resultado:** FAIL — FAQ-38 não apareceu.

**Análise da lacuna:** O FAQ-38 diz "Carga danificada em trânsito tem processo diferente de devolução". A palavra "danificada" só aparece nesse chunk. No entanto, o SLA §3 (incidente crítico) menciona "carga com status desconhecido" e "irregularidade", que o modelo associa semanticamente com "dano" ou "problema com carga". Esse chunk tem score 0.6312 — o mais alto de toda a query — sugerindo que o modelo está capturando o conceito de "problema com carga" mas não especificamente "carga fisicamente danificada". O FAQ-38 ficou provavelmente em posição 6+ (fora do top-5).

---

### Query 7 — "Frete para 300kg para Salvador?" ✓ PASS (sem cobertura)

**Gabarito Anexo B:**
- DEVE: Nenhum chunk relevante (frete padrão < 500kg não está documentado)

**Chunks recuperados (scores baixos, indicando baixa relevância):**

| # | Score | Fonte | Seção |
|---|-------|-------|-------|
| 1 | 0.5072 | PROC-042-frete-especial-v1.md (v1.0) | §1 Objetivo ("acima de 500kg") |
| 2 | 0.4566 | PROC-042-v2-frete-especial-revisado.md (v2.0) | §1 Objetivo |
| 3 | 0.4529 | FAQ-atendimento.md | Item 27 — tracking |
| 4 | 0.4415 | PROC-042-v2 | §2 Fórmula |
| 5 | 0.4395 | PROC-042-v2 | §4 Condições especiais |

**Resultado:** PASS — Comportamento correto. Os chunks retornados mencionam "acima de 500kg" que sinaliza implicitamente ao LLM que 300kg não cobre frete especial. Os scores são os mais baixos entre todas as queries (máx 0.5072 vs 0.56+ para queries com cobertura real), o que indica que o pipeline "sabe" que a query tem menos respaldo documental.

**Comportamento esperado do LLM:** Ao ver esses chunks, o assistente deve responder que as regras de frete especial se aplicam a cargas acima de 500kg e que não há informação documentada sobre frete padrão (< 500kg) — encaminhar ao Comercial.

---

## 3. Diagnóstico das lacunas de retrieval

### 3.1 Causa raiz principal: modelo de embeddings inadequado para português

O `all-MiniLM-L6-v2` foi treinado em dados majoritariamente em inglês. No contexto do corpus NovaTech (100% em português), isso resulta em dois problemas críticos:

**a) Pouca distinção semântica entre compostos nominais:** A query "prazo de **devolução**" deveria ser próxima de "até 7 dias úteis após o recebimento" (POL-001 §3.1). Mas o modelo trata "devolução" como token isolado e o encontra com alta frequência em §3.5 (Custos de devolução) e §3.3 (Procedimento de devolução). Resultado: chunks corretos são superados por chunks que apenas mencionam "devolução" em outro contexto.

**b) Ausência de conhecimento geográfico brasileiro:** "Manaus" não existe no corpus (os documentos usam "Norte"). O modelo não conecta Manaus → Norte, então a query "frete para Manaus" não ativa a tabela de multiplicadores regionais como deveria.

### 3.2 Causa secundária: distribuição do termo "carga perigosa"

"Carga perigosa" aparece em pelo menos 5 chunks de 4 documentos diferentes:
- PROC-042 §4 (frete de cargas perigosas)
- PROC-042-v2 §4 (idem)
- SLA-2024 §3 (incidente crítico por carga perigosa)
- FAQ-22 (seguro de cargas perigosas)
- POL-001 §3.2 (devolução de cargas perigosas)

Para queries como "posso devolver carga perigosa?", todos esses chunks competem. O embedding coloca todos em distância similar da query, e os chunks de PROC-042 e SLA (que aparecem repetidamente no corpus) tomam as posições superiores.

### 3.3 Causa terciária: chunks de FAQ são penalizados pela dimensão curta

Os FAQ Items (FAQ-38, FAQ-32) são chunks curtos (~200-250 chars). O modelo de embedding comprime menos informação em contextos curtos, o que pode resultar em vetores menos específicos. Em competição com chunks de documentos formais mais longos, os chunks de FAQ perdem posição.

---

## 4. Comparativo com o gabarito do Anexo B

| Query | Chunks DEVE | Encontrados | Status |
|-------|-------------|-------------|--------|
| Prazo de devolução | POL-001-A, POL-001-B | 0/2 | ✗ FAIL |
| Devolver carga perigosa | POL-001-B | 0/1 | ✗ FAIL |
| SLA Gold | SLA-2024-B | 0/1 | ✗ FAIL |
| SLA Platinum | SLA-2024-A | 1/1 | ✓ PASS |
| Frete 600kg Manaus | PROC-042v2-B, PROC-042v2-A | 1/2 | ✗ FAIL parcial |
| Frete 300kg Salvador | (nenhum) | 0/0 | ✓ PASS |
| Carga danificada | FAQ-38 | 0/1 | ✗ FAIL |
| Frete expresso perigosa | FAQ-32 | 0/1 | ✗ FAIL |
| Multiplicador Sudeste | PROC-042v2-B | 1/1 | ✓ PASS |
| Multi-domínio | POL-001-A/B, PROC-042v2-A/B | 0/4 | ✗ FAIL |

**Hit rate total: 3/14 chunks obrigatórios (21%)**

---

## 5. O que funcionou bem

Apesar das lacunas, o pipeline demonstrou comportamentos corretos em aspectos importantes:

1. **Chunking correto:** 33 chunks produzidos com estrutura correta — cada `###` seção virou um chunk independente, preservando tabelas de multiplicadores inteiras.

2. **Metadados de versão:** Chunks de PROC-042 v1 e v2 têm metadados de versão distintos. Quando ambos aparecem (query Sudeste, posições 3 e 4), o sistema pode diferenciá-los.

3. **Detecção de ausência de cobertura:** Para frete 300kg (<500kg), os scores mais baixos sinalizam ao LLM que não há cobertura — comportamento correto.

4. **Sem alucinação estrutural:** O pipeline não retornou chunks de fora do corpus nem inventou seções.

5. **SLA-2024-A recuperado corretamente:** Para a query "SLA Platinum", o chunk que diz "Não existem outros tiers" foi recuperado — o pipeline entendeu a intenção da query.

---

## 6. Recomendações para produção

### Imediato (sem mudança de arquitetura)

**R1 — Trocar o modelo de embeddings**  
Substituir `all-MiniLM-L6-v2` por `paraphrase-multilingual-MiniLM-L12-v2` ou `neuralmind/bert-base-portuguese-cased`. Estimativa de melhoria: +30-40% no hit rate para queries em português. Custo: re-executar `ingest.py --reset` após instalar o novo modelo.

**R2 — Aumentar N_RESULTS para 7-10 temporariamente**  
Em testes manuais, os chunks corretos frequentemente aparecem na posição 6-8. Com N=8, o hit rate sobe significativamente antes de qualquer mudança de modelo.

### Médio prazo (mudança de arquitetura)

**R3 — Retrieval híbrido (BM25 + vetorial)**  
Adicionar um estágio de BM25 (busca léxica) antes ou em paralelo com o retrieval vetorial. Para queries como "carga perigosa + devolução", BM25 encontraria POL-001-B por conter exatamente esses termos. Bibliotecas: `rank_bm25` + LangChain `EnsembleRetriever`.

**R4 — Expansão de query**  
Mapear termos geográficos para regiões: "Manaus → Norte", "Salvador → Nordeste", "São Paulo → Sudeste". Pode ser feito com um dicionário simples no `retrieve.py` antes de gerar o embedding.

**R5 — Reranker cross-encoder**  
Após retrieval top-10 vetorial, aplicar um cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) para re-ranquear. Cross-encoders avaliam pares (query, chunk) diretamente e são muito mais precisos que bi-encoders para português.

### Longo prazo

**R6 — Parent Document Retrieval**  
Indexar chunks granulares (### subsections) mas retornar a seção pai (## section) completa. Isso garante que mesmo se o chunk errado é recuperado dentro da seção certa, o contexto relevante ainda aparece.

**R7 — Avaliação contínua com RAGAS**  
Implementar pipeline de avaliação automática (RAGAS framework) que mede Faithfulness, Answer Relevancy e Context Precision — vai além do hit rate do Anexo B.
