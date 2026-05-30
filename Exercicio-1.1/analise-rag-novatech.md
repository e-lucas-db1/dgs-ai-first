# Análise Técnica: Viabilidade de Assistente RAG para a NovaTech

**Arquitetura de Retrieval-Augmented Generation com Gerenciamento de Context Window**

---

## 1. Desafios por Tipo de Fonte

### 1.1 PDFs com Tabelas Complexas (15+ colunas)

**Desafio no pipeline RAG**

Tabelas são estruturas bidimensionais cujo significado emerge da relação entre cabeçalhos de linha, cabeçalhos de coluna e célula. Ao serializar para texto linear (única forma que o chunker padrão processa), essa estrutura colapsa. Uma tabela de 15 colunas × 30 linhas lida linha a linha produz 450 fragmentos de texto onde cada fragmento perde metade de seu significado sem o contexto das demais dimensões. Pior: um chunker por tamanho fixo pode cortar a tabela ao meio, separando cabeçalho de dados.

**Como degrada a qualidade das respostas**

O modelo recebe texto como `"Região Norte | 2.847 | 12% | R$4.2M | ..."` sem saber que a coluna 2 é "Unidades Vendidas" e a coluna 3 é "Crescimento YoY". Perguntas como *"qual região teve maior crescimento em Q3?"* retornam respostas imprecisas ou alucinadas porque o modelo tenta inferir relacionamentos que foram destruídos na serialização.

**Estratégia de tratamento recomendada**

1. **Extração estruturada:** usar bibliotecas de parsing de PDF que preservam estrutura tabular (extração via bounding boxes para recompor linhas/colunas semanticamente, não apenas por fluxo de texto)
2. **Serialização orientada a semântica:** converter cada tabela para Markdown tabular completo, mantendo cabeçalhos repetidos a cada chunk se a tabela for particionada
3. **Chunking table-aware:** tratar cada tabela como unidade atômica indivisível quando possível; se exceder o limite de chunk, particionar por grupos de linhas com cabeçalho repetido no topo de cada partição
4. **Metadata enriquecido:** indexar junto ao chunk: título da seção, número da página, nome do documento, tipo de chunk (`table` vs `text`) — permite filtros pré-retrieval que economizam espaço no contexto

---

### 1.2 PDFs Escaneados (OCR necessário)

**Desafio no pipeline RAG**

PDFs escaneados são imagens de texto. O pipeline precisa de uma camada OCR antes de qualquer processamento — e OCR introduz ruído proporcional à qualidade da digitalização. Documentos com fontes incomuns, texto inclinado, páginas muito densas ou baixa resolução produzem erros de reconhecimento que corrompem o corpus antes mesmo do chunking.

**Como degrada a qualidade das respostas**

Erros de OCR — `"cornpetitividade"` em vez de `"competitividade"`, números trocados como `"R$4.8M"` vs `"R$48M"` (que parecem iguais mas diferem em caracteres internos) — degradam os embeddings vetoriais que sustentam a busca semântica. Um embedding calculado sobre texto corrompido ocupa um ponto diferente no espaço vetorial do que o embedding do texto correto. O resultado é que perguntas legítimas não encontram os documentos relevantes — falha de recall silenciosa, não erro explícito.

**Estratégia de tratamento recomendada**

1. **Pipeline OCR com pós-processamento:** aplicar correção ortográfica contextual após OCR, com dicionário especializado no domínio da NovaTech para evitar correções equivocadas
2. **Segmentação de qualidade:** calcular score de confiança do OCR por página; páginas abaixo de threshold (ex.: < 80% de confiança) marcadas com metadata `ocr_quality: low` e tratadas como fonte de menor confiança no retrieval
3. **Chunking conservador:** para páginas de baixa confiança, chunks menores (200-300 tokens) reduzem o impacto de um erro isolado; um chunk corrompido no meio de um texto longo contamina mais contexto
4. **Auditoria manual prioritária:** identificar os documentos escaneados mais consultados e priorizá-los para revisão/reprocessamento manual

---

### 1.3 Wiki Confluence com Links Internos e Macros

**Desafio no pipeline RAG**

Links internos criam grafos de dependência implícita: uma página que diz *"para detalhes, veja [[Política de Reembolso]]"* é semanticamente incompleta sem o conteúdo dessa referência. Macros customizadas do Confluence (painéis dinâmicos, conteúdo condicional, transclusion) frequentemente não se renderizam em exportações estáticas — produzindo texto truncado, espaços em branco ou artefatos XML visíveis no corpus.

**Como degrada a qualidade das respostas**

O modelo recebe um chunk que termina com referência a outra página, mas essa página pode ou não ter sido recuperada pelo retriever. A resposta fica incompleta ou contraditória: o modelo responde com base em metade da informação, sem saber que metade está faltando (não há sinal de "lacuna" visível para ele). Macros não-renderizadas introduzem ruído estrutural (`{panel:title=...}`) nos embeddings.

**Estratégia de tratamento recomendada**

1. **Resolução de links em tempo de indexação:** durante a exportação, expandir referências internas de primeiro nível (não recursivo, para evitar explosão de tamanho) e incluir um resumo da página referenciada como metadata do chunk
2. **Stripping de macros:** pré-processamento específico para remover sintaxe Confluence não-renderizada; preservar o texto que a macro encapsulava, descartar os delimitadores
3. **Chunking por seção lógica:** wikis têm estrutura hierárquica (H1 > H2 > H3); respeitar essa hierarquia ao chunkar, mantendo o breadcrumb hierárquico como prefixo de cada chunk (`"Processos > RH > Onboarding > Documentação Necessária"`) — o breadcrumb consome tokens mas melhora drasticamente a precisão do retrieval
4. **Indexação de grafo paralelo:** além do índice vetorial, manter um índice de relacionamentos entre páginas para retrieval por propagação de links quando a pergunta parecer exigir múltiplas páginas relacionadas

---

### 1.4 Planilhas com Fórmulas Interdependentes

**Desafio no pipeline RAG**

Planilhas são fundamentalmente diferentes de texto: seu conteúdo é computado, não estático. Uma célula com valor `R$847.000` pode ser resultado de `=SOMA(Custos!B2:B47)*Parâmetros!D3`. O *valor* sem a *fórmula* e sem os *dados de origem* é informação incompleta. Interdependências entre abas multiplicam esse problema: alterar um parâmetro pode cascatear por dezenas de cálculos.

**Como degrada a qualidade das respostas**

Se o sistema indexa apenas valores calculados, o modelo pode responder perguntas sobre cálculos com valores desatualizados (snapshot estático de quando a planilha foi indexada) ou responder "por que esse valor?" sem conseguir rastrear a lógica subjacente. Se o sistema tenta indexar as fórmulas, o texto resultante (`=SOMASE(B2:B100,D1,C2:C100)`) é praticamente não-semântico — embeddings inúteis.

**Estratégia de tratamento recomendada**

1. **Documentação explícita pré-indexação:** transformar cada planilha em documento descritivo: nome das abas, propósito, inputs principais, outputs principais, pressupostos e dependências externas — indexar essa documentação, não os dados brutos
2. **Tabelas de dados como CSV anotado:** extrair regiões de dados (sem fórmulas) como tabelas com cabeçalhos explícitos; cada linha como registro descritivo
3. **Separação input/output:** indexar separadamente os parâmetros de entrada e os resultados-chave; perguntas sobre "qual o resultado de X dado Y" não podem ser respondidas dinamicamente, mas a documentação pode explicar a relação
4. **Restrição explícita de escopo:** informar o modelo (via system prompt especializado para queries de planilha) que não é possível executar recálculos — apenas consultar os valores documentados no momento da indexação

---

## 2. Estimativa de Tamanho da Base em Tokens

### 2.1 Cálculo por componente

**PDFs (texto corrido):**

```
800 documentos × 10 páginas = 8.000 páginas totais
Estimativa: 350 palavras/página (média conservadora para documentos técnicos)
8.000 × 350 = 2.800.000 palavras
2.800.000 × 0,75 = 2.100.000 tokens
```

> **Nota metodológica:** O fator 350 palavras/página assume mix de páginas densas de texto (~450 palavras) e páginas com elementos visuais, margens e espaçamento (~250 palavras). Documentos com múltiplas tabelas podem gerar mais tokens do que palavras visíveis sugerem, pois a serialização de tabelas estruturadas expande o conteúdo.

PDFs escaneados (subconjunto): se parte dos 800 PDFs são escaneados, o OCR não altera o volume de tokens — mas *degrada* sua qualidade vetorial, como discutido na seção 1.2.

**Wiki Confluence:**

```
400 páginas × 1.500 palavras = 600.000 palavras
600.000 × 0,75 = 450.000 tokens
```

**Planilhas:**

```
Estimativa por planilha:
- Documentação descritiva gerada: ~500 palavras
- Tabelas de dados extraídas: ~800 palavras (equivalente)
- Parâmetros e fórmulas documentadas: ~200 palavras
Total por planilha: ~1.500 palavras

50 × 1.500 = 75.000 palavras
75.000 × 0,75 = 56.250 tokens
```

### 2.2 Consolidação

| Componente | Tokens estimados | Percentual do total |
|---|---|---|
| PDFs (800 documentos) | 2.100.000 | 78,8% |
| Wiki Confluence (400 páginas) | 450.000 | 16,9% |
| Planilhas (50 arquivos) | 56.250 | 2,1% |
| **Total estimado** | **~2.606.250** | **100%** |

**Componente de maior desafio de gerenciamento:** Os PDFs dominam em volume absoluto (~2,1M tokens), mas o desafio *qualitativo* mais crítico é a interdependência das planilhas — um corpus pequeno onde a informação não pode ser fragmentada sem perda semântica. O wiki representa o melhor equilíbrio entre volume e estrutura, sendo o componente com estratégia de tratamento mais madura.

---

## 3. Análise de Orçamento de Contexto

### 3.1 Cálculo do espaço disponível

```
Janela total:           128.000 tokens
(-) System prompt:       -1.000 tokens
(-) Margem de resposta:  -4.000 tokens
────────────────────────────────────────
Contexto disponível:    123.000 tokens
```

### 3.2 Capacidade de chunks por query

```
Espaço disponível:  123.000 tokens
Tamanho de chunk:       ÷ 500 tokens
────────────────────────────────────
Chunks por query:      ~246 chunks
```

### 3.3 Cobertura efetiva da base

```
Total estimado da base:  ~2.606.250 tokens
Total de chunks (~500t): ~5.213 chunks

Chunks recuperáveis/query:        246
Cobertura por query:    246/5.213 = ~4,7%
```

**Implicação crítica:** A cada pergunta, menos de 5% da base de conhecimento da NovaTech está acessível ao modelo. Isso não é uma limitação implementacional — é uma propriedade estrutural do sistema. A qualidade das respostas é, portanto, quase inteiramente determinada pela precisão do retriever: um retriever que inclui 30% de chunks irrelevantes não está "sendo 30% menos eficiente" — está *consumindo* 30% do orçamento de atenção com ruído, reduzindo o contexto útil de 246 para ~172 chunks relevantes.

### 3.4 Impacto na estratégia

**Histórico de conversa como custo:** em diálogos de múltiplos turnos, cada troca anterior compete pelo mesmo espaço de 123K tokens. Uma conversa com 5 turnos de perguntas e respostas pode facilmente consumir 15-20K tokens de histórico — reduzindo o espaço para chunks de 123K para ~105K (210 chunks). Estratégias de compressão ou sumarização do histórico são necessárias para conversas longas.

**Perguntas multi-documento são o caso mais frágil:** uma pergunta que genuinamente requer síntese de 10 documentos diferentes exige 10+ chunks relevantes, cada um de uma fonte distinta. O retriever precisa acertar todas as 10 fontes entre seus top-246 resultados — probabilidade que cai rapidamente com o aumento do número de fontes necessárias.

**Chunks de 500 tokens — o trade-off central:** com 246 slots disponíveis, a escolha de tamanho de chunk é uma decisão sobre *largura vs. profundidade*. Chunks maiores (800 tokens) reduzem para ~153 slots mas trazem mais contexto por documento. Chunks menores (200 tokens) aumentam para ~615 slots mas com menor coerência semântica. Para a NovaTech, a solução não é um tamanho único.

---

## 4. Estratégia de Chunking Justificada

### 4.1 Chunking diferenciado por tipo de conteúdo

A NovaTech não tem uma base homogênea, e uma estratégia de chunking única seria subótima para todos os tipos. A proposta é um sistema de quatro regimes:

**Regime A — Texto narrativo (wiki, PDFs sem tabelas):** chunks de 300-400 tokens com sobreposição de 50 tokens entre chunks consecutivos. A sobreposição preserva coerência em fronteiras de chunk onde frases são cortadas. O breadcrumb hierárquico (para wiki) é incluído como prefixo não-contabilizado no limite de tokens do chunk mas adicionado antes da indexação.

**Regime B — Tabelas (PDFs com tabelas complexas):** cada tabela como chunk atômico de até 800 tokens. Se a tabela exceder 800 tokens, particionar por grupo de linhas semanticamente coerentes (ex.: por região, por período, por categoria) com cabeçalhos repetidos em cada partição. Nunca cortar uma tabela entre cabeçalho e dados.

**Regime C — Documentos escaneados (OCR):** chunks de 200-300 tokens. Menor tamanho contém o "raio de impacto" de erros de OCR. Metadata de qualidade (`ocr_confidence`) indexado para uso no reranking: chunks de baixa qualidade OCR recebem penalidade no score final antes de entrar no contexto.

**Regime D — Planilhas:** não chunkar por tamanho — chunkar por unidade semântica. Cada aba como um chunk. A documentação descritiva da planilha como chunk separado. Parâmetros e resultados-chave como chunk de consulta rápida. Máximo de 600 tokens por chunk; se necessário, dividir a aba por seção lógica de dados.

### 4.2 Estratégia de montagem do contexto (mitigação do "lost in the middle")

O efeito "lost in the middle" é uma assimetria de atenção: modelos de linguagem processam com maior fidelidade o conteúdo no início e no fim do contexto. Conteúdo no meio de um contexto longo recebe atenção degradada.

**Proposta de ordenação dos chunks no contexto:**

```
[Posição 1-3]   → Chunks com score de relevância mais alto (crítico)
[Posição 4-N-3] → Chunks complementares, ordenados por score decrescente
[Posição N-2-N] → Chunks de suporte/contexto adicional com alto score
```

A estratégia de "sanduíche" — informação mais relevante nas bordas — mitiga o efeito lost-in-the-middle sem custo adicional de tokens. Para perguntas que exigem síntese de múltiplos documentos, os N/2 chunks mais relevantes vão ao início; os demais ao fim.

**Instrução explícita ao modelo:** o system prompt deve incluir instrução para o modelo priorizar as primeiras e últimas fontes se houver conflito de informação no meio do contexto. Isso compensa parcialmente o viés de atenção.

### 4.3 Estratégia de retrieval em dois estágios

Dado que apenas 4,7% da base é acessível por query, o retriever precisa ser preciso. Um retriever de estágio único (embedding + similaridade cosseno) é insuficiente para a heterogeneidade da base da NovaTech.

**Estágio 1 — Recall amplo:** recuperar top-500 chunks por similaridade semântica; o objetivo é não perder nada relevante.

**Estágio 2 — Reranking preciso:** reordenar os 500 candidatos por um modelo de reranking cross-encoder (que considera chunk e query conjuntamente, não como vetores independentes); selecionar os top-246 para compor o contexto.

O reranking é o ponto onde metadata entra como fator: tipo de chunk, qualidade OCR, relevância estrutural (tabela vs. texto), e frescor do documento.

### 4.4 Trade-offs explícitos

| Decisão | Vantagem | Desvantagem |
|---|---|---|
| Chunks pequenos (200t) | Mais slots (615), retrieval mais preciso | Menor coerência semântica; tabelas ficam fragmentadas |
| Chunks grandes (800t) | Preserva contexto; tabelas intactas | Menos slots (153); um chunk irrelevante "ocupa mais" |
| Sobreposição 50t | Elimina perda em fronteiras | Aumenta volume total em ~15%, reduz slots efetivos |
| Breadcrumb em chunks wiki | Melhora retrieval de tópicos hierárquicos | Consome 20-40 tokens por chunk |

---

## 5. Revisão Crítica

*Esta seção examina a análise anterior e identifica onde estimativas podem estar equivocadas, riscos foram subestimados ou pressupostos implícitos precisam ser explicitados.*

---

### 5.1 Estimativas possivelmente otimistas

**Estimativa de 350 palavras/página para PDFs técnicos — provavelmente subestimada em tokens**

O cálculo de 350 palavras × 0,75 = 262 tokens/página pressupõe que tabelas são parte das 350 palavras. Na prática, uma tabela com 15 colunas e 20 linhas, quando serializada adequadamente (com cabeçalhos repetidos para preservar contexto), produz facilmente 600-900 tokens sozinha — *além* do texto corrido da página. Se 25% das páginas contêm tabelas complexas:

```
Revisado:
6.000 páginas de texto: 6.000 × 262t = 1.572.000t
2.000 páginas com tabelas: 2.000 × 262t (texto) + 2.000 × 500t (tabela) = 524.000t + 1.000.000t
Total PDFs revisado: ~3.096.000 tokens (+47% sobre estimativa original)
```

**Impacto:** o total da base sobe de ~2,6M para ~3,2M tokens; a cobertura por query cai de 4,7% para ~3,8%. A magnitude da restrição é ainda maior do que a análise inicial sugere.

**Estimativa de planilhas — subestimada para fórmulas complexas**

O regime de documentação (1.500 palavras/planilha) pressupõe que a documentação descritiva captura adequadamente o conteúdo. Para planilhas com fórmulas interdependentes entre múltiplas abas, a documentação necessária para cobrir todos os caminhos de dependência pode ser 3-4× maior. **Ajuste recomendado:** auditar as 50 planilhas para identificar o subconjunto com maior complexidade de dependência; para esse subconjunto, planejar documentação mais granular (documentar cada aba individualmente, não apenas a planilha como um todo).

---

### 5.2 Riscos não considerados na análise inicial

**Risco 1 — Degradação silenciosa de qualidade no OCR**

A análise propôs um threshold de 80% de confiança OCR. O que não foi abordado: o custo de *descobrir* esse threshold para os documentos existentes. Para escalar o OCR para os documentos escaneados da NovaTech, é necessário primeiro auditar uma amostra para calibrar o threshold adequado ao domínio específico — terminologia técnica própria da empresa terá taxa de reconhecimento diferente de texto genérico.

**Pressuposto implícito que precisa ser explicitado:** a estratégia de OCR assume que documentos escaneados são uma minoria dos 800 PDFs. Se forem maioria, o custo de pré-processamento e o impacto na qualidade do corpus são significativamente maiores do que a análise sugere.

**Risco 2 — Cascata de falha em perguntas multi-documento**

A análise menciona perguntas multi-documento como "caso mais frágil", mas não quantifica a falha. Se o retriever tem precision de 70% (30% dos chunks recuperados são irrelevantes), em uma pergunta que requer síntese de 5 documentos distintos, a probabilidade de o modelo receber *todos os* 5 documentos relevantes é multiplicativa — não linear. Retrieval de baixa precisão em perguntas complexas não produz respostas parcialmente corretas: produz respostas incorretas com aparência de confiança.

**Recomendação adicionada:** implementar um mecanismo de classificação de tipo de pergunta antes do retrieval. Perguntas claramente simples (factual, um documento) seguem o pipeline padrão. Perguntas com sinais de multi-documento (comparativas, sínteses, "como X se relaciona com Y") acionam um retrieval mais conservador com threshold mais alto, e o sistema pode proativamente informar ao usuário sobre a limitação.

**Risco 3 — Drift temporal das planilhas**

A indexação é um snapshot. Planilhas financeiras ou operacionais da NovaTech podem ser atualizadas com frequência. **Pressuposto implícito:** a análise tratou a base como estática. Um plano de re-indexação periódica (semanal? mensal?) precisa ser definido, e o sistema precisa comunicar ao usuário quando está respondendo com base em dados potencialmente desatualizados — especialmente crítico para planilhas.

**Risco 4 — Macro expansion no Confluence**

A estratégia proposta faz "stripping de macros". Este é um pressuposto significativo: nem toda macro encapsula apenas formatação. Macros de conteúdo condicional no Confluence podem exibir informação diferente para usuários com diferentes permissões. O stripping pode inadvertidamente incluir no índice informação que deveria ser restrita. **Recomendação:** mapeamento de permissões de acesso deve ser feito *antes* da indexação, não tratado como pós-processamento.

---

### 5.3 Pressupostos implícitos explicitados

| Pressuposto | Onde aparece na análise | O que acontece se falso |
|---|---|---|
| OCR cobre todos os documentos escaneados com qualidade aceitável | Seção 1.2 | Subconjunto de documentos pode ser irrecuperável sem redigitação |
| Planilhas têm documentação ou usuários que podem documentá-las | Seção 1.4 | Sem documentação, o Regime D de chunking não é aplicável |
| Links internos do Confluence são entre páginas do mesmo espaço exportado | Seção 1.3 | Links para páginas externas ao escopo criam referências mortas no índice |
| 350 palavras/página é representativo dos PDFs técnicos | Seção 2 | Tabelas densas elevam o total em 30-50%, reduzindo cobertura por query |
| 4K tokens de margem é suficiente para respostas | Seção 3.1 | Respostas longas (sínteses multi-documento) podem precisar de 8-12K tokens, comprimindo o espaço para chunks |
| O histórico de conversa é negligenciável | Seção 3.4 | Em diálogos reais, 5+ turnos consomem 20-25K tokens, reduzindo o espaço efetivo para retrieval |

---

### 5.4 Conclusão da revisão: o que muda nas recomendações

Após a revisão crítica, três ajustes às recomendações originais:

1. **Revisão do orçamento de resposta:** reservar 8K tokens (não 4K) como margem de resposta para acomodar sínteses longas, reduzindo o espaço disponível para chunks de 123K para 119K (~238 chunks). O impacto é pequeno em valor absoluto, mas importante como pressuposto de design.

2. **Adição de classificação de intenção pré-retrieval:** perguntas multi-documento devem ser identificadas antes do retrieval para ajustar estratégia. Isso não estava na análise original e é crítico para a categoria de perguntas mais comum na NovaTech (sínteses que exigem múltiplos documentos).

3. **Explicitação do SLA de dados:** o sistema deve expor metadados de data de indexação ao usuário. Especialmente para planilhas e documentos operacionais, o usuário precisa saber com que data os dados foram indexados — uma resposta correta baseada em dados desatualizados é funcionalmente uma resposta errada.

---

*Documento produzido com base no cenário específico da NovaTech. As estimativas de tokens são aproximações baseadas nas características descritas — valores reais devem ser calibrados após amostragem do corpus real.*
