# Análise Técnica: Viabilidade de Assistente RAG para a NovaTech

**Arquitetura de Retrieval-Augmented Generation com Gerenciamento de Context Window**
**Versão 2** — revisão incorpora ajustes identificados na autorrevisão crítica da v1

---

## 1. Desafios por Tipo de Fonte

### 1.1 PDFs com Tabelas Complexas (15+ colunas)

**Desafio no pipeline RAG**

Tabelas são estruturas bidimensionais cujo significado emerge da relação entre cabeçalhos de linha, cabeçalhos de coluna e célula. Ao serializar para texto linear (única forma que o chunker padrão processa), essa estrutura colapsa. Uma tabela de 15 colunas × 30 linhas lida linha a linha produz 450 fragmentos de texto onde cada fragmento perde metade de seu significado sem o contexto das demais dimensões. Pior: um chunker por tamanho fixo pode cortar a tabela ao meio, separando cabeçalho de dados.

**Como degrada a qualidade das respostas**

O modelo recebe texto como `"Região Norte | 2.847 | 12% | R$4.2M | ..."` sem saber que a coluna 2 é "Unidades Vendidas" e a coluna 3 é "Crescimento YoY". Perguntas como *"qual região teve maior crescimento em Q3?"* retornam respostas imprecisas ou alucinadas porque o modelo tenta inferir relacionamentos que foram destruídos na serialização.

> **Impacto na estimativa de tokens (ajuste v2):** a serialização adequada de tabelas expande significativamente o volume de tokens em relação à contagem de palavras visíveis. Uma tabela de 15 colunas × 20 linhas com cabeçalhos repetidos por partição produz 600-900 tokens sozinha. Esse efeito está incorporado na estimativa revisada da seção 2.

**Estratégia de tratamento recomendada**

1. **Extração estruturada:** usar bibliotecas de parsing de PDF que preservam estrutura tabular (extração via bounding boxes para recompor linhas/colunas semanticamente, não apenas por fluxo de texto)
2. **Serialização orientada a semântica:** converter cada tabela para Markdown tabular completo, mantendo cabeçalhos repetidos a cada chunk se a tabela for particionada
3. **Chunking table-aware:** tratar cada tabela como unidade atômica indivisível quando possível; se exceder o limite de chunk, particionar por grupos de linhas semanticamente coerentes (ex.: por região, por período, por categoria) com cabeçalho repetido no topo de cada partição — nunca cortar entre cabeçalho e dados
4. **Metadata enriquecido:** indexar junto ao chunk: título da seção, número da página, nome do documento, tipo de chunk (`table` vs `text`) — permite filtros pré-retrieval que economizam espaço no contexto

---

### 1.2 PDFs Escaneados (OCR necessário)

**Desafio no pipeline RAG**

PDFs escaneados são imagens de texto. O pipeline precisa de uma camada OCR antes de qualquer processamento — e OCR introduz ruído proporcional à qualidade da digitalização. Documentos com fontes incomuns, texto inclinado, páginas muito densas ou baixa resolução produzem erros de reconhecimento que corrompem o corpus antes mesmo do chunking.

**Como degrada a qualidade das respostas**

Erros de OCR — `"cornpetitividade"` em vez de `"competitividade"`, `"R$4.8M"` lido como `"R$48M"` — degradam os embeddings vetoriais que sustentam a busca semântica. Um embedding calculado sobre texto corrompido ocupa um ponto diferente no espaço vetorial do que o embedding do texto correto. O resultado é que perguntas legítimas não encontram os documentos relevantes — falha de recall silenciosa, não erro explícito.

**Estratégia de tratamento recomendada**

1. **Auditoria de calibração antes da escala:** antes de processar os documentos escaneados em lote, auditar uma amostra representativa (mínimo 20-30 páginas de diferentes origens e formatos) para calibrar o threshold de confiança adequado ao domínio específico da NovaTech. Terminologia técnica própria da empresa terá taxa de reconhecimento diferente de texto genérico — um threshold genérico de 80% pode ser conservador demais para um domínio ou permissivo demais para outro.

2. **Pipeline OCR com pós-processamento:** aplicar correção ortográfica contextual após OCR, com dicionário especializado no domínio da NovaTech para evitar correções equivocadas em terminologia técnica

3. **Segmentação de qualidade:** calcular score de confiança do OCR por página com base no threshold calibrado; páginas abaixo do threshold marcadas com metadata `ocr_quality: low` e tratadas como fonte de menor confiança no retrieval

4. **Chunking conservador para baixa qualidade:** para páginas com `ocr_quality: low`, chunks menores (200-300 tokens) reduzem o impacto de um erro isolado; um chunk corrompido no meio de um texto longo contamina mais contexto

5. **Auditoria manual prioritária:** identificar os documentos escaneados mais consultados e priorizá-los para revisão ou redigitação; se documentos escaneados forem maioria dos 800 PDFs, o custo de pré-processamento e o impacto na qualidade do corpus são substancialmente maiores — esse escopo precisa ser levantado antes do projeto

---

### 1.3 Wiki Confluence com Links Internos e Macros

**Desafio no pipeline RAG**

Links internos criam grafos de dependência implícita: uma página que diz *"para detalhes, veja [[Política de Reembolso]]"* é semanticamente incompleta sem o conteúdo dessa referência. Macros customizadas do Confluence (painéis dinâmicos, conteúdo condicional, transclusion) frequentemente não se renderizam em exportações estáticas — produzindo texto truncado, espaços em branco ou artefatos XML visíveis no corpus.

**Como degrada a qualidade das respostas**

O modelo recebe um chunk que termina com referência a outra página, mas essa página pode ou não ter sido recuperada pelo retriever. A resposta fica incompleta ou contraditória: o modelo responde com base em metade da informação, sem saber que metade está faltando. Macros não-renderizadas introduzem ruído estrutural (`{panel:title=...}`) nos embeddings.

**Estratégia de tratamento recomendada**

1. **Mapeamento de permissões como pré-requisito:** antes de qualquer exportação ou indexação, mapear as permissões de acesso do Confluence por espaço e página. Macros de conteúdo condicional podem exibir informações diferentes para usuários com diferentes níveis de acesso — o stripping de macros pode inadvertidamente incluir no índice informação restrita. O controle de acesso deve ser definido na camada de indexação, não tratado como pós-processamento.

2. **Resolução de links em tempo de indexação:** durante a exportação, expandir referências internas de primeiro nível (não recursivo, para evitar explosão de tamanho) e incluir um resumo da página referenciada como metadata do chunk. Links que apontem para páginas fora do escopo exportado devem ser marcados como referências externas no índice — não criar referências mortas silenciosas.

3. **Stripping de macros com preservação de conteúdo:** pré-processamento específico para remover sintaxe Confluence não-renderizada; preservar o texto que a macro encapsulava, descartar apenas os delimitadores

4. **Chunking por seção lógica:** wikis têm estrutura hierárquica (H1 > H2 > H3); respeitar essa hierarquia ao chunkar, mantendo o breadcrumb hierárquico como prefixo de cada chunk (`"Processos > RH > Onboarding > Documentação Necessária"`) — o breadcrumb consome 20-40 tokens mas melhora drasticamente a precisão do retrieval

5. **Indexação de grafo paralelo:** além do índice vetorial, manter um índice de relacionamentos entre páginas para retrieval por propagação de links quando a pergunta parecer exigir múltiplas páginas relacionadas

---

### 1.4 Planilhas com Fórmulas Interdependentes

**Desafio no pipeline RAG**

Planilhas são fundamentalmente diferentes de texto: seu conteúdo é computado, não estático. Uma célula com valor `R$847.000` pode ser resultado de `=SOMA(Custos!B2:B47)*Parâmetros!D3`. O *valor* sem a *fórmula* e sem os *dados de origem* é informação incompleta. Interdependências entre abas multiplicam esse problema: alterar um parâmetro pode cascatear por dezenas de cálculos.

**Como degrada a qualidade das respostas**

Se o sistema indexa apenas valores calculados, o modelo pode responder perguntas sobre cálculos com valores desatualizados (snapshot estático de quando a planilha foi indexada) ou responder "por que esse valor?" sem conseguir rastrear a lógica subjacente. Se o sistema tenta indexar as fórmulas, o texto resultante (`=SOMASE(B2:B100,D1,C2:C100)`) é praticamente não-semântico — embeddings inúteis.

**Estratégia de tratamento recomendada**

1. **Auditoria de complexidade antes da documentação:** antes de estimar esforço, classificar as 50 planilhas por complexidade de dependência. Planilhas com fórmulas que se propagam por múltiplas abas requerem documentação 3-4× mais granular do que planilhas simples — documentar cada aba individualmente, não apenas a planilha como um todo. Esse subconjunto deve ser identificado explicitamente para planejar o esforço correto.

2. **Documentação explícita pré-indexação:** transformar cada planilha em documento descritivo: nome das abas, propósito, inputs principais, outputs principais, pressupostos e dependências externas — indexar essa documentação, não os dados brutos. Para planilhas complexas, documentar os caminhos de dependência entre abas de forma explícita.

3. **Tabelas de dados como CSV anotado:** extrair regiões de dados (sem fórmulas) como tabelas com cabeçalhos explícitos; cada linha como registro descritivo

4. **Separação input/output:** indexar separadamente os parâmetros de entrada e os resultados-chave; perguntas sobre "qual o resultado de X dado Y" não podem ser respondidas dinamicamente, mas a documentação pode explicar a relação

5. **Restrição explícita de escopo + SLA de dados:** informar o modelo (via system prompt especializado para queries de planilha) que não é possível executar recálculos e que os valores refletem a data de indexação. O sistema deve expor ao usuário a data em que cada planilha foi indexada — uma resposta correta baseada em dados desatualizados é funcionalmente uma resposta errada. Definir ciclo de re-indexação periódica (semanal ou mensal, conforme frequência de atualização das planilhas) como requisito operacional do sistema.

---

## 2. Estimativa de Tamanho da Base em Tokens

### 2.1 Cálculo por componente

**PDFs — estimativa revisada:**

A v1 usava 350 palavras/página × 0,75 = 262 tokens/página como estimativa uniforme. A revisão identificou que páginas com tabelas complexas, quando serializadas com cabeçalhos repetidos para preservar contexto, produzem tokens adicionais além do texto corrido. Assumindo que 25% das páginas (2.000 de 8.000) contêm tabelas complexas:

```
Páginas de texto puro (75%):
  6.000 × 350 palavras × 0,75 = 1.572.000 tokens

Páginas com tabelas complexas (25%):
  Texto corrido:  2.000 × 350 palavras × 0,75 =   524.000 tokens
  Serialização de tabelas (adicional estimado):
  2.000 × 500 tokens/tabela               =  1.000.000 tokens

Total PDFs revisado:                          3.096.000 tokens
(+47% sobre estimativa original de 2.100.000t)
```

**Wiki Confluence:**

```
400 páginas × 1.500 palavras × 0,75 = 450.000 tokens
```

**Planilhas — estimativa revisada:**

A v1 assumia documentação uniforme de ~1.500 palavras por planilha. A revisão recomenda classificar por complexidade de dependência. Assumindo distribuição aproximada de 50% simples / 50% complexas:

```
25 planilhas simples:
  25 × 1.500 palavras × 0,75 =  28.125 tokens

25 planilhas com fórmulas interdependentes (3× mais documentação):
  25 × 4.500 palavras × 0,75 =  84.375 tokens

Total planilhas revisado:        112.500 tokens
(+100% sobre estimativa original de 56.250t)
```

### 2.2 Consolidação revisada

| Componente | v1 (tokens) | v2 revisado (tokens) | Variação |
|---|---|---|---|
| PDFs (800 documentos) | 2.100.000 | 3.096.000 | +47% |
| Wiki Confluence (400 páginas) | 450.000 | 450.000 | — |
| Planilhas (50 arquivos) | 56.250 | 112.500 | +100% |
| **Total** | **~2.606.250** | **~3.658.500** | **+40%** |

**Impacto direto no orçamento de atenção:** o total revisado de ~3,66M tokens eleva o número de chunks para ~7.317 (a 500 tokens/chunk). A cobertura efetiva por query cai — calculada na seção 3.

**Componente de maior desafio de gerenciamento:** os PDFs continuam dominando em volume absoluto, mas a revisão mostrou que o número real de tokens pode ser significativamente maior dependendo da densidade de tabelas. As planilhas, apesar de pequenas em volume, concentram o maior risco de resposta incorreta por dados desatualizados.

---

## 3. Análise de Orçamento de Contexto

### 3.1 Cálculo do espaço disponível — revisado

A v1 reservava 4K tokens para resposta. A revisão identificou que sínteses multi-documento — o tipo de pergunta mais comum na NovaTech — podem exigir respostas de 8-12K tokens. O orçamento revisado usa 8K como margem de segurança:

```
Janela total:           128.000 tokens
(-) System prompt:       -1.000 tokens
(-) Margem de resposta:  -8.000 tokens  ← revisado de 4K para 8K
────────────────────────────────────────
Contexto disponível:    119.000 tokens
```

### 3.2 Capacidade de chunks por query — revisada

```
Espaço disponível:  119.000 tokens
Tamanho de chunk:       ÷ 500 tokens
────────────────────────────────────
Chunks por query:      ~238 chunks
```

### 3.3 Cobertura efetiva da base — revisada

```
Total estimado da base (v2):  ~3.658.500 tokens
Total de chunks (~500t):       ~7.317 chunks

Chunks recuperáveis/query:         238
Cobertura por query:     238/7.317 = ~3,25%
```

**Implicação crítica atualizada:** A cada pergunta, apenas ~3,25% da base de conhecimento da NovaTech está acessível ao modelo — uma queda de 1,5 ponto percentual em relação à estimativa original de 4,7%. Essa não é uma limitação implementacional; é uma propriedade estrutural do sistema. A qualidade das respostas é quase inteiramente determinada pela precisão do retriever: um retriever que inclui 30% de chunks irrelevantes não está "sendo 30% menos eficiente" — está consumindo 71 dos 238 slots com ruído, deixando apenas 167 slots para conteúdo útil.

### 3.4 Impacto do histórico de conversa

Em diálogos de múltiplos turnos, cada troca anterior compete pelo mesmo espaço de 119K tokens. Uma conversa com 5 turnos de perguntas e respostas pode facilmente consumir 15-20K tokens de histórico — reduzindo o espaço para chunks de 119K para ~100K (~200 chunks). Estratégias de compressão ou sumarização do histórico são necessárias para conversas longas; sem elas, o orçamento de atenção deteriora progressivamente ao longo da sessão.

---

## 4. Estratégia de Chunking Justificada

### 4.1 Classificação de intenção pré-retrieval

**Adição da v2.** Antes do retrieval, uma etapa de classificação de intenção determina a estratégia a aplicar. Esta etapa não foi contemplada na v1 e é crítica: dado que apenas 3,25% da base é acessível por query, perguntas de natureza diferente requerem estratégias de retrieval diferentes.

| Tipo de pergunta | Sinal de identificação | Estratégia de retrieval |
|---|---|---|
| **Factual simples** | Quem, quando, qual valor específico | Pipeline padrão, top-238 por relevância |
| **Multi-documento** | "comparar", "diferença entre", "relação entre X e Y" | Threshold mais alto, busca explícita por múltiplas fontes, aviso ao usuário sobre limitação |
| **Cálculo em planilha** | Operações numéricas, fórmulas, projeções | Retrieval restrito a chunks de planilha + documentação, instrução explícita de limitação de recálculo |
| **Navegação em wiki** | "como funciona o processo de", "quais são os passos" | Retrieval com propagação de grafo de links, breadcrumb como fator de relevância adicional |

Perguntas classificadas como multi-documento recebem tratamento explícito: o sistema pode proativamente informar ao usuário que a resposta depende de múltiplas fontes e que a confiabilidade é menor do que em perguntas factuais simples.

### 4.2 Chunking diferenciado por tipo de conteúdo

A NovaTech não tem uma base homogênea, e uma estratégia de chunking única seria subótima para todos os tipos. A proposta é um sistema de quatro regimes:

**Regime A — Texto narrativo (wiki, PDFs sem tabelas):** chunks de 300-400 tokens com sobreposição de 50 tokens entre chunks consecutivos. A sobreposição preserva coerência em fronteiras onde frases são cortadas. O breadcrumb hierárquico (para wiki) é incluído como prefixo adicionado antes da indexação.

**Regime B — Tabelas (PDFs com tabelas complexas):** cada tabela como chunk atômico de até 800 tokens. Se exceder 800 tokens, particionar por grupo de linhas semanticamente coerentes com cabeçalhos repetidos em cada partição. Nunca cortar uma tabela entre cabeçalho e dados.

**Regime C — Documentos escaneados (OCR):** chunks de 200-300 tokens. Menor tamanho contém o "raio de impacto" de erros de OCR. Metadata `ocr_confidence` indexado para uso no reranking: chunks de baixa qualidade OCR recebem penalidade proporcional no score antes de entrar no contexto.

**Regime D — Planilhas:** chunkar por unidade semântica, não por tamanho. Cada aba como um chunk. A documentação descritiva da planilha como chunk separado. Para planilhas complexas, cada seção de dependência como chunk próprio. Máximo de 600 tokens por chunk; se necessário, dividir a aba por seção lógica de dados. Todo chunk de planilha carrega metadata de data de indexação — exibida ao usuário na resposta.

### 4.3 Estratégia de montagem do contexto (mitigação do "lost in the middle")

O efeito "lost in the middle" é uma assimetria de atenção: modelos processam com maior fidelidade o conteúdo no início e no fim do contexto. Conteúdo no meio recebe atenção degradada.

**Proposta de ordenação dos chunks no contexto:**

```
[Posição 1-3]   → Chunks com score de relevância mais alto (crítico)
[Posição 4-N-3] → Chunks complementares, ordenados por score decrescente
[Posição N-2-N] → Chunks de suporte/contexto adicional com alto score
```

A estratégia de "sanduíche" — informação mais relevante nas bordas — mitiga o efeito sem custo adicional de tokens. Para perguntas multi-documento, os N/2 chunks mais relevantes vão ao início; os demais ao fim.

**Instrução explícita ao modelo:** o system prompt deve incluir instrução para o modelo priorizar as primeiras e últimas fontes se houver conflito de informação no meio do contexto.

### 4.4 Retrieval em dois estágios

Dado que apenas 3,25% da base é acessível por query, o retriever precisa ser preciso. Um retriever de estágio único (embedding + similaridade cosseno) é insuficiente para a heterogeneidade da base.

**Estágio 1 — Recall amplo:** recuperar top-500 chunks por similaridade semântica; o objetivo é não perder nada relevante na fase de candidatos.

**Estágio 2 — Reranking preciso:** reordenar os 500 candidatos por um modelo de reranking cross-encoder (que considera chunk e query conjuntamente, não como vetores independentes); selecionar os top-238 para compor o contexto.

O reranking é o ponto onde metadata entra como fator: tipo de chunk, qualidade OCR, relevância estrutural (tabela vs. texto), frescor do documento e — para planilhas — data de indexação.

### 4.5 Trade-offs explícitos

| Decisão | Vantagem | Desvantagem |
|---|---|---|
| Chunks pequenos (200t) | Mais slots (595), retrieval mais preciso | Menor coerência semântica; tabelas ficam fragmentadas |
| Chunks grandes (800t) | Preserva contexto; tabelas intactas | Menos slots (148); um chunk irrelevante "ocupa mais" |
| Sobreposição 50t | Elimina perda em fronteiras | Aumenta volume total em ~15%, reduz slots efetivos |
| Breadcrumb em chunks wiki | Melhora retrieval de tópicos hierárquicos | Consome 20-40 tokens por chunk |
| Classificação de intenção | Estratégia adequada por tipo de pergunta | Custo de latência adicional antes do retrieval |
| Metadata de data nas planilhas | Usuário ciente da defasagem dos dados | Consome tokens; requer lógica de exibição na interface |

---

## 5. Registro de Alterações (v1 → v2)

*Esta seção documenta o que mudou entre as versões e por que, para rastreabilidade das decisões.*

---

### Estimativas revisadas

| Item | v1 | v2 | Motivo da revisão |
|---|---|---|---|
| Tokens por página PDF com tabela | ~262t (uniforme) | ~762t (texto + serialização) | Serialização de tabelas expande tokens além das palavras visíveis |
| Total PDFs | 2.100.000t | 3.096.000t | 25% das páginas com tabelas complexas recalculadas |
| Tokens por planilha complexa | ~844t (uniforme) | ~2.531t | Documentação de fórmulas interdependentes requer 3× mais conteúdo |
| Total planilhas | 56.250t | 112.500t | Split 50/50 simples/complexas aplicado |
| **Total da base** | **~2,6M t** | **~3,66M t** | — |
| Margem de resposta | 4.000t | 8.000t | Sínteses multi-documento exigem mais espaço |
| Contexto disponível | 123.000t | 119.000t | Margem de resposta maior |
| Chunks por query | ~246 | ~238 | Contexto disponível menor |
| Cobertura por query | ~4,7% | ~3,25% | Base maior + contexto menor |

### Adições às estratégias por tipo de fonte

| Fonte | Adição na v2 | Motivo |
|---|---|---|
| PDFs escaneados (1.2) | Etapa de auditoria de calibração do threshold OCR antes da escala | Threshold genérico inadequado para terminologia técnica específica da NovaTech |
| Wiki Confluence (1.3) | Mapeamento de permissões como pré-requisito da indexação | Macros condicionais podem expor conteúdo restrito se removidas sem controle de acesso |
| Planilhas (1.4) | Auditoria de complexidade + documentação por aba + SLA de dados + re-indexação periódica | Fórmulas interdependentes requerem esforço de documentação 3-4× maior; dados desatualizados são silenciosamente incorretos |

### Adições à estratégia de retrieval e chunking (seção 4)

| Adição | Motivo |
|---|---|
| Classificação de intenção pré-retrieval (seção 4.1) | Perguntas multi-documento têm probabilidade de falha multiplicativa com retriever de baixa precisão; estratégia diferenciada reduz esse risco |
| Metadata de data em chunks de planilha (seção 4.2, Regime D) | Drift temporal de planilhas gera respostas corretas-mas-defasadas sem sinalização ao usuário |

### Pressupostos que permanecem explícitos

Os pressupostos abaixo não foram eliminados pela v2 — são restrições do cenário que precisam ser verificadas antes da implementação:

- Documentos escaneados são minoria dos 800 PDFs. Se forem maioria, o escopo de pré-processamento OCR muda fundamentalmente.
- Links internos do Confluence são majoritariamente dentro do espaço exportado. Links externos ao escopo criam referências mortas no índice.
- As 50 planilhas têm usuários ou responsáveis que podem produzir ou validar a documentação descritiva necessária para o Regime D.

---

*Documento produzido com base no cenário específico da NovaTech. As estimativas de tokens são aproximações baseadas nas características descritas — valores reais devem ser calibrados após amostragem do corpus real.*
