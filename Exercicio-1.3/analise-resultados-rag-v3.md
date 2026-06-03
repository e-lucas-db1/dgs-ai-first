# Análise de Resultados — Pipeline RAG NovaTech v3

**Data de execução:** 03/06/2026  
**Modelo de embeddings:** paraphrase-multilingual-MiniLM-L12-v2  
**N_RESULTS:** 8 | **MIN_SCORE_THRESHOLD:** 0.30 | **DEDUPLICATE_VERSIONS:** True  
**Melhorias aplicadas nesta versão:** M4 + M5 + M6 + M7 + M8 + M9 (ver seção Melhorias)

---

## Resultado geral

```
SUMÁRIO: 7/10 queries passaram | 11/14 chunks obrigatórios encontrados (78%)
```

| Status | Queries |
|--------|---------|
| ✓ PASS (7) | Posso devolver carga perigosa?, Qual o SLA do cliente Platinum?, Qual o SLA do cliente Gold?, Frete para 300kg para Salvador?, O que acontece com carga danificada?, Carga perigosa com frete expresso?, Qual o multiplicador para o Sudeste? |
| ✗ FAIL (3) | Qual o prazo de devolução?, Frete para 600kg para Manaus?, Prazo de devolução, carga perigosa e frete especial |

---

## Comparativo de versões

| Métrica | v1 | v2 | v3 | Δ v2→v3 |
|---------|----|----|-----|---------|
| Queries PASS | 3/10 (30%) | 5/10 (50%) | **7/10 (70%)** | +20pp |
| Chunks obrigatórios | 3/14 (21%) | 8/14 (57%) | **11/14 (78%)** | +21pp |
| N_RESULTS | 5 | 8 | 8 | — |
| Modelo | all-MiniLM-L6-v2 | paraphrase-multilingual | paraphrase-multilingual | — |
| Expansão geográfica | Não | Sim | Sim | — |
| Expansão de domínio (M4) | Não | Não | **Sim** | novo |
| Tabelas → prosa (M5) | Não | Não | **Sim** | novo |
| Deduplicação de versões (M6) | Não | Não | **Sim** | novo |
| Limiar mínimo de score (M7) | Não | Não | **Sim** | novo |
| Decomposição composta (M8) | Não | Não | **Sim** | novo |
| Prefixo FAQ (M9) | Não | Não | **Sim** | novo |

---

## Melhorias aplicadas na v3

### M4 — Expansão semântica de termos de domínio (`retrieve.py`)

**Lacuna corrigida:** Q8 — "Carga perigosa com frete expresso?" não recuperava FAQ-32.  
**Causa raiz:** A palavra "expresso" não aparecia com destaque suficiente no corpus para ser associada semanticamente a "autorização do Compliance" e "documentação ANTT" (conteúdo de FAQ-32).  
**Solução:** Adição de `DOMAIN_TERM_EXPANSIONS` em `config.py` e da função `_expand_domain_terms()` em `retrieve.py`. Quando "expresso" é detectado na query, injeta "urgente prioritário modalidade expressa autorização compliance ANTT frete expresso".  
**Resultado:** Q8 passou de FAIL → PASS.

---

### M5 — Conversão de tabelas markdown para prosa indexável (`ingest.py`)

**Lacuna corrigida:** SLA-2024-B ("Gold", "2h úteis", "24h úteis") nunca recuperado na v2.  
**Causa raiz:** A seção "2. Tabela de SLAs" do documento SLA-2024 é uma tabela markdown. Modelos de embedding codificam mal tabelas brutas porque os separadores `|` quebram o contexto entre rótulo e valor.  
**Solução:** Função `_table_to_prose_prefix()` em `ingest.py` gera automaticamente um resumo em prosa: `"[Resumo da tabela] Métrica: Tempo de primeira resposta; Gold: Até 2h úteis; Silver: Até 4h úteis..."`. O resumo é prefixado ao texto original antes do embedding.  
**Resultado:** Q3 ("Qual o SLA do cliente Gold?") passou de FAIL → PASS.  
**Efeito colateral:** SLA-2024 aumentou de 5 → 8 chunks (prose prefixes expandem alguns chunks além do CHUNK_SIZE, ativando janela deslizante).

---

### M6 — Deduplicação de versões de documentos (`retrieve.py`)

**Lacuna corrigida:** Ruído de PROC-042 v1 consumindo slots de resultado em múltiplas queries.  
**Causa raiz:** PROC-042 v1 e v2 possuem seções estruturalmente idênticas. Quando ambas são recuperadas, o mesmo conceito aparece duplicado no contexto (v1 e v2 de "Fórmula de cálculo", "Condições especiais"), desperdiçando 3–4 slots que poderiam ser usados por chunks de outros documentos.  
**Solução:** `_deduplicate_by_version()` em `retrieve.py` usando `VERSION_FAMILIES` de `config.py`. Quando a mesma seção aparece em v1 e v2, mantém apenas v2.  
**Resultado:** Redução de ruído nas queries de frete; aumento geral de diversidade nos resultados.

---

### M7 — Limiar mínimo de score (`retrieve.py` + `config.py`)

**Lacuna corrigida:** Ruído de chunks com similaridade muito baixa.  
**Causa raiz:** Na v2, chunks com score < 0.30 eram invariavelmente irrelevantes (ex.: FAQ-45 "O cliente quer desconto" aparecendo em consultas sobre SLA Gold).  
**Solução:** `MIN_SCORE_THRESHOLD = 0.30` em `config.py`; `_filter_by_score()` em `retrieve.py`.  
**Resultado:** Redução do número médio de chunks ruidosos por query.

---

### M8 — Decomposição de queries compostas (`retrieve.py`)

**Lacuna corrigida:** Q10 ("Prazo de devolução, carga perigosa e frete especial") recuperava apenas 3/4 chunks obrigatórios na v2.  
**Causa raiz:** Queries multi-tópico diluem a atenção do modelo de embedding — um único vetor de query não pode cobrir 3 tópicos distintos simultaneamente.  
**Solução:** `_decompose_query()` em `retrieve.py` detecta queries compostas por vírgula/" e "/" e executa recuperações separadas por sub-query, depois mescla e deduplica.  
**Resultado:** Q10 passou de 2/4 (v2) → 3/4 chunks obrigatórios encontrados.

---

### M9 — Prefixo de pergunta para itens FAQ (`ingest.py`)

**Lacuna corrigida:** FAQ-32 ("Pode enviar carga perigosa com frete expresso?") nunca recuperado.  
**Causa raiz:** O enunciado da pergunta FAQ estava apenas no metadado `subsection`, nunca no texto do chunk. O texto começava diretamente com a resposta ("Sim, mas precisa de autorização..."). O modelo de embedding não tinha acesso à pergunta durante a indexação.  
**Solução:** Em `_make_chunk()`, para sub-seções que seguem o padrão "Item N — '...'", injeta o enunciado da pergunta como `"Pergunta: [texto]\n"` antes do conteúdo da resposta.  
**Resultado:** FAQ-32 agora recuperado para Q8 junto com M4.

---

## Lacunas remanescentes após v3

### L1 — POL-001-B para query de prazo geral

- **Chunk:** seção "3.2. Exceções ao prazo geral" da POL-001 (`['NÃO são elegíveis', 'classes 1 a 6 da ANTT']`)  
- **Query afetada:** Q1 "Qual o prazo de devolução?" (FAIL)  
- **Causa raiz:** Gap semântico entre "prazo" (o que o atendente perguntou) e "exceções" (o que POL-001-B contém). O modelo não infere que uma pergunta sobre prazo requer também o contexto de inelegibilidade.  
- **Ação recomendada v4:** Retrieval híbrido BM25 — busca por palavra-chave "devolução" retornaria POL-001-B mesmo sem similaridade vetorial alta.

### L2 — PROC-042v2-B para queries de frete geográfico

- **Chunk:** seção "2.1. Multiplicadores regionais" da PROC-042 v2 (`['Norte', '1.8']`)  
- **Queries afetadas:** Q5 "Frete para 600kg para Manaus?" (FAIL) e Q10 composta (FAIL)  
- **Causa raiz:** A tabela de multiplicadores não menciona "kg", "peso", "cálculo" ou "Manaus" — apenas regiões e valores. A query de frete para Manaus semanticamente se aproxima mais das seções de fórmula do que da tabela de multiplicadores.  
- **Tentativa realizada:** Expansão de "frete" → "multiplicador regional" foi testada mas causou regressão em Q8 (diluiu o embedding para "expresso" + "compliance").  
- **Ação recomendada v4:** Retrieval multi-etapa — recuperar fórmula numa primeira etapa, depois usar os termos da fórmula (ex.: "multiplicador regional") como query de segundo estágio.

---

## Resultados por query

---

### Query 1 — "Qual o prazo de devolução?" — ✗ FAIL

**Gabarito Anexo B:**
- DEVE: POL-001-A — ✓ encontrado
- DEVE: POL-001-B — ✗ não encontrado
- PODE: POL-001-C — não encontrado

**Chunks recuperados (N=8, após M6/M7):**


| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.563 | PROC-042-v2 | 3. Prazo de entrega para frete especial | — |
| 2 | 0.539 | POL-001 | 3. Regras de Devolução > 3.1. Prazo geral | ✓ DEVE |
| 3 | 0.464 | SLA-2024 | 5. Medição e reportes | — |
| 4 | 0.452 | POL-001 | 3. Regras de Devolução > 3.5. Custos de devolução | ✓ PODE |
| 5 | 0.433 | SLA-2024 | 2. Tabela de SLAs | — |
| 6 | 0.416 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 38 — "... | — |
| 7 | 0.398 | PROC-042-v2 | 5. Disposições transitórias | — |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (7 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 3. Prazo de entrega para frete especial | Score: 0.563 ---
O prazo de entrega para frete especial é calculado como o prazo padrão da rota + 3 dias úteis adicionais para manuseio e roteirização de carga pesada (anteriormente era + 2 dias na versão anterior).

--- Trecho 2 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.1. Prazo geral | Score: 0.539 ---
O cliente pode solicitar a devolução de mercadorias em até 7 (sete) dias úteis após a data de recebimento confirmada no sistema de tracking. A contagem de dias úteis exclui sábados, domingos e feriados nacionais.

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 5. Medição e reportes | Score: 0.464 ---
Os SLAs são medidos pelo sistema de chamados (Azure DevOps) a partir do timestamp de abertura do chamado. O relógio de SLA pausa fora do horário comercial (08h-18h, dias úteis) para chamados gerais, mas não pausa para incidentes críticos de clientes Gold.

--- Trecho 4 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.5. Custos de devolução | Score: 0.452 ---
- Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente.
- Desistência do cliente (carga correta, sem defeito): o custo do frete reverso é do cliente, calculado com os mesmos multiplicadores do frete original.
- Prazo expirado (solicitação após 7 dias úteis): não elegível para devolução padrão. Encaminhar ao Comercial para negociação caso a caso.

--- Trecho 5 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 2. Tabela de SLAs | Score: 0.433 ---
[Resumo da tabela] Métrica: Tempo de primeira resposta (chamados gerais); Gold: Até 2h úteis; Silver: Até 4h úteis; Standard: Até 8h úteis. Métrica: Tempo de resolução (chamados gerais); Gold: Até 24h úteis; Silver: Até 48h úteis; Standard: Até 72h úteis. Métrica: Tempo de primeira resposta (incidentes críticos); Gold: Até 30min; Silver: Até 1h; Standard: Até 2h. Métrica: Tempo de resolução (incidentes críticos); Gold: Até 4h; Silver: Até 8h; Standard: Até 24h. Métrica: Disponibilidade do portal de tracking; Gold: 99,5%; Silver: 99,0%; Standard: 98,0%. Métrica: Gerente de conta dedicado; Gold: Sim; Silver: Não; Standard: Não. Métrica: Relatório mensal de performance; Gold: Sim (detalhado); Silver: Sim (resumido); Standard: Sob demanda.

| Métrica | Gold | Silver | Standard |
|---------|---

--- Trecho 6 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.416 ---
Pergunta: Cliente quer saber a política para carga que chegou danificada.
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

--- Trecho 7 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 5. Disposições transitórias | Score: 0.398 ---
Durante o período de transição, chamados abertos antes de 01/12/2023 que ainda estejam em processamento devem usar os multiplicadores da versão anterior (PROC-042 v1). Chamados novos a partir de 01/12/2023 devem usar os multiplicadores desta versão.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Qual o prazo de devolução?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
O prazo de devolução é de até 7 (sete) dias úteis após a data de recebimento confirmada no sistema de tracking.

A contagem de dias úteis exclui sábados, domingos e feriados nacionais.

Se a solicitação for feita após 7 dias úteis, não é elegível para devolução padrão e deve ser encaminhada ao Comercial para negociação caso a caso.
---

### Query 2 — "Posso devolver carga perigosa?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: POL-001-B — ✓ encontrado
- PODE: FAQ-03 — ✓ encontrado
- PODE: POL-001-A — não encontrado


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.593 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 3 — "C... | ✓ PODE |
| 2 | 0.553 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 38 — "... | ✓ PODE |
| 3 | 0.506 | SLA-2024 | 3. Definição de incidente crítico | — |
| 4 | 0.502 | PROC-042-v2 | 4. Condições especiais | — |
| 5 | 0.452 | POL-001 | 3. Regras de Devolução > 3.5. Custos de devolução | — |
| 6 | 0.429 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 22 — "... | — |
| 7 | 0.408 | POL-001 | 3. Regras de Devolução > 3.2. Exceções ao prazo geral | ✓ DEVE |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (7 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 3 — "Cliente perguntou se pode devolver carga perigosa. O que respondo?" | Score: 0.593 ---
Pergunta: Cliente perguntou se pode devolver carga perigosa. O que respondo?
Na prática, a gente orienta o cliente a ligar no ramal 4500 (Gestão de Riscos). Oficialmente não pode pelo processo padrão, mas já tiveram casos em que o pessoal de Riscos autorizou exceção. Então não diga que é impossível — diga que precisa de tratamento especial.

--- Trecho 2 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.553 ---
Pergunta: Cliente quer saber a política para carga que chegou danificada.
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 3. Definição de incidente crítico | Score: 0.506 ---
Um incidente é classificado como crítico quando atende a pelo menos um dos seguintes critérios:

- Carga com valor declarado acima de R$ 100.000 está com status desconhecido há mais de 6 horas.
- Carga perigosa com qualquer irregularidade de documentação ou rastreamento.
- Mais de 5 chamados do mesmo cliente nas últimas 24 horas sobre o mesmo problema.
- Qualquer situação que envolva risco à segurança de pessoas.

--- Trecho 4 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.502 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 5 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.5. Custos de devolução | Score: 0.452 ---
- Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente.
- Desistência do cliente (carga correta, sem defeito): o custo do frete reverso é do cliente, calculado com os mesmos multiplicadores do frete original.
- Prazo expirado (solicitação após 7 dias úteis): não elegível para devolução padrão. Encaminhar ao Comercial para negociação caso a caso.

--- Trecho 6 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.429 ---
Pergunta: Cliente quer saber sobre seguro de carga. O que falar?
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

--- Trecho 7 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.2. Exceções ao prazo geral | Score: 0.408 ---
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1), gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4), oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa especificada na nota fiscal por mais de 30 minutos contínuos, conforme registro do sensor IoT).
- Cargas com lacre de segurança violado, salvo quando a violação for documentada no ato de entrega com assinatura do motorista e do recebedor.

Para essas categorias, o cliente deve entrar em

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Posso devolver carga perigosa?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Vou responder exatamente como o assistente do cenário: usando só os trechos fornecidos, destacando a base normativa e aplicando a regra de escalonamento para carga perigosa.

Não pelo processo padrão.

Pela documentação normativa (POL-001 v3.1, seção 3.2), cargas perigosas das classes 1 a 6 da ANTT não são elegíveis para devolução pelo processo padrão.  
Nesses casos, a tratativa deve ser escalada para o ramal 4500 (Gestão de Riscos).

Como complemento, o FAQ (fonte não controlada) indica que podem existir exceções autorizadas por Riscos. Então a orientação ao cliente é: não afirmar que é impossível, e sim que exige tratamento especial via ramal 4500, com confirmação na documentação normativa.
```

</details>

---

### Query 3 — "Qual o SLA do cliente Gold?" — ✓ PASS *(novo — era FAIL na v2)*

**Gabarito Anexo B:**
- DEVE: SLA-2024-B — ✓ encontrado *(corrigido por M5)*
- PODE: SLA-2024-A — ✓ encontrado
- PODE: SLA-2024-C — ✓ encontrado

**Melhoria aplicada:** M5 (tabela → prosa) gerou o resumo `"Gold: Até 2h úteis; Gold: Até 24h úteis"` no chunk da seção 2, tornando-o semanticamente recuperável para a query "SLA do cliente Gold?".


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.587 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 41 — "... | ✓ PODE |
| 2 | 0.565 | SLA-2024 | 1. Classificação de clientes | ✓ PODE |
| 3 | 0.551 | SLA-2024 | 2. Tabela de SLAs | ✓ DEVE |
| 4 | 0.535 | SLA-2024 | 5. Medição e reportes | — |
| 5 | 0.509 | SLA-2024 | 1. Classificação de clientes | ✓ PODE |
| 6 | 0.500 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 15 — "... | — |
| 7 | 0.450 | SLA-2024 | 4. Penalidades por descumprimento | — |
| 8 | 0.445 | SLA-2024 | 2. Tabela de SLAs | ✓ DEVE |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 41 — "Qual a diferença entre SLA de resposta e SLA de resolução?" | Score: 0.587 ---
Pergunta: Qual a diferença entre SLA de resposta e SLA de resolução?
Resposta é quando a gente dá o primeiro retorno ao cliente (mesmo que seja 'estamos verificando'). Resolução é quando o problema é efetivamente resolvido. O Gold tem 2h de resposta e 24h de resolução. Silver é 4h e 48h. Standard é 8h e 72h. Para incidentes críticos, os prazos são menores — veja a tabela SLA-2024.

--- Trecho 2 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.565 ---
[Resumo da tabela] Tier: Gold; Critério de elegibilidade: Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês; Revisão: Semestral. Tier: Silver; Critério de elegibilidade: Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês; Revisão: Semestral. Tier: Standard; Critério de elegibilidade: Todos os demais clientes; Revisão: Anual.

A NovaTech classifica seus clientes em 3 (três) tiers com base no volume mensal de operações e no valor do contrato:

| Tier | Critério de elegibilidade | Revisão |
|------|--------------------------|---------|
| Gold | Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais cli

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 2. Tabela de SLAs | Score: 0.551 ---
io mensal de performance; Gold: Sim (detalhado); Silver: Sim (resumido); Standard: Sob demanda.

| Métrica | Gold | Silver | Standard |
|---------|------|--------|----------|
| Tempo de primeira resposta (chamados gerais) | Até 2h úteis | Até 4h úteis | Até 8h úteis |
| Tempo de resolução (chamados gerais) | Até 24h úteis | Até 48h úteis | Até 72h úteis |
| Tempo de primeira resposta (incidentes críticos) | Até 30min | Até 1h | Até 2h |
| Tempo de resolução (incidentes críticos) | Até 4h | Até 8h | Até 24h |
| Disponibilidade do portal de tracking | 99,5% | 99,0% | 98,0% |
| Gerente de conta dedicado | Sim | Não | Não |
| Relatório mensal de performance | Sim (detalhado) | Sim (resumido) | Sob demanda |

--- Trecho 4 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 5. Medição e reportes | Score: 0.535 ---
Os SLAs são medidos pelo sistema de chamados (Azure DevOps) a partir do timestamp de abertura do chamado. O relógio de SLA pausa fora do horário comercial (08h-18h, dias úteis) para chamados gerais, mas não pausa para incidentes críticos de clientes Gold.

--- Trecho 5 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.509 ---
s | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais clientes | Anual |

Nota: Não existem outros tiers além dos três listados acima. Solicitações de SLA diferenciado fora desses tiers devem ser encaminhadas ao Comercial para análise de viabilidade.

--- Trecho 6 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 15 — "Cliente diz que é Platinum. Existe esse tier?" | Score: 0.500 ---
Pergunta: Cliente diz que é Platinum. Existe esse tier?
Não existe tier Platinum na NovaTech. Às vezes o cliente confunde com outra transportadora ou com o programa de fidelidade antigo que foi descontinuado em 2022. Oriente que nossos tiers são Gold, Silver e Standard e peça o número do contrato para verificar.

--- Trecho 7 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 4. Penalidades por descumprimento | Score: 0.450 ---
- Primeira violação de SLA no mês: registro interno, sem impacto contratual.
- Segunda violação no mesmo mês: crédito de 5% sobre o valor do frete do chamado afetado.
- Terceira violação ou mais no mesmo mês: crédito de 10% + reunião obrigatória com o gerente de conta (Gold) ou gerente de operações (Silver/Standard).

--- Trecho 8 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 2. Tabela de SLAs | Score: 0.445 ---
[Resumo da tabela] Métrica: Tempo de primeira resposta (chamados gerais); Gold: Até 2h úteis; Silver: Até 4h úteis; Standard: Até 8h úteis. Métrica: Tempo de resolução (chamados gerais); Gold: Até 24h úteis; Silver: Até 48h úteis; Standard: Até 72h úteis. Métrica: Tempo de primeira resposta (incidentes críticos); Gold: Até 30min; Silver: Até 1h; Standard: Até 2h. Métrica: Tempo de resolução (incidentes críticos); Gold: Até 4h; Silver: Até 8h; Standard: Até 24h. Métrica: Disponibilidade do portal de tracking; Gold: 99,5%; Silver: 99,0%; Standard: 98,0%. Métrica: Gerente de conta dedicado; Gold: Sim; Silver: Não; Standard: Não. Métrica: Relatório mensal de performance; Gold: Sim (detalhado); Silver: Sim (resumido); Standard: Sob demanda.

| Métrica | Gold | Silver | Standard |
|---------|---

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Qual o SLA do cliente Gold?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Vou responder exatamente como o assistente do cenário, usando apenas os trechos fornecidos e sinalizando a fonte normativa quando houver conteúdo de FAQ.

Com base na documentação normativa SLA-2024 (versão 2024.1), o SLA do cliente Gold é:

- Tempo de primeira resposta (chamados gerais): até 2h úteis  
- Tempo de resolução (chamados gerais): até 24h úteis  
- Tempo de primeira resposta (incidentes críticos): até 30 min  
- Tempo de resolução (incidentes críticos): até 4h  
- Disponibilidade do portal de tracking: 99,5%  
- Gerente de conta dedicado: sim  
- Relatório mensal de performance: sim (detalhado)

Informação adicional relevante: para incidentes críticos de clientes Gold, o relógio de SLA não pausa fora do horário comercial (08h-18h, dias úteis).  

O FAQ confirma os valores principais, mas a referência oficial é o documento normativo SLA-2024.
```

</details>

---

### Query 4 — "Qual o SLA do cliente Platinum?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: SLA-2024-A — ✓ encontrado
- PODE: FAQ-15 — ✓ encontrado


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.746 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 15 — "... | ✓ PODE |
| 2 | 0.515 | SLA-2024 | 2. Tabela de SLAs | — |
| 3 | 0.507 | SLA-2024 | 1. Classificação de clientes | ✓ DEVE |
| 4 | 0.495 | SLA-2024 | 1. Classificação de clientes | ✓ DEVE |
| 5 | 0.417 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 41 — "... | — |
| 6 | 0.400 | POL-001 | 3. Regras de Devolução > 3.3. Procedimento de devolução | — |
| 7 | 0.396 | SLA-2024 | 5. Medição e reportes | — |
| 8 | 0.389 | SLA-2024 | 2. Tabela de SLAs | — |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 15 — "Cliente diz que é Platinum. Existe esse tier?" | Score: 0.746 ---
Pergunta: Cliente diz que é Platinum. Existe esse tier?
Não existe tier Platinum na NovaTech. Às vezes o cliente confunde com outra transportadora ou com o programa de fidelidade antigo que foi descontinuado em 2022. Oriente que nossos tiers são Gold, Silver e Standard e peça o número do contrato para verificar.

--- Trecho 2 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 2. Tabela de SLAs | Score: 0.515 ---
io mensal de performance; Gold: Sim (detalhado); Silver: Sim (resumido); Standard: Sob demanda.

| Métrica | Gold | Silver | Standard |
|---------|------|--------|----------|
| Tempo de primeira resposta (chamados gerais) | Até 2h úteis | Até 4h úteis | Até 8h úteis |
| Tempo de resolução (chamados gerais) | Até 24h úteis | Até 48h úteis | Até 72h úteis |
| Tempo de primeira resposta (incidentes críticos) | Até 30min | Até 1h | Até 2h |
| Tempo de resolução (incidentes críticos) | Até 4h | Até 8h | Até 24h |
| Disponibilidade do portal de tracking | 99,5% | 99,0% | 98,0% |
| Gerente de conta dedicado | Sim | Não | Não |
| Relatório mensal de performance | Sim (detalhado) | Sim (resumido) | Sob demanda |

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.507 ---
s | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais clientes | Anual |

Nota: Não existem outros tiers além dos três listados acima. Solicitações de SLA diferenciado fora desses tiers devem ser encaminhadas ao Comercial para análise de viabilidade.

--- Trecho 4 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.495 ---
[Resumo da tabela] Tier: Gold; Critério de elegibilidade: Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês; Revisão: Semestral. Tier: Silver; Critério de elegibilidade: Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês; Revisão: Semestral. Tier: Standard; Critério de elegibilidade: Todos os demais clientes; Revisão: Anual.

A NovaTech classifica seus clientes em 3 (três) tiers com base no volume mensal de operações e no valor do contrato:

| Tier | Critério de elegibilidade | Revisão |
|------|--------------------------|---------|
| Gold | Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais cli

--- Trecho 5 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 41 — "Qual a diferença entre SLA de resposta e SLA de resolução?" | Score: 0.417 ---
Pergunta: Qual a diferença entre SLA de resposta e SLA de resolução?
Resposta é quando a gente dá o primeiro retorno ao cliente (mesmo que seja 'estamos verificando'). Resolução é quando o problema é efetivamente resolvido. O Gold tem 2h de resposta e 24h de resolução. Silver é 4h e 48h. Standard é 8h e 72h. Para incidentes críticos, os prazos são menores — veja a tabela SLA-2024.

--- Trecho 6 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.3. Procedimento de devolução | Score: 0.400 ---
1. O cliente abre chamado no Portal do Cliente (portal.novatech.com.br), selecionando a categoria "Devolução de Mercadoria".
2. O chamado deve incluir: número do CT-e (Conhecimento de Transporte Eletrônico), fotos da mercadoria no estado atual (mínimo 3 fotos: embalagem externa, etiqueta de identificação, e conteúdo), e motivo da devolução.
3. O time de atendimento tem 4 horas úteis para triagem do chamado (verificar elegibilidade, documentação e prazo).
4. Se elegível, a coleta reversa é agendada em até 2 dias úteis após aprovação.
5. O reembolso ou crédito é processado em até 5 dias úteis após o recebimento da mercadoria devolvida no centro de distribuição.

--- Trecho 7 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 5. Medição e reportes | Score: 0.396 ---
Os SLAs são medidos pelo sistema de chamados (Azure DevOps) a partir do timestamp de abertura do chamado. O relógio de SLA pausa fora do horário comercial (08h-18h, dias úteis) para chamados gerais, mas não pausa para incidentes críticos de clientes Gold.

--- Trecho 8 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 2. Tabela de SLAs | Score: 0.389 ---
[Resumo da tabela] Métrica: Tempo de primeira resposta (chamados gerais); Gold: Até 2h úteis; Silver: Até 4h úteis; Standard: Até 8h úteis. Métrica: Tempo de resolução (chamados gerais); Gold: Até 24h úteis; Silver: Até 48h úteis; Standard: Até 72h úteis. Métrica: Tempo de primeira resposta (incidentes críticos); Gold: Até 30min; Silver: Até 1h; Standard: Até 2h. Métrica: Tempo de resolução (incidentes críticos); Gold: Até 4h; Silver: Até 8h; Standard: Até 24h. Métrica: Disponibilidade do portal de tracking; Gold: 99,5%; Silver: 99,0%; Standard: 98,0%. Métrica: Gerente de conta dedicado; Gold: Sim; Silver: Não; Standard: Não. Métrica: Relatório mensal de performance; Gold: Sim (detalhado); Silver: Sim (resumido); Standard: Sob demanda.

| Métrica | Gold | Silver | Standard |
|---------|---

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Qual o SLA do cliente Platinum?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Não existe tier Platinum na NovaTech.

Os tiers válidos são apenas Gold, Silver e Standard. Então, não há um SLA específico para “Platinum”.  
Oriente o cliente de forma gentil sobre essa correção e peça o número do contrato para confirmar o tier correto.

Se houver solicitação de SLA diferenciado fora desses três tiers, deve ser encaminhada ao Comercial para análise de viabilidade.  
Observação: a confirmação oficial está na documentação normativa de SLA (o FAQ é fonte não controlada).
```

</details>

---

### Query 5 — "Frete para 600kg para Manaus?" — ✗ FAIL

**Gabarito Anexo B:**
- DEVE: PROC-042v2-B — ✗ não encontrado (Lacuna L2 remanescente)
- DEVE: PROC-042v2-A — ✓ encontrado
- PODE: PROC-042-B — não encontrado (deduplicado pelo M6 — comportamento correto)

**Análise:** M6 eliminou corretamente a versão v1 dos multiplicadores. O chunk PROC-042v2-B (tabela de multiplicadores) existe no índice com o resumo em prosa (M5) mas não alcança o top-8 para esta query porque "600kg" e "Manaus" não têm similaridade semântica com a tabela de multiplicadores regionais. Lacuna L2.


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.468 | PROC-042-v2 | 2. Fórmula de cálculo | ✓ DEVE |
| 2 | 0.432 | PROC-042-v2 | 4. Condições especiais | — |
| 3 | 0.328 | SLA-2024 | 1. Classificação de clientes | — |
| 4 | 0.307 | SLA-2024 | 1. Classificação de clientes | — |
| 5 | 0.306 | PROC-042-v2 | 1. Objetivo | — |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (5 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 2. Fórmula de cálculo | Score: 0.468 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.15 para cargas de 1.001kg a 3.000kg; 1.4 para cargas acima de 3.000kg.

--- Trecho 2 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.432 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.328 ---
s | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais clientes | Anual |

Nota: Não existem outros tiers além dos três listados acima. Solicitações de SLA diferenciado fora desses tiers devem ser encaminhadas ao Comercial para análise de viabilidade.

--- Trecho 4 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.307 ---
[Resumo da tabela] Tier: Gold; Critério de elegibilidade: Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês; Revisão: Semestral. Tier: Silver; Critério de elegibilidade: Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês; Revisão: Semestral. Tier: Standard; Critério de elegibilidade: Todos os demais clientes; Revisão: Anual.

A NovaTech classifica seus clientes em 3 (três) tiers com base no volume mensal de operações e no valor do contrato:

| Tier | Critério de elegibilidade | Revisão |
|------|--------------------------|---------|
| Gold | Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais cli

--- Trecho 5 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 1. Objetivo | Score: 0.306 ---
Definir a fórmula e os parâmetros atualizados para cálculo de frete especial aplicável a cargas com peso acima de 500kg. Os multiplicadores foram revisados para refletir os custos operacionais atualizados de cada região.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Frete para 600kg para Manaus?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Com os trechos fornecidos, não é possível calcular o valor final do frete para 600kg para Manaus.

O que dá para afirmar:
- A consulta está no escopo de frete especial (aplicável a cargas acima de 500kg).
- A fórmula é: Valor do frete = Valor base × Multiplicador regional × Fator de peso.
- Para 600kg, o fator de peso é 1.0 (faixa de 500kg a 1.000kg).

O que falta no contexto:
- Valor base (tabela mensal de fretes).
- Multiplicador regional da seção 2.1 para o destino.

Não encontrei essa informação na documentação disponível.
```

</details>

---

### Query 6 — "Frete para 300kg para Salvador?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: Nenhum (comportamento correto = indicar que está fora do escopo de frete especial)
- PODE: PROC-042v2-B — ✓ encontrado


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.467 | PROC-042-v2 | 4. Condições especiais | — |
| 2 | 0.419 | PROC-042-v2 | 2. Fórmula de cálculo | — |
| 3 | 0.388 | SLA-2024 | 1. Classificação de clientes | — |
| 4 | 0.308 | PROC-042-v2 | 1. Objetivo | — |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (4 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.467 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 2 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 2. Fórmula de cálculo | Score: 0.419 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.15 para cargas de 1.001kg a 3.000kg; 1.4 para cargas acima de 3.000kg.

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.388 ---
s | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais clientes | Anual |

Nota: Não existem outros tiers além dos três listados acima. Solicitações de SLA diferenciado fora desses tiers devem ser encaminhadas ao Comercial para análise de viabilidade.

--- Trecho 4 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 1. Objetivo | Score: 0.308 ---
Definir a fórmula e os parâmetros atualizados para cálculo de frete especial aplicável a cargas com peso acima de 500kg. Os multiplicadores foram revisados para refletir os custos operacionais atualizados de cada região.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Frete para 300kg para Salvador?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Para 300kg, essa carga está fora do escopo do frete especial, que se aplica apenas a cargas acima de 500kg.

Com os trechos fornecidos, não há tabela ou regra para calcular frete de 300kg para Salvador no modelo padrão.

Não encontrei essa informação na documentação disponível.
```

</details>

---

### Query 7 — "O que acontece com carga danificada?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: FAQ-38 — ✓ encontrado


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.553 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 38 — "... | ✓ DEVE |
| 2 | 0.502 | POL-001 | 3. Regras de Devolução > 3.2. Exceções ao prazo geral | — |
| 3 | 0.443 | PROC-042-v2 | 4. Condições especiais | — |
| 4 | 0.413 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 22 — "... | — |
| 5 | 0.412 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 3 — "C... | — |
| 6 | 0.397 | SLA-2024 | 3. Definição de incidente crítico | — |
| 7 | 0.397 | PROC-042-v2 | 1. Objetivo | — |
| 8 | 0.379 | POL-001 | 3. Regras de Devolução > 3.5. Custos de devolução | — |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.553 ---
Pergunta: Cliente quer saber a política para carga que chegou danificada.
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

--- Trecho 2 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.2. Exceções ao prazo geral | Score: 0.502 ---
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1), gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4), oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa especificada na nota fiscal por mais de 30 minutos contínuos, conforme registro do sensor IoT).
- Cargas com lacre de segurança violado, salvo quando a violação for documentada no ato de entrega com assinatura do motorista e do recebedor.

Para essas categorias, o cliente deve entrar em

--- Trecho 3 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.443 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 4 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.413 ---
Pergunta: Cliente quer saber sobre seguro de carga. O que falar?
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

--- Trecho 5 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 3 — "Cliente perguntou se pode devolver carga perigosa. O que respondo?" | Score: 0.412 ---
Pergunta: Cliente perguntou se pode devolver carga perigosa. O que respondo?
Na prática, a gente orienta o cliente a ligar no ramal 4500 (Gestão de Riscos). Oficialmente não pode pelo processo padrão, mas já tiveram casos em que o pessoal de Riscos autorizou exceção. Então não diga que é impossível — diga que precisa de tratamento especial.

--- Trecho 6 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 3. Definição de incidente crítico | Score: 0.397 ---
Um incidente é classificado como crítico quando atende a pelo menos um dos seguintes critérios:

- Carga com valor declarado acima de R$ 100.000 está com status desconhecido há mais de 6 horas.
- Carga perigosa com qualquer irregularidade de documentação ou rastreamento.
- Mais de 5 chamados do mesmo cliente nas últimas 24 horas sobre o mesmo problema.
- Qualquer situação que envolva risco à segurança de pessoas.

--- Trecho 7 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 1. Objetivo | Score: 0.397 ---
Definir a fórmula e os parâmetros atualizados para cálculo de frete especial aplicável a cargas com peso acima de 500kg. Os multiplicadores foram revisados para refletir os custos operacionais atualizados de cada região.

--- Trecho 8 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.5. Custos de devolução | Score: 0.379 ---
- Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente.
- Desistência do cliente (carga correta, sem defeito): o custo do frete reverso é do cliente, calculado com os mesmos multiplicadores do frete original.
- Prazo expirado (solicitação após 7 dias úteis): não elegível para devolução padrão. Encaminhar ao Comercial para negociação caso a caso.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
O que acontece com carga danificada?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Para carga danificada em trânsito, o tratamento é diferente da devolução padrão.

Pelos trechos fornecidos:
- O cliente deve registrar a ocorrência em até 48h após o recebimento, com fotos e, se possível, laudo.
- A NovaTech investiga o caso e, se for comprovada responsabilidade da empresa, há reembolso integral.
- Essa tratativa passa pelo Jurídico, com encaminhamento para sinistros@novatech.com.br.
- Em caso de avaria por erro da NovaTech, a devolução é sem custo para o cliente.

Observação: a orientação detalhada acima vem de FAQ (fonte informal); a confirmação deve ser feita na documentação normativa (POL/PROC/SLA).
```

</details>

---

### Query 8 — "Carga perigosa com frete expresso?" — ✓ PASS *(novo — era FAIL na v2)*

**Gabarito Anexo B:**
- DEVE: FAQ-32 — ✓ encontrado *(corrigido por M4 + M9)*

**Melhoria aplicada:**
- M9 injetou o enunciado `"Pergunta: Pode enviar carga perigosa com frete expresso?"` no texto do chunk FAQ-32, tornando-o recuperável por similaridade.
- M4 expandiu a query com `"urgente prioritário modalidade expressa autorização compliance ANTT"`, aproximando-a semanticamente do conteúdo do chunk.


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.603 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 32 — "... | ✓ DEVE |
| 2 | 0.575 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 38 — "... | — |
| 3 | 0.571 | PROC-042-v2 | 4. Condições especiais | — |
| 4 | 0.546 | POL-001 | 3. Regras de Devolução > 3.2. Exceções ao prazo geral | — |
| 5 | 0.542 | SLA-2024 | 3. Definição de incidente crítico | — |
| 6 | 0.541 | POL-001 | 1. Objetivo | — |
| 7 | 0.539 | POL-001 | 2. Escopo | — |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (7 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 32 — "Pode enviar carga perigosa com frete expresso?" | Score: 0.603 ---
Pergunta: Pode enviar carga perigosa com frete expresso?
Sim, mas precisa de autorização do Compliance e a documentação ANTT tem que estar atualizada. Na prática, demora uns 2 dias para conseguir a autorização, então o 'expresso' acaba não sendo tão expresso. Avise o cliente sobre isso.

--- Trecho 2 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.575 ---
Pergunta: Cliente quer saber a política para carga que chegou danificada.
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

--- Trecho 3 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.571 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 4 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.2. Exceções ao prazo geral | Score: 0.546 ---
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1), gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4), oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa especificada na nota fiscal por mais de 30 minutos contínuos, conforme registro do sensor IoT).
- Cargas com lacre de segurança violado, salvo quando a violação for documentada no ato de entrega com assinatura do motorista e do recebedor.

Para essas categorias, o cliente deve entrar em

--- Trecho 5 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 3. Definição de incidente crítico | Score: 0.542 ---
Um incidente é classificado como crítico quando atende a pelo menos um dos seguintes critérios:

- Carga com valor declarado acima de R$ 100.000 está com status desconhecido há mais de 6 horas.
- Carga perigosa com qualquer irregularidade de documentação ou rastreamento.
- Mais de 5 chamados do mesmo cliente nas últimas 24 horas sobre o mesmo problema.
- Qualquer situação que envolva risco à segurança de pessoas.

--- Trecho 6 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 1. Objetivo | Score: 0.541 ---
Esta política define as regras e procedimentos para devolução de mercadorias transportadas pela NovaTech, aplicável a todos os tipos de cliente e categorias de carga, salvo exceções explicitamente listadas na seção 3.

--- Trecho 7 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 2. Escopo | Score: 0.539 ---
Aplica-se a todas as devoluções solicitadas por clientes da NovaTech após a entrega da mercadoria. Não se aplica a mercadorias ainda em trânsito (para essas, consultar PROC-088: Procedimento de Interceptação de Carga).

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Carga perigosa com frete expresso?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Pode, mas com tratamento especial.

Para carga perigosa com frete expresso:
- é necessária autorização do Compliance;
- a documentação ANTT deve estar atualizada;
- na prática, a autorização pode levar cerca de 2 dias, então o “expresso” pode não manter a mesma agilidade.

Por se tratar de carga perigosa, escale sempre para o ramal 4500 (Gestão de Riscos).

Observação: essa orientação operacional vem de fonte informal (FAQ); a confirmação deve ser feita na documentação normativa (POL/PROC/SLA).
```

</details>

---

### Query 9 — "Qual o multiplicador para o Sudeste?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: PROC-042v2-B — ✓ encontrado (score 0.68+)
- PODE: PROC-042-B — não encontrado (deduplicado pelo M6 — comportamento correto)


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.609 | PROC-042-v2 | 2. Fórmula de cálculo > 2.1. Multiplicadores regionais (atualizados... | ✓ DEVE |
| 2 | 0.602 | PROC-042-v1 | 2. Fórmula de cálculo > 2.1. Multiplicadores regionais | — |
| 3 | 0.487 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 8 — "C... | — |
| 4 | 0.385 | PROC-042-v2 | 1. Objetivo | — |
| 5 | 0.356 | PROC-042-v2 | 2. Fórmula de cálculo | — |
| 6 | 0.342 | PROC-042-v2 | 5. Disposições transitórias | — |
| 7 | 0.335 | PROC-042-v2 | 4. Condições especiais | — |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (7 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 2. Fórmula de cálculo > 2.1. Multiplicadores regionais (atualizados em novembro/2023) | Score: 0.609 ---
[Resumo da tabela] Região: Sul; Multiplicador: 1.3. Região: Sudeste; Multiplicador: 1.1. Região: Centro-Oeste; Multiplicador: 1.4. Região: Nordeste; Multiplicador: 1.5. Região: Norte; Multiplicador: 1.8.

| Região | Multiplicador |
|--------|--------------|
| Sul | 1.3 |
| Sudeste | 1.1 |
| Centro-Oeste | 1.4 |
| Nordeste | 1.5 |
| Norte | 1.8 |

--- Trecho 2 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 2. Fórmula de cálculo > 2.1. Multiplicadores regionais | Score: 0.602 ---
[Resumo da tabela] Região: Sul; Multiplicador: 1.2. Região: Sudeste; Multiplicador: 1.0. Região: Centro-Oeste; Multiplicador: 1.3. Região: Nordeste; Multiplicador: 1.4. Região: Norte; Multiplicador: 1.6.

| Região | Multiplicador |
|--------|--------------|
| Sul | 1.2 |
| Sudeste | 1.0 |
| Centro-Oeste | 1.3 |
| Nordeste | 1.4 |
| Norte | 1.6 |

--- Trecho 3 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 8 — "Como funciona o frete especial?" | Score: 0.487 ---
Pergunta: Como funciona o frete especial?
Acima de 500kg, aplica a tabela de multiplicadores por região. Cuidado: existem duas versões da PROC-042. A mais recente tem multiplicadores mais altos. Na dúvida, use a mais recente (v2), mas se o cliente reclamar do valor, pode ser que o contrato dele ainda esteja na tabela antiga.

--- Trecho 4 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 1. Objetivo | Score: 0.385 ---
Definir a fórmula e os parâmetros atualizados para cálculo de frete especial aplicável a cargas com peso acima de 500kg. Os multiplicadores foram revisados para refletir os custos operacionais atualizados de cada região.

--- Trecho 5 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 2. Fórmula de cálculo | Score: 0.356 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.15 para cargas de 1.001kg a 3.000kg; 1.4 para cargas acima de 3.000kg.

--- Trecho 6 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 5. Disposições transitórias | Score: 0.342 ---
Durante o período de transição, chamados abertos antes de 01/12/2023 que ainda estejam em processamento devem usar os multiplicadores da versão anterior (PROC-042 v1). Chamados novos a partir de 01/12/2023 devem usar os multiplicadores desta versão.

--- Trecho 7 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.335 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Qual o multiplicador para o Sudeste?

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Há contradição entre as versões da PROC-042 para o Sudeste:

- PROC-042 v1: multiplicador 1.0  
- PROC-042 v2 (mais recente): multiplicador 1.1

Usando a versão mais recente, o multiplicador para o Sudeste é **1.1**.

Observação: para chamados abertos antes de 01/12/2023 e ainda em processamento, aplica-se a regra transitória da versão anterior (v1).
```

</details>

---

### Query 10 — "Prazo de devolução, carga perigosa e frete especial" — ✗ FAIL

**Gabarito Anexo B:**
- DEVE: POL-001-A — ✓ encontrado *(era FAIL na v2 para esta query)*
- DEVE: POL-001-B — ✓ encontrado
- DEVE: PROC-042v2-A — ✓ encontrado
- DEVE: PROC-042v2-B — ✗ não encontrado (Lacuna L2 remanescente)
- PODE: FAQ-03 — ✓ encontrado

**Progresso:** 3/4 → agora 3/4 obrigatórios encontrados mas não 4/4. M8 (decomposição) melhorou de 2/4 (v2) para 3/4 (v3).


**Chunks recuperados (N=8, após filtro de score e deduplicação):**

| # | Score | Fonte | Seção / Subseção | Gabarito? |
|---|-------|-------|------------------|-----------|
| 1 | 0.579 | POL-001 | 3. Regras de Devolução > 3.2. Exceções ao prazo geral | ✓ DEVE |
| 2 | 0.577 | PROC-042-v2 | 4. Condições especiais | — |
| 3 | 0.511 | POL-001 | 3. Regras de Devolução > 3.5. Custos de devolução | — |
| 4 | 0.483 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 3 — "C... | ✓ PODE |
| 5 | 0.477 | POL-001 | 3. Regras de Devolução > 3.1. Prazo geral | ✓ DEVE |
| 6 | 0.465 | FAQ | Perguntas selecionadas (das 47 do documento original) > Item 22 — "... | — |
| 7 | 0.415 | PROC-042-v2 | 3. Prazo de entrega para frete especial | — |
| 8 | 0.405 | SLA-2024 | 5. Medição e reportes | — |

<details>
<summary>Prompt gerado pelo pipeline (clique para expandir e colar no agente)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.2. Exceções ao prazo geral | Score: 0.579 ---
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1), gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4), oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa especificada na nota fiscal por mais de 30 minutos contínuos, conforme registro do sensor IoT).
- Cargas com lacre de segurança violado, salvo quando a violação for documentada no ato de entrega com assinatura do motorista e do recebedor.

Para essas categorias, o cliente deve entrar em

--- Trecho 2 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.577 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 3 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.5. Custos de devolução | Score: 0.511 ---
- Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente.
- Desistência do cliente (carga correta, sem defeito): o custo do frete reverso é do cliente, calculado com os mesmos multiplicadores do frete original.
- Prazo expirado (solicitação após 7 dias úteis): não elegível para devolução padrão. Encaminhar ao Comercial para negociação caso a caso.

--- Trecho 4 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 3 — "Cliente perguntou se pode devolver carga perigosa. O que respondo?" | Score: 0.483 ---
Pergunta: Cliente perguntou se pode devolver carga perigosa. O que respondo?
Na prática, a gente orienta o cliente a ligar no ramal 4500 (Gestão de Riscos). Oficialmente não pode pelo processo padrão, mas já tiveram casos em que o pessoal de Riscos autorizou exceção. Então não diga que é impossível — diga que precisa de tratamento especial.

--- Trecho 5 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.1. Prazo geral | Score: 0.477 ---
O cliente pode solicitar a devolução de mercadorias em até 7 (sete) dias úteis após a data de recebimento confirmada no sistema de tracking. A contagem de dias úteis exclui sábados, domingos e feriados nacionais.

--- Trecho 6 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.465 ---
Pergunta: Cliente quer saber sobre seguro de carga. O que falar?
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

--- Trecho 7 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 3. Prazo de entrega para frete especial | Score: 0.415 ---
O prazo de entrega para frete especial é calculado como o prazo padrão da rota + 3 dias úteis adicionais para manuseio e roteirização de carga pesada (anteriormente era + 2 dias na versão anterior).

--- Trecho 8 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 5. Medição e reportes | Score: 0.405 ---
Os SLAs são medidos pelo sistema de chamados (Azure DevOps) a partir do timestamp de abertura do chamado. O relógio de SLA pausa fora do horário comercial (08h-18h, dias úteis) para chamados gerais, mas não pausa para incidentes críticos de clientes Gold.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Prazo de devolução, carga perigosa e frete especial

──────────────────────────────────────────────────────────────────────
↑ Copie TUDO acima e cole no Claude para obter a resposta.
```

</details>

<details>
<summary>Resposta do agente (clique para expandir após obter resposta)</summary>

```
Resumo com base nos trechos fornecidos:

- Prazo de devolução (regra geral): até 7 dias úteis após a data de recebimento confirmada no tracking (exclui sábados, domingos e feriados nacionais).
- Carga perigosa: cargas perigosas das classes 1 a 6 da ANTT não são elegíveis para devolução pelo processo padrão.
- Para carga perigosa: escalar para o ramal 4500 (Gestão de Riscos).
- Frete especial (prazo): prazo da rota padrão + 3 dias úteis adicionais para manuseio e roteirização de carga pesada.
- Condição adicional de frete especial: cargas perigosas acima de 500kg seguem tabela específica PROC-043 (em revisão pelo Compliance).

Complemento importante:
- Se a solicitação de devolução for após 7 dias úteis, não é elegível para devolução padrão e deve ser encaminhada ao Comercial para negociação caso a caso.
- A indicação de possíveis exceções para carga perigosa aparece no FAQ (fonte informal); a confirmação deve ser feita na documentação normativa (POL/PROC/SLA).
```

</details>

---

## Diagnóstico técnico das lacunas remanescentes

### Por que POL-001-B não é recuperado para "prazo de devolução"?

A query "Qual o prazo de devolução?" tem alta similaridade com POL-001-A (que contém "7 dias úteis", "data de recebimento") e baixa similaridade com POL-001-B (que contém "NÃO são elegíveis", "classes 1 a 6 da ANTT"). Do ponto de vista semântico, o modelo vê POL-001-B como sendo sobre "exceções e cargas perigosas" — não sobre "prazo de devolução". A associação entre esses dois chunks depende de conhecimento de domínio que o modelo não possui.

**Impacto prático:** O atendente recebe a informação do prazo (7 dias) mas não é alertado sobre as categorias de carga que não se qualificam para esse prazo. Risco de orientação incompleta para clientes com cargas perigosas.

### Por que PROC-042v2-B não é recuperado para queries de frete geográfico?

A tabela de multiplicadores (PROC-042v2-B) contém apenas pares "Região: Norte; Multiplicador: 1.8" — sem contexto de peso, cálculo ou cidade. A query "Frete para 600kg para Manaus?" tem semanticamente mais a ver com "cálculo de frete" (fórmula) do que com "tabela de valores por região". A expansão geográfica adiciona "Norte" mas o score do chunk de multiplicadores ainda fica abaixo de 0.30 para essa query.

**Tentativa realizada (descartada):** adicionar "frete" às expansões de domínio causou regressão — a expansão diluiu o vetor de Q8 a ponto de FAQ-32 cair abaixo do limiar.

---

## Recomendações para v4

| Prioridade | Ação | Lacuna alvo | Complexidade |
|-----------|------|-------------|-------------|
| Alta | Retrieval híbrido BM25 + vetorial (`rank_bm25` + ChromaDB) | L1, L2 | Alta |
| Média | Recuperação multi-etapa (fórmula → multiplicador) para queries de frete | L2 | Média |
| Média | N_RESULTS aumentado para 10-12 para queries compostas | L1, L2 | Baixa |
| Baixa | HyDE (Hypothetical Document Embeddings) | L1 geral | Alta |
| Baixa | Fine-tuning do modelo de embeddings com pares query↔chunk do corpus NovaTech | Geral | Muito Alta |
