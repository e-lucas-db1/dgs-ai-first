# Histórico de Evolução — Análise RAG NovaTech

Registro descritivo das interações que produziram as três versões da análise técnica de viabilidade do assistente RAG para a NovaTech.

---

## Ponto de partida — o prompt original

A solicitação inicial definia um exercício estruturado com escopo preciso: produzir uma análise técnica rigorosa sobre viabilidade de assistente RAG para a NovaTech, considerando limitações práticas de gerenciamento de context window.

O prompt fornecia:
- Descrição da base de conhecimento heterogênea (~800 PDFs, ~400 páginas wiki, ~50 planilhas)
- Modelo disponível: Claude com janela de 128K tokens
- Quatro eixos obrigatórios de análise: desafios por tipo de fonte, estimativa de tokens, orçamento de contexto, estratégia de chunking
- Uma instrução de autorrevisão: após completar a análise, revisar o próprio trabalho como revisor técnico e incorporar os ajustes no documento final

O elemento mais importante do prompt era a instrução de autorrevisão — ela transformou o exercício de uma análise linear em um processo de duas camadas: produzir e depois questionar o que foi produzido.

---

## Versão 1 — Análise inicial com autorrevisão incorporada

**O que foi pedido:** análise técnica completa entregue diretamente no chat, depois salva em arquivo `.md` na pasta `Exercicio-1.1`.

**Como a análise foi construída:**

A análise cobriu os quatro eixos obrigatórios:

- **Desafios por tipo de fonte:** para cada categoria (PDFs com tabelas, PDFs escaneados, wiki com links, planilhas com fórmulas), o raciocínio seguiu sempre a mesma estrutura — qual é o desafio específico para o pipeline, como ele degrada a qualidade das respostas, e qual estratégia de tratamento resolve.

- **Estimativa de tokens:** o cálculo usou os multiplicadores fornecidos no prompt. O resultado foi ~2,6M tokens no total, dominado pelos PDFs (78,8%). Uma nota metodológica já alertava que tabelas poderiam expandir o volume além das palavras visíveis — semente do ajuste que viria na v2.

- **Orçamento de contexto:** com 128K − 1K (system prompt) − 4K (margem de resposta) = 123K disponíveis e chunks de 500 tokens, chegou-se a 246 chunks por query — cobrindo apenas ~4,7% da base por pergunta. Esse número foi o centro gravitacional de toda a análise: a restrição não é implementacional, é estrutural.

- **Estratégia de chunking:** quatro regimes diferenciados por tipo de conteúdo (texto narrativo, tabelas, OCR, planilhas) e estratégia de "sanduíche" para mitigar o efeito *lost in the middle*.

**A seção de autorrevisão (Seção 5)** foi onde o valor real apareceu. A revisão crítica identificou:
1. Estimativa de PDFs provavelmente subestimada — tabelas serializam para mais tokens do que palavras visíveis sugerem
2. Planilhas com fórmulas interdependentes precisam de documentação 3-4× mais granular
3. Quatro riscos não considerados: calibração de threshold OCR, cascata de falha em perguntas multi-documento, drift temporal das planilhas, permissions no Confluence antes do stripping de macros
4. Seis pressupostos implícitos que precisavam ser tornados explícitos

A seção 5 terminou com uma lista de três ajustes concretos às recomendações originais — que foram a entrada direta para a v2.

**Arquivo gerado:** `analise-rag-novatech.md`

---

## Versão 2 — Incorporação das recomendações da autorrevisão

**O que foi pedido:** *"baseando-se na seção 5 da análise, crie uma v2 do arquivo seguindo as recomendações descritas na seção."*

A instrução era clara: a seção 5 da v1 havia identificado problemas; a v2 deveria resolvê-los estruturalmente, não apenas anotá-los.

**O que mudou e por quê:**

**Estimativas revisadas (Seção 2):**
- PDFs: 2,1M → 3,1M tokens (+47%). O recálculo explicitou que 25% das páginas têm tabelas complexas, e cada tabela serializada adequadamente adiciona ~500 tokens além do texto corrido da página. A estimativa original ignorava esse overhead.
- Planilhas: 56K → 112K tokens (+100%). A v1 assumia documentação uniforme de 1.500 palavras por planilha. A v2 separou o conjunto em 50% simples e 50% complexas (3× mais documentação cada).
- Total da base: ~2,6M → ~3,66M tokens.

**Orçamento de contexto revisado (Seção 3):**
- Margem de resposta: 4K → 8K tokens. Sínteses multi-documento — o tipo de pergunta mais comum na NovaTech — podem exigir respostas longas. A v1 usava uma margem adequada para respostas simples.
- Contexto disponível: 123K → 119K tokens.
- Chunks por query: 246 → 238.
- Cobertura por query: 4,7% → 3,25%. Uma queda de 1,5 ponto percentual que amplifica a importância da precisão do retriever.

**Estratégias por fonte atualizadas (Seção 1):**
- OCR: adicionada etapa de auditoria de calibração do threshold *antes* de processar em lote — threshold genérico é inadequado para terminologia logística específica da NovaTech
- Wiki: mapeamento de permissões como pré-requisito da indexação — macros condicionais podem expor conteúdo restrito se removidas sem controle de acesso
- Planilhas: auditoria de complexidade + documentação por aba para casos complexos + SLA de dados explícito + ciclo de re-indexação periódica

**Adições à estratégia de retrieval (Seção 4):**
- Classificação de intenção pré-retrieval: nova etapa que diferencia perguntas factuais simples, multi-documento, de cálculo e de navegação — cada tipo com estratégia de retrieval distinta
- Metadata de data de indexação em chunks de planilha: usuário precisa saber com que data os dados foram indexados

**Seção 5 transformada:** deixou de ser uma crítica (a v2 incorporou as críticas) e passou a ser um registro de alterações rastreável, documentando o que mudou de v1 para v2 e por quê.

**Três pressupostos continuaram não resolvidos**, por falta de informação disponível naquele momento:
1. Documentos escaneados são minoria dos 800 PDFs
2. Links internos do Confluence apontam majoritariamente para páginas dentro do espaço exportado
3. As 50 planilhas têm responsáveis que podem produzir a documentação necessária

**Arquivo gerado:** `analise-rag-novatech-v2.md`

---

## Versão 3 — Resolução dos pressupostos com base na documentação real

**O que foi pedido:** *"dentro da pasta Contexto existem exemplos de arquivos e processos que descrevem o cenário da NovaTech, leia esses arquivos para analisar e explicitar claramente os pressupostos não eliminados na v2. Crie uma v3 com essa análise incorporada."*

**O que foi lido:** sete arquivos na pasta `Contexto/`:
- `exercicio-fase-1-entendimento.md` — descrição completa do cenário, exercícios por papel, informações adicionais da NovaTech
- `anexo-a-documentacao-simulada-novatech.md` — os cinco documentos reais da base: POL-001, PROC-042, PROC-042-v2, SLA-2024, FAQ-Atendimento, com notas explícitas sobre contradições e gaps identificados
- `anexo-b-chunks-referencia-rag.md` — chunks extraídos do corpus, mapa de cobertura (pergunta → chunks esperados) e armadilhas para exercícios de avaliação
- Arquivos individuais: `POL-001-politica-devolucao.md`, `PROC-042-frete-especial-v1.md`, `PROC-042-v2-frete-especial-revisado.md`, `SLA-2024-tabela-sla-clientes.md`, `FAQ-atendimento.md`

**Resolução dos três pressupostos pendentes:**

**Pressuposto 1 (OCR — minoria):** Confirmado. O exercício de desenvolvimento descreve a base como contendo *"alguns documentos escaneados (OCR necessário)"* — a palavra "alguns" confirma subconjunto minoritário. A proporção exata requer discovery. O pressuposto estava correto na direção; o escopo exato ainda é desconhecido.

**Pressuposto 2 (links dentro do escopo):** Violado com evidência concreta. A análise dos documentos reais revelou dois casos imediatos:
- POL-001 referencia PROC-088 (Interceptação de Carga), que não está na base
- PROC-042 v1 e v2 referenciam PROC-043 (Frete de Cargas Perigosas), que não está na base e está "em processo de revisão pelo Compliance"

As referências mortas não eram risco teórico — já existiam no corpus. A estratégia precisou ser expandida além de "resolver links que existem" para incluir tratamento de documentos referenciados que nunca foram indexados.

**Pressuposto 3 (planilhas têm responsáveis):** Complicado. O Comercial existe e atualiza as planilhas mensalmente — mas o arquivo mais crítico para o caso de uso principal (`frete-base-AAAAMM.xlsx`, com o valor base do cálculo de frete) está em uma pasta de rede (`\\novatech-fs\comercial\tabelas\`), fora do SharePoint. O pipeline padrão de ingestão não alcança esse arquivo. A consequência direta: o assistente consegue responder *"qual a fórmula do frete especial?"* mas não *"quanto custa frete de 600kg para Manaus?"* — que é a pergunta real e frequente dos atendentes.

**Cinco novos problemas identificados no corpus real (nova Seção 5):**

**5.1 — Conflito de versões ativo (PROC-042 v1 vs v2):** ambas as versões coexistem no SharePoint sem hierarquia formal. A análise identificou oito parâmetros com valores distintos entre as versões — multiplicadores regionais, fatores de peso e prazo adicional. O FAQ-08 documenta que o próprio time de atendimento já convive com essa ambiguidade. Sem instrução determinística de desambiguação no system prompt, o modelo mescla valores das duas versões.

**5.2 — FAQ como única fonte para tópicos críticos:** o FAQ-Atendimento é explicitamente marcado como não validado. Três tópicos críticos existem *apenas* no FAQ, sem documento formal: carga danificada em trânsito (FAQ-38), frete expresso para carga perigosa (FAQ-32), seguro de carga (FAQ-22). Adicionalmente, o FAQ-45 cita o limiar de desconto de volume como "10 fretes/mês" — baseado no PROC-042-v1, mas o PROC-042-v2 já havia alterado esse limiar para 8/15 fretes/mês. O FAQ não foi atualizado: três fontes com três valores diferentes para o mesmo parâmetro.

**5.3 — Referências a documentos ausentes:** PROC-043 e PROC-088 são referenciados por documentos indexados mas não existem na base. O modelo receberá chunks que citam esses documentos sem acesso ao seu conteúdo — risco de alucinação do conteúdo do procedimento ausente.

**5.4 — Gaps de cobertura completos:** frete padrão (cargas <500kg) não tem cobertura em nenhum documento. O mapa de cobertura do Anexo B confirma: para a pergunta *"frete para 300kg para Salvador?"*, a resposta correta é que não existe chunk relevante na base.

**5.5 — Ausência de processo unificado de revisão:** a publicação do PROC-042-v2 sem arquivar o v1, e o FAQ desatualizado em relação ao v2, são exemplos do padrão — não de acidentes pontuais. Novas versões continuarão sendo publicadas sem arquivar as anteriores. O pipeline de ingestão precisa detectar conflitos de identificador antes de indexar, não apenas ingerir automaticamente.

**O que mudou estruturalmente na v3:**

As seções 1.1 a 1.4 foram atualizadas com casos concretos dos documentos reais em vez de apenas cenários hipotéticos. A Seção 4 (chunking) ganhou dois tratamentos novos: desambiguação de versões conflitantes com instrução determinística no system prompt, e resposta padronizada para referências a documentos ausentes. Uma nova Seção 5 documentou os cinco problemas concretos com evidências textuais. Uma nova Seção 6 resolveu explicitamente os três pressupostos pendentes. As seções de estimativa de tokens e orçamento de contexto foram mantidas da v2 — os problemas de qualidade não alteram o volume, mas reduzem a fração do corpus que produz respostas confiáveis.

**Arquivo gerado:** `analise-rag-novatech-v3.md`

---

## Versão 4 — Recalibração de estimativas e análise de pipeline

**O que foi pedido:** incorporar três lacunas identificadas na avaliação externa do exercício: (1) recalibrar a estimativa de tokens para o domínio logístico real, (2) desenvolver o trade-off entre chunks máximos e chunks práticos por query, e (3) adicionar análise de viabilidade do pipeline de ingestão.

**O que mudou e por quê:**

**Estimativa de tokens recalibrada (Seção 2):**
O modelo anterior usava overhead fixo de 500 tokens por página de tabela — derivado de uma heurística para documentos genéricos. Para tabelas com 15+ colunas (padrão nos documentos da NovaTech), a serialização Markdown real é ~5× maior: uma tabela de 15 colunas × 20 linhas gera ~1.170 tokens. Adicionalmente, documentos logísticos têm um terceiro perfil ausente nas versões anteriores — formulários estruturados (CT-e, manifestos, romaneios) com campos label:valor e identificadores alfanuméricos que tokenizam como múltiplos tokens. O total revisado passa de ~3,66M para ~9,01M tokens (+2,46×), agora dentro do intervalo de referência para bases de conhecimento de escala equivalente.

**Dimensionamento adaptativo de chunks (Seção 4.3):**
A análise anterior calculava 238 chunks como máximo teórico e usava esse número como baseline. A v4 introduz o `CHUNK_BUDGET` por tipo de intenção: de 5 chunks para queries factuais simples até 25 para multi-documento. O impacto operacional é significativo — para 320 queries/dia, a diferença entre 238 chunks fixos e 15 chunks adaptativos representa ~$3.200/mês em custo de tokens de entrada. Além do custo, o dimensionamento adaptativo reduz o efeito de diluição de atenção: com 15 chunks (~7,5K tokens), o modelo opera com alta densidade de sinal em vez de baixa densidade em contexto diluído.

**Pipeline de ingestão como análise de viabilidade (Seção 7 — nova):**
A análise de viabilidade estava incompleta sem estimar o custo e o cronograma do pipeline. A nova seção cobre cinco estágios (classificação, extração, OCR, tabelas, embeddings/indexação), com estimativas de tempo e custo para cenário cloud (~$87, ~1,5h paralelizável) e self-hosted (~$10, ~2,5h com GPU). Critérios go/no-go explícitos: a validação manual de tabelas críticas (3-4h de engenheiro, não automatizável) e a decisão arquitetural sobre a pasta de rede `\\novatech-fs\` (bloqueador para o caso de uso de cálculo de valor de frete).

**Arquivo gerado:** `analise-rag-novatech-v4.md`

---

## Síntese do processo de evolução

| Dimensão | v1 | v2 | v3 | v4 |
|---|---|---|---|---|
| **Ponto de partida** | Prompt estruturado com instrução de autorrevisão | Seção 5 (autorrevisão) da v1 | Documentação real do Anexo A | Avaliação externa com gaps identificados |
| **Tipo de revisão** | Autorrevisão crítica sem nova informação | Incorporação das críticas próprias | Validação e confronto com dados reais | Recalibração por domínio + análise operacional |
| **Principais mudanças** | Criação da análise base + identificação de problemas | Recálculo de estimativas + novas estratégias | Resolução de pressupostos + 5 novos problemas concretos | Recalibração de tokens + chunks adaptativos + pipeline de ingestão |
| **Estimativa total de tokens** | ~2,6M | ~3,66M | ~3,66M | ~9,01M |
| **Cobertura por query** | ~4,7% | ~3,25% | ~3,25% (volume igual; qualidade efetiva menor) | ~1,32% (corpus calibrado) |
| **Chunks por query** | 246 fixos | 238 fixos | 238 fixos | 5–25 adaptativos por intenção |
| **Pressupostos pendentes** | 6 implícitos, não mapeados | 3 explícitos, não resolvidos | 0 pendentes | 0 pendentes |
| **Análise de pipeline** | Ausente | Ausente | Ausente | Completa (custo, cronograma, go/no-go) |

O padrão que emerge nas quatro versões reflete uma progressão de abstrato para concreto e de análise para implementação: a v1 raciocinou sobre tipos genéricos de problema; a v2 quantificou; a v3 encontrou esses problemas nos documentos reais; a v4 calibrou as estimativas para o domínio específico e adicionou a dimensão operacional — o que é necessário para ir de análise para decisão de construir.
