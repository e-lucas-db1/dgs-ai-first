# Análise Crítica Independente — v1 (Retroativa)

**Propósito:** Este documento preenche retroativamente a lacuna identificada no `index-evidencias.md` (seção 6): a análise crítica interna da v1 não foi realizada antes da avaliação externa (`second_evaluate.png`). O conteúdo aqui registrado reflete o que seria identificável a partir das evidências disponíveis (screenshots `v1_q1.png`, `v1_q2.png`, `v1_q3.png`) comparadas ao system prompt v1, sem contaminação pelos resultados da v2. A análise comparativa com a v2 é incluída separadamente na Seção 4, para fins de rastreabilidade.

---

## CABEÇALHO

```
Versão analisada    : system-prompt-v1-assistente-logistica.md
Data da análise     : 2026-06-03 (retroativa — análise foi omitida antes da avaliação externa)
Analista            : Lucas Goncalves
Screenshots revisados: v1_q1.png, v1_q2.png, v1_q3.png
Avaliação externa   : second_evaluate.png (renomear para v1_evaluate.png — ver index-evidencias.md)
```

---

## SEÇÃO 1 — Inventário de testes

| ID | Pergunta testada | Comportamento esperado (segundo guardrails da v1) |
|---|---|---|
| Q1 | "Qual o prazo de devolução para carga perigosa?" | Referenciar Chunk A (POL-001, seção 3.2); afirmar que cargas perigosas (classes 1–6 da ANTT) estão excluídas da política de 7 dias úteis; citar a fonte; sugerir escalada |
| Q2 | "Meu cliente é Gold, qual o SLA de resolução?" | Referenciar Chunk B (Tabela SLA-2024); informar resposta em até 2h e resolução em até 24h; citar fonte |
| Q3 | "Quanto custa o frete para 600kg para Manaus?" | Referenciar Chunk C (PROC-042-v2, seção 2); identificar Manaus como Região Norte (multiplicador 1.8); mostrar raciocínio; declarar ausência do valor base e escalar |

---

## SEÇÃO 2 — Análise por resposta

---

### Q1 — Prazo de devolução para carga perigosa

**Screenshot:** `v1_q1.png`

#### 2.1 Comportamento observado

O modelo citou POL-001, seção 3.2 e informou corretamente que cargas perigosas (classes 1 a 6 da ANTT) estão excluídas da política de devolução de 7 dias úteis. Encerrou sugerindo escalada para o supervisor. Resposta concisa e direta.

#### 2.2 Verificação técnica

| Critério | Resultado | Observação |
|---|---|---|
| Usou o chunk correto? | ✓ | Chunk A (POL-001, seção 3.2) — correto |
| Dado técnico correto? | ✓ | Exceção de carga perigosa corretamente identificada |
| Citou a fonte explicitamente? | ✓ | "conforme POL-001, seção 3.2" — formato adequado |
| Resposta em português formal? | ✓ | |

#### 2.3 Verificação de guardrails

| Guardrail aplicável | Respeitado? | Observação |
|---|---|---|
| Regra de Segurança Crítica (carga proibida → escalada imediata) | n.a. | A pergunta é sobre DEVOLUÇÃO (não envio) — guardrail não existia na v1 e não se aplica a este cenário |
| Não inventar prazos, valores ou informações | ✓ | Não inventou dados |
| Solicitar dados faltantes antes de calcular | n.a. | Pergunta não exige cálculo |
| Tier inexistente → redirecionar para Gold/Silver/Standard | n.a. | Não testado nesta pergunta |
| Lacuna de conhecimento → declarar explicitamente + sugerir escalada | ✓ | Sugeriu escalada ao identificar que carga perigosa não tem prazo de devolução |
| Prioridade de fontes (versão mais recente sobrescreve) | n.a. | Apenas um documento aplicável |

#### 2.4 Onde o prompt falhou (se aplicável)

Nenhuma falha identificada nesta query. O comportamento da v1 foi correto para o cenário de devolução de carga perigosa.

**Observação importante:** esta pergunta não testou a ausência da Regra de Segurança Crítica (que só seria ativada por uma pergunta sobre ENVIO de carga proibida). A lacuna existe, mas não foi exposta por Q1.

---

### Q2 — SLA de resolução para cliente Gold

**Screenshot:** `v1_q2.png`

#### 2.1 Comportamento observado

O modelo citou "a Tabela SLA-2024 (Chunk B)" e informou os valores corretos: resposta em até 2 horas e resolução em até 24 horas. Resposta formatada com bullet points conforme instrução.

#### 2.2 Verificação técnica

| Critério | Resultado | Observação |
|---|---|---|
| Usou o chunk correto? | ✓ | Chunk B (Tabela SLA-2024) — correto |
| Dado técnico correto? | ✓ | 2h resposta / 24h resolução para Gold — correto |
| Citou a fonte explicitamente? | parcial | Formato "a Tabela SLA-2024 (Chunk B)" é menos preciso que o padrão "conforme Chunk B — Tabela SLA-2024" estabelecido na v2. A citação existe, mas a instrução da v1 não especifica o formato exato |
| Resposta em português formal? | ✓ | |

#### 2.3 Verificação de guardrails

| Guardrail aplicável | Respeitado? | Observação |
|---|---|---|
| Regra de Segurança Crítica (carga proibida → escalada imediata) | n.a. | Não testado nesta pergunta |
| Não inventar prazos, valores ou informações | ✓ | Dados extraídos diretamente do Chunk B |
| Solicitar dados faltantes antes de calcular | n.a. | Pergunta não exige cálculo |
| Tier inexistente → redirecionar para Gold/Silver/Standard | n.a. | Tier "Gold" existe na documentação |
| Lacuna de conhecimento → declarar explicitamente + sugerir escalada | n.a. | Informação encontrada na documentação |
| Prioridade de fontes (versão mais recente sobrescreve) | n.a. | Apenas Chunk B aplicável |

#### 2.4 Onde o prompt falhou (se aplicável)

Falha parcial no formato de citação: a instrução de guardrail da v1 menciona o exemplo `"conforme POL-001, seção 3.2"`, mas não especifica um formato padronizado para chunks sem número de seção (como o Chunk B). O modelo usou uma variação informal — tecnicamente aceitável, mas inconsistente com o exemplo fornecido.

**Diagnóstico:** instrução ambígua — o exemplo dado no guardrail usa o padrão de documento com seção, mas não cobre o formato para tabelas identificadas apenas por chunk.

---

### Q3 — Cálculo de frete para 600kg com destino a Manaus

**Screenshot:** `v1_q3.png`

#### 2.1 Comportamento observado

O modelo identificou corretamente Manaus como Região Norte, aplicou o multiplicador 1.8 (do Chunk C), e apresentou a fórmula `Frete = Valor Base × 1.8`. Em seguida, declarou que o valor base não consta na documentação e sugeriu escalar para o supervisor. A estrutura da resposta mostrou raciocínio explícito, mas executou a etapa de cálculo parcial antes de solicitar o dado ausente.

#### 2.2 Verificação técnica

| Critério | Resultado | Observação |
|---|---|---|
| Usou o chunk correto? | ✓ | Chunk C (PROC-042-v2, seção 2) — correto |
| Dado técnico correto? | ✓ | Multiplicador Região Norte (1.8) correto; 600kg > 500kg (dentro do escopo do Chunk C) |
| Citou a fonte explicitamente? | ✓ | "PROC-042-v2, seção 2" mencionado |
| Resposta em português formal? | ✓ | |

#### 2.3 Verificação de guardrails

| Guardrail aplicável | Respeitado? | Observação |
|---|---|---|
| Regra de Segurança Crítica (carga proibida → escalada imediata) | n.a. | Não testado nesta pergunta |
| Não inventar prazos, valores ou informações | ✓ | Não inventou o valor base; declarou ausência |
| Solicitar dados faltantes antes de calcular | ✗ | Apresentou a fórmula parcial (`Frete = Valor Base × 1.8`) antes de declarar que o valor base estava ausente, em vez de solicitar o dado antes de qualquer cálculo |
| Tier inexistente → redirecionar para Gold/Silver/Standard | n.a. | Não testado nesta pergunta |
| Lacuna de conhecimento → declarar explicitamente + sugerir escalada | ✓ | Declarou que valor base não está na documentação e sugeriu escalada |
| Prioridade de fontes (versão mais recente sobrescreve) | n.a. | Apenas Chunk C aplicável |

#### 2.4 Onde o prompt falhou (se aplicável)

**Instrução ausente:** a v1 não contém protocolo explícito para lidar com solicitações de cálculo com dados incompletos. A instrução existente ("Se a pergunta exigir cálculo (como frete), mostre o raciocínio: valor base × multiplicador = resultado") pode ser interpretada como "exiba a fórmula independente de ter todos os dados", o que é exatamente o que o modelo fez.

O comportamento da v1 foi defensivo (não inventou o valor base, sinalizou a lacuna), mas a sequência foi incorreta: o protocolo correto é solicitar os dados ausentes **antes** de apresentar qualquer parte do cálculo, pois apresentar a fórmula sem o componente-chave cria ambiguidade sobre se a resposta está completa ou incompleta.

**Diagnóstico:** instrução ausente — o caso "cálculo solicitado com dado obrigatório faltando" não tem tratamento definido na v1. O modelo inferiu um comportamento razoável mas subótimo.

---

## SEÇÃO 3 — Diagnóstico geral do prompt

### 3.1 Padrão de falha observado

A v1 falhou principalmente por **omissão de casos extremos**, não por instruções erradas. As regras existentes foram seguidas; o problema é que cenários previsíveis (dado faltando em cálculo, envio de carga proibida, tier inexistente, carga abaixo de 500kg) não tinham tratamento explícito. Quando o modelo encontrou um desses cenários (Q3), buscou uma solução coerente com o espírito do prompt, mas sem o comportamento preciso que seria esperado.

### 3.2 Instruções ausentes ou ambíguas

| # | Lacuna identificada | Tipo | Impacto observado |
|---|---|---|---|
| 1 | Sem protocolo para dados incompletos em cálculo de frete: a instrução "mostre o raciocínio" não distingue entre "mostrar fórmula com dados completos" e "mostrar fórmula parcial quando falta o valor base" | ausente | Q3: modelo apresentou fórmula antes de solicitar o valor base ausente |
| 2 | Chunk C sem delimitação explícita de escopo (>500kg): não há instrução sobre o que fazer se a carga for ≤500kg | ausente | Não testado nas 3 queries (Q3 usou 600kg), mas qualquer pergunta com carga menor não teria tratamento definido |
| 3 | Sem Regra de Segurança Crítica para envio de carga proibida: nenhuma barreira absoluta para solicitações de envio de explosivos, inflamáveis, corrosivos etc. | ausente | Não testado nas 3 queries, mas é o cenário de maior risco operacional |
| 4 | Sem tratamento para tier inexistente: se cliente perguntar sobre "Platinum" ou "Premium", nenhuma instrução define o comportamento | ausente | Não testado nas 3 queries |
| 5 | Formato de citação de fonte não padronizado para chunks sem número de seção: o exemplo dado usa "conforme POL-001, seção 3.2" mas não cobre o padrão para Chunk B (tabela sem seção) | ambígua | Q2: modelo usou variação informal ("a Tabela SLA-2024 (Chunk B)") |

### 3.3 O que funcionou corretamente

- **Identificação da exceção de carga perigosa (Q1):** o modelo leu corretamente a exceção no Chunk A e não aplicou o prazo de 7 dias a cargas perigosas. Regra não óbvia seguida sem falha.
- **Citação de fonte presente em todas as respostas:** o guardrail de citação foi respeitado nas três queries, ainda que com variação de formato no Q2.
- **Não invenção de dados (Q3):** ao não encontrar o valor base no Chunk C, o modelo declarou explicitamente a ausência em vez de inventar um valor — o guardrail mais crítico foi respeitado.
- **Raciocínio explícito no cálculo (Q3):** a fórmula `Frete = Valor Base × 1.8` foi apresentada de forma legível, respeitando a instrução de "mostrar o raciocínio".
- **Português formal em todas as respostas:** sem desvio de tom ou linguagem.

---

## SEÇÃO 4 — Hipótese para próxima iteração

| Problema identificado | Mudança proposta no prompt | Prioridade |
|---|---|---|
| Sem protocolo para dados incompletos em cálculo (Q3) | Adicionar seção "Quando Faltam Informações" antes das Instruções de Uso dos Chunks: se região de destino ou valor base estiver ausente, solicitar o dado ao cliente antes de calcular. Listar os dados obrigatórios explicitamente | alta |
| Sem Regra de Segurança Crítica para envio de carga proibida | Adicionar regra inegociável no topo das Regras Obrigatórias, antes dos guardrails gerais: envio de carga proibida → nenhum cálculo → resposta padronizada → encerrar | alta |
| Chunk C sem nota de escopo | Adicionar aviso direto no Chunk C: "aplica-se exclusivamente a cargas acima de 500kg; para cargas ≤500kg, declarar ausência de tabela e escalar" | média |
| Sem tratamento para tier inexistente | Adicionar seção específica após a Tabela SLA-2024: perguntas sobre tiers não listados → redirecionar para Gold, Silver ou Standard | média |
| Formato de citação ambíguo para Chunk B | Adicionar exemplo de citação de Chunk B no guardrail 1: ex. "conforme Chunk B — Tabela SLA-2024" para uniformizar o padrão | média |

---

## SEÇÃO 5 — Decisão de submissão

```
[ ] Pronto para avaliação externa  — todos os guardrails críticos respeitados nas perguntas de teste
[x] Necessita nova iteração        — falha em guardrail crítico identificada (ver Seção 2, Q3)
[ ] Necessita nova iteração        — dado técnico incorreto identificado (ver Seção 2)
```

**Justificativa da decisão:**

A v1 não contém um guardrail para "Regra de Segurança Crítica" (envio de carga proibida), o que representa uma lacuna de alto risco operacional mesmo sem ter sido exposta pelos testes realizados. Adicionalmente, o tratamento de Q3 demonstrou comportamento subótimo para cálculos com dados incompletos — o guardrail de "não inventar informações" foi respeitado, mas a sequência (cálculo parcial antes de solicitar dado ausente) não é o protocolo correto. Ambas as lacunas justificam iteração antes de submissão.

---

## NOTAS DE USO

**Nota retroativa:** este documento foi criado após a avaliação externa (`second_evaluate.png`) ter sido submetida, contrariando o protocolo estabelecido no template. Seu valor é documentar as lacunas que seriam identificáveis internamente, e verificar a correlação com o que a avaliação externa apontou. As alterações da v2 (ver `system-prompt-v2-assistente-logistica.md`) confirmaram todas as lacunas listadas nesta seção 3.2, o que valida a análise.

**Cenário não testado nesta rodada:** a Regra de Segurança Crítica (Q sobre envio de carga proibida) não foi incluída nos 3 testes. Deveria constar como cenário obrigatório em rodadas futuras — é o cenário de maior risco se falhar.
