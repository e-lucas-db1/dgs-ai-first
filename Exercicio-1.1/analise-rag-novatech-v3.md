# Análise Técnica: Viabilidade de Assistente RAG para a NovaTech

**Arquitetura de Retrieval-Augmented Generation com Gerenciamento de Context Window**
**Versão 3** — incorpora análise da documentação real da NovaTech (Anexo A) para resolver pressupostos pendentes da v2 e identificar problemas concretos no corpus existente

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

*(Cálculos mantidos da v2 — os documentos reais não alteram os volumes estimados, mas os problemas de qualidade descritos nas seções 1 e 5 afetam a eficiência do retrieval mesmo dentro desse volume.)*

### 2.1 Cálculo por componente

**PDFs — estimativa revisada (v2):**

```
Páginas de texto puro (75%):
  6.000 × 350 palavras × 0,75 = 1.572.000 tokens

Páginas com tabelas complexas (25%):
  Texto corrido:  2.000 × 350 palavras × 0,75 =   524.000 tokens
  Serialização de tabelas:
  2.000 × 500 tokens/tabela               =  1.000.000 tokens

Total PDFs revisado:                          3.096.000 tokens
```

**Wiki Confluence:**

```
400 páginas × 1.500 palavras × 0,75 = 450.000 tokens
```

**Planilhas — estimativa revisada (v2):**

```
25 planilhas simples:  25 × 1.500 palavras × 0,75 =  28.125 tokens
25 planilhas complexas: 25 × 4.500 palavras × 0,75 =  84.375 tokens
Total planilhas:                                       112.500 tokens
```

### 2.2 Consolidação

| Componente | Tokens estimados | Percentual |
|---|---|---|
| PDFs (800 documentos) | 3.096.000 | 84,6% |
| Wiki Confluence (400 páginas) | 450.000 | 12,3% |
| Planilhas (50 arquivos) | 112.500 | 3,1% |
| **Total** | **~3.658.500** | **100%** |

**Nota v3:** O volume total permanece o mesmo estimado na v2. O que muda é a avaliação de *qualidade efetiva* do corpus: documentos contraditórios, referências mortas e fontes informais não aumentam o volume, mas reduzem a fração do corpus que produz respostas confiáveis. A cobertura de 3,25% por query calculada na seção 3 é sobre o volume total — a cobertura efetiva de informação *confiável e não contraditória* é menor.

---

## 3. Análise de Orçamento de Contexto

*(Cálculos mantidos da v2.)*

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
Espaço disponível:  119.000 tokens  ÷  500 tokens/chunk  =  ~238 chunks
```

### 3.3 Cobertura efetiva da base

```
Total da base:  ~3.658.500 tokens  →  ~7.317 chunks

Cobertura por query:  238 / 7.317  =  ~3,25%
```

**Implicação crítica:** a cada pergunta, apenas ~3,25% da base está acessível. Com documentos contraditórios indexados (PROC-042 v1 e v2), parte desses 238 slots será consumida por chunks que se contradizem — reduzindo ainda mais o espaço para informação útil e não conflitante.

### 3.4 Impacto do histórico de conversa

Em diálogos de múltiplos turnos, 5+ trocas consomem 15-20K tokens de histórico, reduzindo o espaço disponível para chunks de 119K para ~100K (~200 chunks). Estratégias de compressão ou sumarização do histórico são necessárias para sessões longas no Teams.

---

## 4. Estratégia de Chunking Justificada

### 4.1 Classificação de intenção pré-retrieval

Antes do retrieval, uma etapa de classificação de intenção determina a estratégia a aplicar:

| Tipo de pergunta | Sinal de identificação | Estratégia |
|---|---|---|
| **Factual simples** | Quem, quando, qual valor específico | Pipeline padrão, top-238 por relevância |
| **Multi-documento** | "comparar", "diferença entre", "relação entre X e Y" | Threshold mais alto, aviso sobre limitação |
| **Cálculo de frete** | Peso, região, valor | Retrieval restrito a PROC-042 + aviso se frete-base não disponível |
| **Exceção / cargas especiais** | "perigosa", "refrigerada", "lacre" | Priorizar POL-001 + escalar para Gestão de Riscos se PROC-043 ausente |
| **SLA / tier** | "Gold", "Silver", "Standard", "prazo" | Retrieval restrito a SLA-2024; rejeitar tier "Platinum" com citação explícita |

### 4.2 Chunking diferenciado por tipo de conteúdo

**Regime A — Texto narrativo (wiki, PDFs sem tabelas):** chunks de 300-400 tokens com sobreposição de 50 tokens. Breadcrumb hierárquico como prefixo para wiki.

**Regime B — Tabelas (PDFs com tabelas complexas):** chunk atômico por tabela, até 800 tokens. Se exceder, particionar por grupos de linhas com cabeçalhos repetidos. Nunca cortar entre cabeçalho e dados. **Para tabelas em documentos com versões conflitantes (PROC-042): cada versão de tabela como chunk separado, com metadado de versão obrigatório.**

**Regime C — Documentos escaneados (OCR):** chunks de 200-300 tokens. Metadata `ocr_confidence` para penalidade no reranking.

**Regime D — Planilhas:** chunkar por unidade semântica (aba, seção lógica), não por tamanho. Toda resposta baseada em planilha inclui `indexed_date`. Máximo 600 tokens por chunk.

**Regime E — Fontes informais (FAQ):** chunks de 200-300 tokens com metadata `source_tier: informal`. Nunca apresentados como resposta definitiva — sempre acompanhados de marcação de incerteza e referência ao documento formal correspondente quando existir.

### 4.3 Tratamento de conflito de versões no contexto

Quando o retriever retornar chunks de PROC-042 v1 e v2 simultaneamente (alta probabilidade para qualquer pergunta sobre frete especial), o sistema precisa de lógica explícita de disambiguação:

**Regra de transição já documentada em PROC-042-v2, seção 5:** *"Chamados novos a partir de 01/12/2023 devem usar os multiplicadores desta versão."* Essa regra deve ser extraída como instrução determinística no system prompt — não deixada para o modelo inferir.

```
Instrução no system prompt (exemplo):
"Para cálculo de frete especial, use SEMPRE os multiplicadores de PROC-042-v2
(emitido em 10/11/2023) para chamados abertos a partir de 01/12/2023.
Se ambas as versões aparecerem no contexto, aplique esta regra e informe
ao atendente que existe uma versão anterior com valores diferentes."
```

### 4.4 Tratamento de documentos ausentes referenciados

Quando o retriever retornar chunks que referenciam PROC-043 ou PROC-088 (documentos ausentes), o modelo deve ser instruído a reconhecer a lacuna explicitamente:

```
Instrução no system prompt (exemplo):
"Se a resposta exigir PROC-043 (Frete de Cargas Perigosas) ou PROC-088
(Interceptação de Carga), informe que esses documentos não estão disponíveis
na base e oriente o atendente a contatar o setor responsável."
```

### 4.5 Estratégia de montagem do contexto (mitigação do "lost in the middle")

```
[Posição 1-3]   → Chunks com score de relevância mais alto (crítico)
[Posição 4-N-3] → Chunks complementares, score decrescente
[Posição N-2-N] → Chunks de suporte com alto score
```

Para perguntas sobre frete especial, o chunk de PROC-042-v2 (versão vigente) deve ocupar a posição 1; o chunk de PROC-042-v1 (se recuperado) deve ser posicionado no meio com label explícito de "versão anterior".

### 4.6 Retrieval em dois estágios

**Estágio 1 — Recall amplo:** top-500 chunks por similaridade semântica.

**Estágio 2 — Reranking preciso:** reordenar os 500 por cross-encoder, aplicando:
- Boost para `source_tier: formal_normative` e `formal_contractual`
- Penalidade para `source_tier: informal_operational`
- Penalidade para `ocr_quality: low`
- Boost para `doc_status: vigente`; penalidade para `doc_status: indefinido`

Selecionar top-238 para compor o contexto.

### 4.7 Trade-offs explícitos

| Decisão | Vantagem | Desvantagem |
|---|---|---|
| Regime E para FAQ | Preserva conhecimento tácito com incerteza explícita | Atendente pode questionar por que o sistema não confia no FAQ |
| Chunks de tabela como unidade atômica | Preserva relação cabeçalho-dado | Tabelas grandes (>800t) excedem o regime |
| Instrução de versão no system prompt | Determinístico; previne mistura de multiplicadores | Requer atualização manual do system prompt quando NovaTech formalizar a versão vigente |
| Classificação de intenção pré-retrieval | Estratégia adequada por tipo | Latência adicional antes do retrieval |
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

- Configurar o sistema para reconhecer quando nenhum chunk recuperado tem relevância acima do threshold mínimo — e responder explicitamente com incerteza em vez de tentar uma resposta forçada
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

| Pressuposto | Status na v2 | Resolução na v3 | Evidência |
|---|---|---|---|
| Documentos escaneados são minoria dos 800 PDFs | Não resolvido | **Confirmado direcionalmente** | exercicio-fase-1-entendimento.md: "alguns documentos escaneados" |
| Links internos do Confluence são majoritariamente dentro do espaço exportado | Não resolvido | **Violado com evidência concreta** | PROC-043 e PROC-088 referenciados por documentos da base, mas ausentes |
| Planilhas têm responsáveis que podem documentá-las | Não resolvido | **Complicado: responsável existe, mas localização é problema** | frete-base-AAAAMM.xlsx em pasta de rede (`\\novatech-fs\`), fora do SharePoint |

**Implicações para o projeto:**

- **Pressuposição 1 (OCR):** o risco OCR está confirmado como subconjunto — o esforço de calibração e auditoria é proporcional, não total. Levantamento no discovery definirá o escopo exato.

- **Pressuposição 2 (links):** a estratégia de expansão de links em tempo de indexação da v2 é necessária e insuficiente. O problema não é apenas links para páginas existentes — é referências a documentos que nunca foram indexados. A nova estratégia (seção 1.3, item 3) de indexar entradas sintéticas para documentos ausentes é a resposta a esse cenário.

- **Pressuposição 3 (planilhas):** o Regime D (documentação descritiva por planilha) é viável operacionalmente (o Comercial existe e tem o conhecimento), mas requer uma decisão de arquitetura sobre a pasta de rede. Sem essa decisão, o caso de uso central — atendente consultando valor de frete atual — não é atendível pelo assistente.

---

## 7. Registro de Alterações (v2 → v3)

### Adições por seção

| Seção | Adição | Origem |
|---|---|---|
| 1.1 — PDFs com tabelas | Caso concreto: PROC-042 v1 vs v2 como exemplo real do problema de serialização de tabelas conflitantes | Análise de Anexo A |
| 1.2 — OCR | Resolução da Assunção 1: "alguns documentos escaneados" confirmado; discovery deve quantificar | exercicio-fase-1-entendimento.md |
| 1.3 — Wiki | Resolução da Assunção 2: PROC-043 e PROC-088 confirmados como referências mortas; tiering de fontes (formal vs informal) para FAQ | Anexo A — POL-001, PROC-042, FAQ |
| 1.4 — Planilhas | Resolução da Assunção 3: frete-base-AAAAMM.xlsx em pasta de rede, fora do escopo padrão de indexação; implicação direta para o caso de uso de cálculo de frete | Anexo A — PROC-042 v1 e v2 |
| 4.1 — Intenção | Adicionada pergunta sobre carga especial/perigosa e sobre tier Platinum com comportamento específico | Análise de FAQ e SLA-2024 |
| 4.2 — Chunking | Regime E adicionado para fontes informais (FAQ); Regime B atualizado para versões conflitantes | Análise de FAQ |
| 4.3 — Conflito de versões | Nova seção: instrução determinística de desambiguação baseada na regra de transição do PROC-042-v2 | PROC-042-v2, seção 5 |
| 4.4 — Documentos ausentes | Nova seção: instrução para tratar PROC-043 e PROC-088 com resposta de lacuna explícita | Análise de Anexo A |
| **Seção 5 (nova)** | Problemas concretos no corpus: conflito de versões (5.1), FAQ informal (5.2), referências mortas (5.3), gaps de cobertura (5.4), ausência de governança (5.5) | Análise completa de Anexo A |
| **Seção 6 (nova)** | Resolução explícita dos três pressupostos pendentes da v2 com evidências documentais | Análise de Anexo A + exercício |

### O que não mudou

Os cálculos das seções 2 e 3 (estimativa de tokens e orçamento de contexto) são mantidos da v2. Os problemas de qualidade identificados na v3 não alteram o volume da base — afetam a fração do corpus que produz respostas confiáveis, que é uma dimensão qualitativa, não volumétrica.

---

*Documento produzido com base no cenário específico da NovaTech e nos documentos reais do Anexo A. As estimativas de tokens são aproximações — valores reais devem ser calibrados após amostragem do corpus completo. Os problemas documentados na seção 5 foram identificados na amostra de 5 documentos disponibilizada; o corpus de 800 PDFs provavelmente contém padrões semelhantes em escala.*
