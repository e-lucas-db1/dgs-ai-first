# Análise Técnica: Viabilidade de Assistente RAG para a NovaTech

**Arquitetura de Retrieval-Augmented Generation com Gerenciamento de Context Window**
**Versão 4** — incorpora (1) recalibração da estimativa de tokens por perfil de página de documento logístico, (2) dimensionamento adaptativo de chunks por tipo de intenção de query, e (3) análise de viabilidade do pipeline de ingestão com estimativas de custo e cronograma

---

## 1. Desafios por Tipo de Fonte

### 1.1 PDFs com Tabelas Complexas (15+ colunas)

**Desafio no pipeline RAG**

Tabelas são estruturas bidimensionais cujo significado emerge da relação entre cabeçalhos de linha, cabeçalhos de coluna e célula. Ao serializar para texto linear, essa estrutura colapsa. Um chunker por tamanho fixo pode cortar a tabela ao meio, separando cabeçalho de dados.

**Caso concreto identificado no corpus da NovaTech**

A documentação real confirma esse risco com precisão: PROC-042 v1 e PROC-042-v2 contêm tabelas de multiplicadores regionais com a mesma estrutura (5 regiões × 1 coluna de multiplicador), mas valores distintos — e ambos os documentos coexistem no SharePoint sem indicação de qual é o vigente. Sem chunking table-aware e sem metadado de versão, o retriever retornará chunks de ambas as versões para qualquer pergunta sobre frete especial. O modelo receberá Sul=1,2 (v1) e Sul=1,3 (v2) no mesmo contexto e não terá base para escolher — ou mesclará os dois valores em uma resposta aparentemente coerente mas incorreta.

**Como degrada a qualidade das respostas**

Além do problema genérico de serialização, o corpus da NovaTech tem um padrão documentado de versões concorrentes sem hierarquia clara. Isso significa que a degradação não é acidental — é estrutural: sempre que uma tabela for atualizada em um novo documento sem arquivar o anterior, o problema se reproduz.

**Estratégia de tratamento recomendada**

1. **Extração estruturada com preservação de versão:** preservar estrutura tabular (bounding boxes) E anotar cada chunk de tabela com metadados `doc_id`, `doc_version`, `doc_date`, e `doc_status` (`vigente` / `histórico` / `indefinido`)
2. **Versionamento explícito obrigatório:** para o caso específico PROC-042, ambas as versões devem ser indexadas com status `indefinido` até que a NovaTech formalize qual é a vigente; o system prompt deve instruir o modelo a apresentar ambas e explicitar a ambiguidade
3. **Serialização orientada a semântica:** converter tabelas para Markdown tabular completo, com cabeçalhos repetidos em cada partição se a tabela exceder o limite de chunk
4. **Chunking table-aware:** tratar cada tabela como unidade atômica; se exceder 800 tokens, particionar por grupos de linhas semanticamente coerentes com cabeçalho repetido — nunca cortar entre cabeçalho e dados
5. **Metadata enriquecido:** indexar junto ao chunk: título da seção, número da página, nome do documento, tipo de chunk (`table` vs `text`) — permite filtros pré-retrieval

---

### 1.2 PDFs Escaneados (OCR necessário)

**Desafio no pipeline RAG**

PDFs escaneados são imagens de texto. O pipeline precisa de uma camada OCR antes de qualquer processamento, e OCR introduz ruído proporcional à qualidade da digitalização. Documentos com fontes incomuns, texto inclinado ou baixa resolução produzem erros que corrompem os embeddings vetoriais — falha de recall silenciosa, não erro explícito.

**Resolução do pressuposto pendente da v2 (Assunção 1)**

A v2 assumia que documentos escaneados seriam minoria dos 800 PDFs, sem evidência direta. O exercício de desenvolvimento (exercicio-fase-1-entendimento.md) descreve a base como: *"PDFs do SharePoint incluem documentos com tabelas complexas, fluxogramas embutidos como imagens, e **alguns** documentos escaneados (OCR necessário)."* A palavra "alguns" confirma que escaneados são um subconjunto minoritário, não o conjunto dominante. **O pressuposto é confirmado direcionalmente**, mas a proporção exata requer levantamento na fase de discovery — o impacto no pipeline OCR é proporcional a essa contagem.

**Estratégia de tratamento recomendada**

1. **Levantamento obrigatório no discovery:** quantificar exatamente quantos dos 800 PDFs são escaneados antes de dimensionar o esforço OCR; a proporção afeta diretamente o cronograma e o custo do pré-processamento
2. **Auditoria de calibração antes da escala:** amostrar 20-30 páginas de diferentes origens para calibrar o threshold de confiança ao domínio da NovaTech — terminologia logística específica (CT-e, ANTT, classes de carga) terá taxa de reconhecimento diferente de texto genérico
3. **Pipeline OCR com pós-processamento:** correção ortográfica contextual com dicionário especializado no domínio
4. **Segmentação de qualidade:** páginas abaixo do threshold recebem metadata `ocr_quality: low` e penalidade no reranking
5. **Chunking conservador para baixa qualidade:** chunks de 200-300 tokens reduzem o raio de impacto de erros de OCR; chunks maiores com texto corrompido contaminam mais contexto

---

### 1.3 Wiki Confluence com Links Internos e Macros

**Desafio no pipeline RAG**

Links internos criam grafos de dependência implícita: uma página semanticamente incompleta sem o conteúdo da referência que cita. Macros customizadas do Confluence frequentemente não se renderizam em exportações estáticas — produzindo artefatos XML visíveis no corpus.

**Resolução do pressuposto pendente da v2 (Assunção 2) — pressuposto violado pelo corpus real**

A v2 assumia que links internos do Confluence apontariam majoritariamente para páginas dentro do espaço exportado. A análise da documentação real invalida esse pressuposto com evidências diretas:

- **POL-001, seção 2:** *"Não se aplica a mercadorias em trânsito (para essas, consultar PROC-088: Procedimento de Interceptação de Carga)."* — PROC-088 não existe na base de documentos indexada.
- **PROC-042 v1 e v2, seção 4:** *"Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas)."* — PROC-043 não existe na base. A v2 acrescenta: *"a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações."*

**O problema das referências mortas não é hipotético — já está presente no corpus atual.** Em ambos os casos, o modelo receberá chunks que mencionam explicitamente outros documentos que não foram indexados. Sem tratamento, o modelo tentará responder perguntas sobre carga perigosa ou interceptação de carga com base apenas nas referências, sem o conteúdo real — risco de alucinação ou de resposta incompleta apresentada com confiança.

**Adicionalmente: o FAQ como fonte de conhecimento informal**

O FAQ-Atendimento coexiste com documentos formais no mesmo espaço. Seu cabeçalho é explícito: *"documento informal — NÃO validado por Compliance ou Operações. Representa o conhecimento prático do time, mas pode conter informações desatualizadas ou imprecisas."* Se indexado sem distinção de tipo, chunks do FAQ concorrerão com chunks de POL e PROC no mesmo retrieval — e o modelo não terá como diferenciar uma política normativa de um conselho informal de atendente.

**Estratégia de tratamento recomendada**

1. **Mapeamento de permissões como pré-requisito:** antes de qualquer exportação, mapear permissões de acesso para evitar que macros condicionais incluam no índice conteúdo restrito
2. **Inventário de referências externas:** durante a ingestão, identificar todas as referências a documentos (PROC-NNN, POL-NNN) e verificar se existem na base; referências a documentos ausentes devem ser marcadas com metadata `reference_target: absent` — permitindo que o modelo responda: *"este procedimento menciona PROC-088, mas esse documento não está disponível na base"*
3. **Tratamento explícito de PROC-043 e PROC-088:** os dois documentos ausentes mais críticos devem ser escalados para a NovaTech como gap prioritário; até que sejam fornecidos, o sistema deve responder com incerteza explícita para perguntas sobre carga perigosa acima de 500kg e interceptação de carga
4. **Tiering de fontes no índice:** indexar documentos com metadata `source_tier`:
   - `formal_normative`: POL, PROC com versão controlada e responsável definido
   - `formal_contractual`: SLA com responsável e classificação contratual
   - `informal_operational`: FAQ, documentos sem responsável formal
   O reranker deve aplicar boost para `formal` e penalidade para `informal` em perguntas sobre prazos, valores e regras
5. **Resolução de links em tempo de indexação:** expandir referências de primeiro nível quando o documento referenciado existe na base; quando ausente, incluir a referência como metadata e não como conteúdo
6. **Chunking por seção lógica:** respeitar hierarquia H1 > H2 > H3, com breadcrumb hierárquico como prefixo de cada chunk

---

### 1.4 Planilhas com Fórmulas Interdependentes

**Desafio no pipeline RAG**

Planilhas têm conteúdo computado, não estático. Uma célula com valor `R$847.000` pode ser resultado de `=SOMA(Custos!B2:B47)*Parâmetros!D3`. O valor sem a fórmula e sem os dados de origem é informação incompleta. Interdependências entre abas multiplicam esse problema.

**Resolução do pressuposto pendente da v2 (Assunção 3) — pressuposto complicado pelo corpus real**

A v2 assumia que as 50 planilhas teriam usuários ou responsáveis capazes de produzir a documentação descritiva necessária para o Regime D. A análise da documentação real revela uma complicação estrutural:

**A planilha mais crítica para o caso de uso principal está fora do escopo de indexação padrão.** Ambas as versões do PROC-042 referenciam o valor base do cálculo de frete como: *"tarifa publicada na tabela mensal de fretes (disponível em `\\novatech-fs\comercial\tabelas\frete-base-AAAAMM.xlsx`)"*. Esse arquivo está em uma **pasta de rede** (`\\novatech-fs\`), não no SharePoint nem no Confluence. O pipeline de ingestão padrão (via conector SharePoint) não alcança esse caminho de rede.

**Implicação prática direta:** o assistente poderá responder *"qual é a fórmula do frete especial?"* com precisão (a fórmula está nos documentos indexados). Mas não poderá responder *"quanto custa frete de 600kg para Manaus?"* — porque o valor base (`frete-base-AAAAMM.xlsx`), que varia mensalmente, não está acessível. A pergunta mais frequente dos atendentes (calcular valor de frete) requer exatamente o dado que o sistema não consegue indexar pelo caminho padrão.

O responsável Comercial existe e atualiza as planilhas mensalmente — mas a **localização** das atualizações (pasta de rede, não SharePoint) significa que o pipeline não as vê automaticamente.

**Estratégia de tratamento recomendada**

1. **Decisão de escopo obrigatória no discovery:** definir se a pasta de rede `\\novatech-fs\comercial\tabelas\` será incluída no pipeline de ingestão; isso requer conector adicional ou processo de publicação que mova o arquivo para o SharePoint após cada atualização mensal
2. **Se a planilha mensal for indexável:** tratar como Regime D — documentar o schema (colunas, regiões, unidades), indexar como CSV anotado, e marcar explicitamente com `indexed_date` para que o modelo informe ao usuário a data do valor base utilizado
3. **Se a planilha mensal não for indexável:** o assistente deve ter uma resposta padrão para perguntas de cálculo de valor: *"posso informar a fórmula e os multiplicadores regionais, mas o valor base atualizado está em uma planilha que não está na minha base de conhecimento — consulte `\\novatech-fs\comercial\tabelas\frete-base-AAAAMM.xlsx`"*
4. **Auditoria de complexidade das 50 planilhas:** classificar por complexidade de dependência; planilhas com fórmulas interdependentes entre múltiplas abas requerem documentação 3-4× mais granular
5. **SLA de dados explícito:** toda resposta baseada em planilha deve incluir a data de indexação — resposta correta com dado desatualizado é funcionalmente uma resposta errada
6. **Re-indexação periódica:** definir cadência de re-indexação alinhada com o ciclo de atualização mensal do Comercial, com processo formal de notificação quando planilha for atualizada

---

## 2. Estimativa de Tamanho da Base em Tokens

*(Revisado na v4 — reclassificação por perfil de conteúdo corrige subestimação estrutural do custo de serialização de tabelas logísticas.)*

### 2.1 Por que a estimativa anterior subestimava o corpus

As versões v2 e v3 modelavam o corpus em dois perfis — texto puro e páginas com tabelas — usando um overhead fixo de 500 tokens por página de tabela. Para documentos logísticos com tabelas de 15+ colunas, esse overhead é 5× insuficiente.

Uma tabela típica no corpus NovaTech (multiplicadores regionais de PROC-042, com 5 regiões × faixas de peso × prazo) serializada em Markdown:

```
| Região     | Mult. base | Fator 0-500kg | Fator 501-1.000kg | Fator 1.001-3.000kg | Fator >3.000kg | Prazo adicional |
|------------|------------|---------------|-------------------|---------------------|----------------|-----------------|
| Sul        | 1,3        | 1,0           | 1,05              | 1,15                | 1,4            | +3 dias úteis   |
| Sudeste    | 1,1        | ...
| (5 linhas de dados)
```

Contagem de tokens para essa tabela (15 colunas × 20 linhas):

```
Header:    15 colunas × ~6 tokens/nome de coluna  =   90 tokens
Separador: 15 × "---"                              =   30 tokens
Dados:     20 linhas × 15 células × ~3,5 tok/cel  = 1.050 tokens
────────────────────────────────────────────────────────────────
Por tabela:                                        ~1.170 tokens

Página com 2 tabelas:  2 × 1.170 = 2.340 tokens só em tabelas
Prosa da página:                  +  262 tokens
Total por página table-heavy:     ~2.600 tokens
```

O modelo anterior alocava ~500 tokens para toda a página — 5,2× abaixo da serialização real. Para 2.000 páginas com tabelas, a diferença é de ~1M tokens estimados para ~5,2M tokens reais.

Adicionalmente, documentos logísticos contêm um terceiro perfil ausente nas versões anteriores: **formulários estruturados** (CT-e, romaneios, manifestos de carga). Esses documentos são saturados de campos label:valor e identificadores alfanuméricos (RNTRC, CNPJ, placa) que tokenizam como múltiplos tokens por código — diferente de texto narrativo com palavras convencionais.

### 2.2 Reclassificação por perfil de conteúdo

| Perfil | Exemplos NovaTech | % estimada | Tokens/página |
|--------|------------------|------------|---------------|
| **Texto narrativo** | Seções de política em POL-001, introduções de PROC, wiki | 50% (4.000 pág.) | 262 tokens (350 × 0,75) |
| **Tabela complexa** | Multiplicadores regionais PROC-042, tabela de tiers SLA-2024 | 25% (2.000 pág.) | ~2.800 tokens (prosa + 2 tabelas 15 colunas × 20 linhas) |
| **Formulário/estruturado** | Manifestos de carga, CT-e, romaneios, listas de embarque | 25% (2.000 pág.) | ~900 tokens (50 campos × label + valor + formatação estrutural) |

### 2.3 Cálculo por componente

**PDFs — estimativa v4:**

```
Texto narrativo:   4.000 páginas × 262 tokens    = 1.048.000 tokens
Tabela complexa:   2.000 páginas × 2.800 tokens  = 5.600.000 tokens
Formulário:        2.000 páginas × 900 tokens    = 1.800.000 tokens
──────────────────────────────────────────────────────────────────
Total PDFs:                                        8.448.000 tokens
```

**Wiki Confluence e planilhas (mantidos da v2/v3):**

```
Wiki Confluence:   400 páginas × 1.125 tokens  =   450.000 tokens
Planilhas:                                     =   112.500 tokens
```

### 2.4 Consolidação

| Componente | Tokens estimados | Percentual |
|---|---|---|
| PDFs (800 documentos) | 8.448.000 | 93,8% |
| Wiki Confluence (400 páginas) | 450.000 | 5,0% |
| Planilhas (50 arquivos) | 112.500 | 1,2% |
| **Total** | **~9.010.500** | **100%** |

**Nota v4:** O total sobe de ~3,66M (v2/v3) para ~9,01M tokens — aumento de 2,46×. A divergência vem quase inteiramente do componente de tabelas: o overhead real de serialização Markdown para tabelas com 15+ colunas é ~5× maior do que o estimado pela v2. O modelo de texto narrativo (262 tokens/página) permanece inalterado; o ajuste é metodológico. Os valores reais devem ser calibrados após amostragem do corpus durante o discovery (seção 7.9).

---

## 3. Análise de Orçamento de Contexto

*(Espaço disponível por query mantido da v3. O tamanho revisado do corpus altera a cobertura efetiva por query.)*

### 3.1 Cálculo do espaço disponível

```
Janela total:           128.000 tokens
(-) System prompt:       -1.000 tokens
(-) Margem de resposta:  -8.000 tokens
────────────────────────────────────────
Contexto disponível:    119.000 tokens
```

### 3.2 Capacidade de chunks por query

```
Espaço disponível:  119.000 tokens  ÷  500 tokens/chunk  =  ~238 chunks (máximo teórico)
```

### 3.3 Cobertura efetiva da base

```
Total da base:  ~9.010.500 tokens  →  ~18.021 chunks

Cobertura por query (máximo teórico):  238 / 18.021  =  ~1,32%
```

**Implicação crítica atualizada:** a cobertura por query cai de 3,25% (v3) para 1,32% na estimativa calibrada. A cada pergunta, mesmo preenchendo todo o contexto disponível, apenas ~1,32% da base está acessível. Isso reforça que a precisão do retriever é o determinante de qualidade — não a quantidade de chunks. Um retriever que seleciona os 10 chunks corretos de 18.021 entrega mais valor do que um que preenche 238 slots com chunks mediocres.

Com documentos contraditórios indexados (PROC-042 v1 e v2), parte dos 238 slots será consumida por chunks que se contradizem — reduzindo ainda mais o espaço para informação útil e não conflitante. Este é o argumento técnico central para o dimensionamento adaptativo de chunks por intenção (seção 4.3).

### 3.4 Impacto do histórico de conversa

Em diálogos de múltiplos turnos, 5+ trocas consomem 15-20K tokens de histórico, reduzindo o espaço disponível para chunks de 119K para ~100K (~200 chunks). Estratégias de compressão ou sumarização do histórico são necessárias para sessões longas no Teams.

---

## 4. Estratégia de Chunking Justificada

### 4.1 Classificação de intenção pré-retrieval

A etapa de classificação de intenção determina tanto a estratégia de retrieval quanto o orçamento de chunks a compor o contexto efetivo da resposta:

| Tipo de pergunta | Sinal de identificação | Estratégia | Chunks-alvo |
|---|---|---|---|
| **Factual simples** | Quem, quando, qual valor específico | Pipeline padrão, top por relevância | 5 |
| **Policy check** | "posso", "é permitido", "se aplica a" | Retrieval restrito à política + contexto adjacente | 10 |
| **Multi-documento** | "comparar", "diferença entre", "relação entre X e Y" | Threshold mais alto, aviso sobre limitação | 25 |
| **Cálculo de frete** | Peso, região, valor | Retrieval restrito a PROC-042 + aviso se frete-base não disponível | 15 |
| **Exceção / cargas especiais** | "perigosa", "refrigerada", "lacre" | Priorizar POL-001 + escalar para Gestão de Riscos se PROC-043 ausente | 10 |
| **SLA / tier** | "Gold", "Silver", "Standard", "prazo" | Retrieval restrito a SLA-2024; rejeitar tier "Platinum" com citação explícita | 8 |
| **Gap de cobertura** | Score top-1 < 0,55 | Nenhum chunk — resposta de gap explícita | 0 |

### 4.2 Chunking diferenciado por tipo de conteúdo

**Regime A — Texto narrativo (wiki, PDFs sem tabelas):** chunks de 300-400 tokens com sobreposição de 50 tokens. Breadcrumb hierárquico como prefixo para wiki.

**Regime B — Tabelas (PDFs com tabelas complexas):** chunk atômico por tabela, até 800 tokens. Se exceder, particionar por grupos de linhas semanticamente coerentes com cabeçalho repetido. Nunca cortar entre cabeçalho e dados. **Para tabelas em documentos com versões conflitantes (PROC-042): cada versão de tabela como chunk separado, com metadado de versão obrigatório.**

**Regime C — Documentos escaneados (OCR):** chunks de 200-300 tokens. Metadata `ocr_confidence` para penalidade no reranking.

**Regime D — Planilhas:** chunkar por unidade semântica (aba, seção lógica), não por tamanho. Toda resposta baseada em planilha inclui `indexed_date`. Máximo 600 tokens por chunk.

**Regime E — Fontes informais (FAQ):** chunks de 200-300 tokens com metadata `source_tier: informal`. Nunca apresentados como resposta definitiva — sempre acompanhados de marcação de incerteza e referência ao documento formal correspondente quando existir.

**Regime F — Formulários/documentos estruturados (CT-e, manifestos, romaneios):** chunks por seção lógica do documento (cabeçalho identificador, remetente/destinatário, itens de carga, totais e assinaturas). Preservar estrutura campo:valor sem fragmentar grupos de campos relacionados. Máximo 400 tokens por chunk. Metadata `doc_type: operational_form` para priorização em perguntas operacionais e deprioritização em perguntas de política.

### 4.3 Orçamento de Chunks por Intenção

O segundo estágio do retrieval (reranking) não deve sempre selecionar 238 chunks. O número de chunks compondo o contexto efetivo deve ser determinado pela intenção classificada na seção 4.1:

```python
CHUNK_BUDGET = {
    "factual_simples":     5,
    "policy_check":       10,
    "calculo_frete":      15,
    "excecao_especial":   10,
    "sla_tier":            8,
    "multi_documento":    25,
    "conflito_versao":    20,
    "gap_cobertura":       0   # score top-1 < 0,55 → resposta de gap, sem chunks
}
```

**Impacto operacional — custo por query:**

```
Custo de input (Claude Sonnet, ~$3/1M tokens de entrada):
  238 chunks × 500 tokens = 119.000 tokens/query → $0,357/query
   15 chunks × 500 tokens =   7.500 tokens/query → $0,023/query

Para 320 queries/dia (volume NovaTech estimado):
  238 chunks fixos:  $0,357 × 320 = $114/dia  →  ~$3.420/mês
   15 chunks default: $0,023 × 320 =  $7/dia   →    ~$218/mês

Redução: ~16× no custo de entrada com melhoria de qualidade por
redução de ruído — sem trade-off de qualidade para a maioria das queries.
```

**Impacto de qualidade — efeito de diluição de atenção:**

Com 238 chunks (119K tokens de contexto), o modelo opera próximo ao limite da janela. Chunks posicionados nas posições intermediárias (50-200 de 238) têm probabilidade menor de influenciar a resposta do que chunks nas posições iniciais e finais — o efeito lost-in-the-middle opera mesmo com a estratégia de montagem da seção 4.6. Com 15 chunks (~7,5K tokens), o modelo opera em regime de alta densidade de sinal, sem diluição por ruído de chunks marginalmente relevantes.

O orçamento de 238 chunks deve ser reservado para queries explicitamente identificadas como síntese abrangente — não como padrão operacional.

### 4.4 Tratamento de conflito de versões no contexto

Quando o retriever retornar chunks de PROC-042 v1 e v2 simultaneamente (alta probabilidade para qualquer pergunta sobre frete especial), o sistema precisa de lógica explícita de disambiguação:

**Regra de transição já documentada em PROC-042-v2, seção 5:** *"Chamados novos a partir de 01/12/2023 devem usar os multiplicadores desta versão."* Essa regra deve ser extraída como instrução determinística no system prompt — não deixada para o modelo inferir.

```
Instrução no system prompt (exemplo):
"Para cálculo de frete especial, use SEMPRE os multiplicadores de PROC-042-v2
(emitido em 10/11/2023) para chamados abertos a partir de 01/12/2023.
Se ambas as versões aparecerem no contexto, aplique esta regra e informe
ao atendente que existe uma versão anterior com valores diferentes."
```

### 4.5 Tratamento de documentos ausentes referenciados

Quando o retriever retornar chunks que referenciam PROC-043 ou PROC-088 (documentos ausentes), o modelo deve ser instruído a reconhecer a lacuna explicitamente:

```
Instrução no system prompt (exemplo):
"Se a resposta exigir PROC-043 (Frete de Cargas Perigosas) ou PROC-088
(Interceptação de Carga), informe que esses documentos não estão disponíveis
na base e oriente o atendente a contatar o setor responsável."
```

### 4.6 Estratégia de montagem do contexto (mitigação do "lost in the middle")

```
[Posição 1-3]   → Chunks com score de relevância mais alto (crítico)
[Posição 4-N-3] → Chunks complementares, score decrescente
[Posição N-2-N] → Chunks de suporte com alto score
```

Para perguntas sobre frete especial, o chunk de PROC-042-v2 (versão vigente) deve ocupar a posição 1; o chunk de PROC-042-v1 (se recuperado) deve ser posicionado no meio com label explícito de "versão anterior".

### 4.7 Retrieval em dois estágios

**Estágio 1 — Recall amplo:** top-500 chunks por similaridade semântica.

**Estágio 2 — Reranking preciso:** reordenar os 500 por cross-encoder, aplicando:
- Boost para `source_tier: formal_normative` e `formal_contractual`
- Penalidade para `source_tier: informal_operational`
- Penalidade para `ocr_quality: low`
- Boost para `doc_status: vigente`; penalidade para `doc_status: indefinido`

Selecionar `CHUNK_BUDGET[intent]` chunks após o reranking (não 238 fixos).

### 4.8 Trade-offs explícitos

| Decisão | Vantagem | Desvantagem |
|---|---|---|
| Regime E para FAQ | Preserva conhecimento tácito com incerteza explícita | Atendente pode questionar por que o sistema não confia no FAQ |
| Regime F para formulários | Preserva estrutura campo:valor de documentos operacionais | Overhead de chunking adicional; documentos operacionais têm baixa frequência de acesso |
| Chunks de tabela como unidade atômica | Preserva relação cabeçalho-dado | Tabelas grandes (>800t) excedem o regime |
| Instrução de versão no system prompt | Determinístico; previne mistura de multiplicadores | Requer atualização manual quando NovaTech formalizar a versão vigente |
| Classificação de intenção pré-retrieval | Estratégia e orçamento adequados por tipo | Latência adicional antes do retrieval (~50-100ms); erro de classificação pode sub-servir multi-documento |
| CHUNK_BUDGET adaptativo | Redução de custo ~16× + melhoria de qualidade por foco | Requer classificador de intenção confiável |
| Metadata `indexed_date` em planilhas | Usuário ciente da defasagem | Requer lógica de exibição na interface |

---

## 5. Problemas Concretos Identificados no Corpus da NovaTech

*Esta seção documenta problemas específicos encontrados na documentação real (Anexo A). Cada problema é descrito com sua evidência, impacto para o RAG e tratamento recomendado.*

---

### 5.1 Conflito de versões ativo — PROC-042 v1 vs PROC-042-v2

**Evidência no corpus**

Ambos os documentos coexistem no SharePoint sem indicação formal de qual é o vigente. O Anexo A observa: *"Este documento não possui indicação formal de vigência ou obsolescência no sistema da NovaTech. Coexiste com a versão PROC-042-v2."*

**Contradições numéricas específicas entre as versões:**

| Parâmetro | PROC-042 v1 (mar/2023) | PROC-042-v2 (nov/2023) |
|---|---|---|
| Multiplicador Sul | 1,2 | 1,3 |
| Multiplicador Sudeste | 1,0 | 1,1 |
| Multiplicador Centro-Oeste | 1,3 | 1,4 |
| Multiplicador Nordeste | 1,4 | 1,5 |
| Multiplicador Norte | 1,6 | 1,8 |
| Fator peso 1.001-3.000kg | 1,2 | 1,15 |
| Fator peso >3.000kg | 1,5 | 1,4 |
| Prazo adicional | +2 dias úteis | +3 dias úteis |

**Impacto para o RAG**

Para qualquer pergunta sobre frete especial, o retriever provavelmente retornará chunks de ambas as versões. Sem instrução explícita de desambiguação, o modelo pode: (a) escolher arbitrariamente uma versão, (b) apresentar ambas sem indicar qual usar, ou (c) calcular com valores misturados. O FAQ-08 documenta que o próprio time de atendimento já convive com essa ambiguidade: *"existem duas versões da PROC-042. A mais recente tem multiplicadores mais altos."*

**Tratamento recomendado**

- Indexar ambas as versões com metadados `doc_version` e `doc_date`
- Aplicar a regra da seção 5 do PROC-042-v2 como instrução determinística no system prompt
- Escalar formalmente para a NovaTech a necessidade de arquivar o PROC-042-v1 — sem resolução no nível do dado, o system prompt é um workaround, não uma solução permanente

---

### 5.2 FAQ como única fonte para tópicos críticos

**Evidência no corpus**

O FAQ-Atendimento é explicitamente marcado como: *"documento informal — NÃO validado por Compliance ou Operações. Representa o conhecimento prático do time, mas pode conter informações desatualizadas ou imprecisas."*

Três tópicos críticos para o atendimento existem **apenas** no FAQ, sem documento formal correspondente:

| Tópico | Fonte disponível | Documento formal existente? |
|---|---|---|
| Carga danificada em trânsito | FAQ-38 | Não |
| Frete expresso para carga perigosa | FAQ-32 | Não |
| Seguro de carga (percentuais) | FAQ-22 | Não |

Para carga danificada, o FAQ orienta encaminhar ao e-mail `sinistros@novatech.com.br`, mas não existe PROC ou POL que descreva o processo formal.

**Adicionalmente:** o FAQ-45 cita o limiar de desconto de volume como "mais de 10 fretes/mês" — baseado no PROC-042-v1. O PROC-042-v2, publicado posteriormente, alterou esse limiar para 8 fretes/mês (5%) e 15 fretes/mês (10%). O FAQ não foi atualizado. Há três fontes com três valores diferentes para o mesmo parâmetro.

**Impacto para o RAG**

Se o FAQ for indexado sem distinção de tier, o modelo apresentará conhecimento tácito informal com o mesmo nível de confiança que uma política normativa. Para os três tópicos acima, isso é inevitável — são os únicos documentos disponíveis. Para o desconto de volume, o modelo pode retornar o valor desatualizado do FAQ em vez do valor correto do PROC-042-v2.

**Tratamento recomendado**

- Indexar FAQ com metadata `source_tier: informal_operational`
- Para os três tópicos sem cobertura formal, a resposta deve incluir marcação explícita de incerteza: *"esta informação está disponível apenas em um documento operacional informal, não validado pela área responsável"*
- Escalar para a NovaTech a necessidade de criar documentos formais para carga danificada, frete expresso e seguro de carga — esses gaps de documentação são riscos operacionais independentemente do RAG

---

### 5.3 Referências a documentos ausentes da base

**Evidência no corpus**

Dois documentos são referenciados explicitamente por múltiplos documentos da base, mas não estão disponíveis:

**PROC-043 (Frete de Cargas Perigosas):**
- Referenciado por PROC-042-v1, seção 4: *"Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043)"*
- Referenciado por PROC-042-v2, seção 4: *"PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações"*
- Ausente da base indexada

**PROC-088 (Interceptação de Carga):**
- Referenciado por POL-001, seção 2: *"mercadorias ainda em trânsito — para essas, consultar PROC-088"*
- Ausente da base indexada

**Impacto para o RAG**

Perguntas sobre cálculo de frete de carga perigosa pesada (>500kg) e sobre interceptação de carga em trânsito não têm resposta na base. O modelo receberá chunks que mencionam esses documentos sem ter acesso ao seu conteúdo. Os comportamentos possíveis — todos problemáticos:
- Alucinação do conteúdo do procedimento ausente
- Resposta parcial sem sinalizar que existe um documento específico não disponível
- Negativa correta ("não encontrei") sem indicar que o documento existe mas está ausente

**Tratamento recomendado**

- Registrar PROC-043 e PROC-088 como documentos ausentes com prioridade alta no levantamento de discovery
- Enquanto ausentes: adicionar entrada sintética no índice para cada um, contendo apenas: nome do documento, que ele existe, que não está na base, e o contato responsável
- O metadata `reference_target: absent` nos chunks que referenciam esses documentos permite ao retriever ativar uma instrução específica quando recuperá-los

---

### 5.4 Gaps de cobertura — perguntas sem resposta na base

**Evidência no corpus**

Além dos documentos ausentes, há tópicos que simplesmente não têm cobertura em nenhum documento da base:

| Tópico | Status | Impacto |
|---|---|---|
| Frete padrão (cargas <500kg) | Sem cobertura | Perguntas sobre fretes de menor volume não têm resposta |
| Processo formal de carga danificada | Só no FAQ informal | Respostas baseadas em fonte não validada |
| Política formal de seguro de carga | Só no FAQ informal | Percentuais informados sem garantia de precisão |
| Frete expresso para carga perigosa | Só no FAQ informal | Processo não formalizado apresentado como procedimento |
| Processo da Gestão de Riscos para devoluções excepcionais | Mencionado em POL-001 (ramal 4500) | O que acontece depois do encaminhamento é desconhecido |

**Impacto para o RAG**

O mapa de cobertura do Anexo B confirma: para a pergunta *"Frete para 300kg para Salvador?"*, a resposta correta é que não há documento na base — nenhum chunk relevante existe. Um sistema sem tratamento explícito de ausência de cobertura tentará responder com base em chunks parcialmente relacionados, gerando respostas incorretas com aparência de confiança.

**Tratamento recomendado**

- Configurar o sistema para reconhecer quando nenhum chunk recuperado tem relevância acima do threshold mínimo (score top-1 < 0,55) — e responder explicitamente com incerteza em vez de tentar uma resposta forçada
- Escalar os gaps de cobertura para a NovaTech como requisito de documentação a ser criada antes do go-live ou como limitação explícita do escopo inicial do assistente

---

### 5.5 Ausência de processo unificado de revisão documental

**Evidência no corpus**

O exercício descreve: *"A documentação é atualizada mensalmente por 3 áreas diferentes (Operações, Compliance, Comercial), sem processo unificado de revisão."* O Anexo A confirma com exemplos concretos: PROC-042-v2 foi publicada em novembro/2023 sem que PROC-042-v1 fosse arquivada. O FAQ nunca foi atualizado para refletir as mudanças do PROC-042-v2 (desconto de volume).

**Impacto estrutural para o RAG**

A ausência de processo de revisão não é um problema pontual — é o mecanismo pelo qual novos conflitos surgirão continuamente após o go-live. Mesmo que todos os problemas atuais sejam resolvidos na ingestão inicial, novas versões de documentos publicadas sem arquivar as anteriores reproduzirão o conflito PROC-042 em outros procedimentos.

**Tratamento recomendado**

- O pipeline de ingestão deve incluir detecção de conflito: quando um novo documento é indexado com o mesmo identificador (PROC-NNN) de um documento existente, deve acionar revisão humana antes de indexar — não sobrescrever automaticamente
- Propor à NovaTech, como parte das recomendações do discovery, um processo mínimo de governança documental: ao publicar nova versão, marcar a anterior como obsoleta no SharePoint com data de expiração
- O SLA de atualização da base (requisito de produto: máximo 24h após publicação) deve incluir etapa de validação de conflito, não apenas ingestão automática

---

## 6. Resolução dos Pressupostos Pendentes da v2

| Pressuposto | Status na v2 | Resolução na v3/v4 | Evidência |
|---|---|---|---|
| Documentos escaneados são minoria dos 800 PDFs | Não resolvido | **Confirmado direcionalmente** | exercicio-fase-1-entendimento.md: "alguns documentos escaneados" |
| Links internos do Confluence são majoritariamente dentro do espaço exportado | Não resolvido | **Violado com evidência concreta** | PROC-043 e PROC-088 referenciados por documentos da base, mas ausentes |
| Planilhas têm responsáveis que podem documentá-las | Não resolvido | **Complicado: responsável existe, mas localização é problema** | frete-base-AAAAMM.xlsx em pasta de rede (`\\novatech-fs\`), fora do SharePoint |

**Implicações para o projeto:**

- **Pressuposição 1 (OCR):** o risco OCR está confirmado como subconjunto — o esforço de calibração e auditoria é proporcional, não total. Levantamento no discovery definirá o escopo exato.

- **Pressuposição 2 (links):** a estratégia de expansão de links em tempo de indexação da v2 é necessária e insuficiente. O problema não é apenas links para páginas existentes — é referências a documentos que nunca foram indexados. A nova estratégia (seção 1.3, item 3) de indexar entradas sintéticas para documentos ausentes é a resposta a esse cenário.

- **Pressuposição 3 (planilhas):** o Regime D (documentação descritiva por planilha) é viável operacionalmente (o Comercial existe e tem o conhecimento), mas requer uma decisão de arquitetura sobre a pasta de rede. Sem essa decisão, o caso de uso central — atendente consultando valor de frete atual — não é atendível pelo assistente.

---

## 7. Viabilidade do Pipeline de Ingestão

*Esta seção documenta o custo, o cronograma e os critérios go/no-go do pipeline de ingestão inicial e da re-indexação periódica. Incorporada na v4 para completar a análise de viabilidade técnica.*

---

### 7.1 Classificação do corpus antes da ingestão

Antes de processar os 800 PDFs, uma etapa de classificação automatizada determina o perfil de cada documento:

| Categoria | Estimativa | Método de detecção | Pipeline aplicado |
|---|---|---|---|
| PDFs digitais/vetoriais | ~640 (80%) | Texto extraível nativo | PyMuPDF direto |
| PDFs escaneados | ~80 (10%) | Ausência de camada de texto | OCR obrigatório |
| PDFs mistos | ~80 (10%) | Texto parcial + imagens embutidas | Extração + OCR seletivo por página |

Tempo estimado de classificação automatizada: ~20 minutos.

---

### 7.2 Estágio 1 — Extração de texto

**PDFs digitais (640 × 10 = 6.400 páginas):**

```
Ferramenta local (PyMuPDF):
  ~150ms/página × 6.400 = 960s ≈ 16 minutos

Azure Document Intelligence (Layout API):
  ~$0,01/página × 6.400 = $64
  Vantagem: detecta estrutura de tabelas mais confiável que extração local
```

**PDFs mistos (80 × 10 = 800 páginas, ~50% com imagens embutidas):**

Processamento híbrido: páginas digitais seguem extração local; páginas com imagens escaneadas seguem o estágio de OCR abaixo.

---

### 7.3 Estágio 2 — OCR para documentos escaneados

**PDFs escaneados puros (800 páginas) + páginas mistas (~400 páginas) = ~1.200 páginas com OCR:**

```
Tesseract (self-hosted, CPU):
  ~3s/página × 1.200 = 3.600s ≈ 60 minutos
  Risco: accuracy não calibrada para terminologia logística (RNTRC, CT-e, DANFE)

Azure Document Intelligence (Read API):
  ~$0,001/página × 1.200 = $1,20
  Melhor accuracy em layouts mistos e fontes não-padrão
```

**Pré-requisito obrigatório de calibração:** antes do processamento em lote, amostrar 20-30 páginas representativas e validar accuracy em termos críticos do domínio (CT-e, RNTRC, ANTT, multiplicadores numéricos). Se accuracy < 92% em termos logísticos, adicionar pós-processamento com dicionário especializado antes da ingestão em escala. O custo de calibração (~2h de engenheiro) é negligenciável frente ao custo de reindexar 1.200 páginas com OCR de baixa qualidade.

---

### 7.4 Estágio 3 — Extração de tabelas

**2.000 páginas com tabelas complexas (25% do corpus):**

```
camelot-py (lattice mode, self-hosted):
  ~2s/página × 2.000 = 4.000s ≈ 67 minutos
  Limitação crítica: falha em tabelas sem bordas visíveis ou células mescladas

Azure Document Intelligence (Table API):
  ~$0,01/página × 2.000 = $20
  Suporta tabelas sem bordas, células mescladas, layouts de apresentação
```

**Validação manual obrigatória (estimativa: 3-4 horas de engenheiro):**

| Documento | O que validar | Motivo |
|---|---|---|
| PROC-042-v1 e v2 | Todos os 8 parâmetros conflitantes com valores corretos | Erro silencioso gera cálculos incorretos sem detectabilidade no retrieval |
| SLA-2024 | Estrutura de tiers (Gold, Silver, Standard) e valores de SLA | Base para respostas de prazo — erros afetam toda query de SLA |
| POL-001 | Tabelas de exceções e condições de devolução | Fonte para armadilha intencional do exercício 1.2 |

Essa validação não é opcional. Um erro silencioso na extração de multiplicadores de PROC-042 introduziria erros de cálculo não detectáveis no nível do retrieval ou do reranking.

---

### 7.5 Estágio 4 — Chunking e geração de embeddings

```
Corpus revisado: ~9.010.500 tokens → ~18.021 chunks de 500 tokens

Embeddings (cloud):
  OpenAI text-embedding-3-large ($0,13/1M):  9.010.500 × $0,13/1M = $1,17
  Azure OpenAI ada-002 ($0,10/1M):           9.010.500 × $0,10/1M = $0,90
  Tempo (batch API):  18.021 chunks ÷ ~500 chunks/min ≈ 36 minutos

Embeddings (self-hosted, e5-large ou all-mpnet-base-v2):
  GPU A10G (~$0,75/hora):  18.021 ÷ ~3.000 chunks/min = ~6 min → < $0,10
```

---

### 7.6 Estágio 5 — Construção do índice vetorial

```
18.021 vetores × 1.536 dimensões (ada-002) ou 768 (e5-large)

FAISS HNSW (self-hosted):   ~45 segundos
ChromaDB / Qdrant:          ~2-3 minutos
Azure AI Search:            ~10 minutos

Armazenamento: 18.021 × 1.536 floats × 4 bytes ≈ 110 MB
```

---

### 7.7 Consolidado do pipeline de ingestão inicial

| Estágio | Cenário cloud (Azure DI + OpenAI) | Cenário self-hosted GPU | Custo cloud |
|---|---|---|---|
| Classificação do corpus | ~20 min | ~20 min | — |
| Extração texto (digitais) | ~16 min | ~16 min | $64 |
| OCR (escaneados + mistos) | ~9 min (Azure DI) | ~60 min (CPU) | $1,20 |
| Extração de tabelas | ~15 min (paralelo) | ~67 min | $20 |
| Validação manual de tabelas críticas | 3–4h | 3–4h | — (eng.) |
| Chunking + embeddings | ~36 min | ~6 min (GPU) | $1,17 |
| Build do índice | ~10 min | ~3 min | — |
| **Total excl. validação manual** | **~1,5h (paralelizável)** | **~2,5h** | **~$87** |

O custo de ingestão inicial (~$87-100) não é um bloqueador para um projeto enterprise. O gargalo real é a **validação manual de tabelas críticas** — 3-4h de engenheiro que não podem ser automatizadas dado o impacto de erros silenciosos nos multiplicadores de PROC-042.

---

### 7.8 Re-indexação periódica (SLA de 24h)

NovaTech atualiza documentação mensalmente por 3 áreas. Estimativa de churn: ~40-60 documentos/mês.

```
40 PDFs × 10 páginas = 400 páginas/mês

Extração + OCR (proporcional):  ~$4 (Azure DI)
Embeddings:                     ~$0,05
Conflict detection:             +5 minutos ao pipeline

Tempo total de re-indexação:    ~25-30 minutos para 40 PDFs
Custo mensal (variável):        ~$4-6
```

**Atende o SLA de 24h com ampla folga.** O gargalo operacional é o processo de notificação e acionamento do pipeline após uma publicação, não o processamento em si.

**Requisito obrigatório no pipeline incremental:** antes de indexar qualquer documento novo, verificar se existe no índice um documento com o mesmo identificador (PROC-NNN, POL-NNN). Se existir, acionar revisão humana antes de prosseguir — não sobrescrever automaticamente. Essa verificação implementa a recomendação da seção 5.5 no nível do pipeline.

---

### 7.9 Critérios go/no-go e discovery de validação

Antes da ingestão em escala, três validações de discovery são obrigatórias:

| Validação | O que fazer | Custo/tempo | Critério de go |
|---|---|---|---|
| **OCR accuracy** | Amostrar 20-30 páginas de PDFs escaneados; validar reconhecimento de CT-e, RNTRC, multiplicadores numéricos | ~2h eng. + $0,03 API | Accuracy > 92% em termos críticos |
| **Table extraction** | Extrair PROC-042-v1, v2 e SLA-2024; comparar todos os valores com ground truth | ~2h eng. + $0,03 API | Zero erros em valores numéricos |
| **Conflict detection** | Executar detecção de PROC-NNN/POL-NNN duplicados no corpus completo | ~30 min automatizado | Mapa completo de conflitos antes da indexação em escala |

**Critério de no-go que bloqueia o projeto independentemente do resto:**

> A pasta de rede `\\novatech-fs\comercial\tabelas\frete-base-AAAAMM.xlsx` (valor base do cálculo de frete, atualizada mensalmente pelo Comercial) não está acessível pelo conector SharePoint padrão. Sem uma decisão arquitetural sobre como incluir esse arquivo no pipeline — por conector adicional de pasta de rede ou por processo de publicação manual para o SharePoint após cada atualização — o assistente não poderá responder à pergunta mais frequente dos atendentes: calcular o valor de frete para um embarque específico. Esse bloqueio é de acesso ao dado, não de qualidade do retrieval — não resolve com melhorias no pipeline de indexação ou na estratégia de chunking.

---

## 8. Registro de Alterações (v3 → v4)

### Adições e revisões por seção

| Seção | Alteração | Origem |
|---|---|---|
| **2 — Estimativa de tokens** | Reclassificação de dois perfis (texto/tabela) para três perfis (texto narrativo / tabela complexa / formulário estruturado). Revisão do overhead de tabela de 500t/página para ~2.800t/página para documentos com 15+ colunas. Total revisado: 3,66M → 9,01M tokens (+2,46×) | Análise de custo de serialização Markdown para tabelas logísticas com 15+ colunas |
| **3 — Orçamento de contexto** | Cobertura por query atualizada: 3,25% → 1,32% (reflexo do corpus revisado: 7.317 → 18.021 chunks totais) | Derivado da revisão da Seção 2 |
| **4.1 — Intenção** | Adicionada coluna "Chunks-alvo" com orçamento por tipo de query; adicionados tipos "policy_check" e "gap_cobertura" com threshold explícito (score top-1 < 0,55) | Análise de custo por query e impacto de diluição de atenção |
| **4.2 — Chunking** | Adicionado Regime F para formulários/documentos estruturados (CT-e, manifestos, romaneios) | Derivado do perfil "formulário" identificado na Seção 2 |
| **4.3 (nova) — Orçamento de chunks por intenção** | Nova seção com `CHUNK_BUDGET` explícito por intenção, análise de custo comparativa (238 vs 15 chunks: ~$3.420/mês vs ~$218/mês para 320 queries/dia), e análise do efeito de diluição de atenção | Análise de custo operacional e efeito lost-in-the-middle |
| **4.7 — Retrieval dois estágios** | Seleção final alterada para `CHUNK_BUDGET[intent]` em vez de 238 fixos | Derivado da Seção 4.3 |
| **4.8 — Trade-offs** | Adicionadas duas linhas: CHUNK_BUDGET adaptativo (com risco de classificador de intenção) e Regime F | Derivado das seções 4.3 e 4.2 |
| **Seção 7 (nova) — Pipeline de ingestão** | Nova seção completa: classificação do corpus (7.1), extração texto (7.2), OCR com critério de calibração (7.3), tabelas com validação manual obrigatória (7.4), embeddings (7.5), índice (7.6), custo consolidado (7.7), re-indexação periódica (7.8), critérios go/no-go e discovery (7.9) | Análise de viabilidade operacional do pipeline |

### O que não mudou

As seções 1 (Desafios por tipo de fonte), 5 (Problemas concretos no corpus) e 6 (Resolução de pressupostos) são mantidas integralmente da v3 — a análise do corpus NovaTech e os problemas identificados permanecem válidos. A estratégia de chunking diferenciado por regimes A-E é mantida; o Regime F foi adicionado sem alterar os outros. Os cálculos de espaço disponível por query (119K tokens, 238 chunks máximos teóricos) são mantidos da v2/v3.

---

*Documento produzido com base no cenário específico da NovaTech, nos documentos reais do Anexo A, e na análise de custo de serialização de tabelas logísticas. As estimativas de tokens são aproximações — valores reais devem ser calibrados após amostragem do corpus completo durante o discovery de validação descrito na seção 7.9. Os problemas documentados na seção 5 foram identificados na amostra de 5 documentos disponibilizada; o corpus de 800 PDFs provavelmente contém padrões semelhantes em escala.*
