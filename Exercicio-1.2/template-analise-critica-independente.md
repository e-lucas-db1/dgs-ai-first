# Template — Análise Crítica Independente (Pré-Avaliação Externa)

**Propósito:** Este documento deve ser preenchido pelo analista **antes** de submeter qualquer versão do system prompt para avaliação externa. Garante que problemas identificáveis internamente sejam registrados com perspectiva própria, sem contaminação pelo resultado da rubrica externa.

**Quando criar:** imediatamente após capturar todos os screenshots `v{N}_q{M}.png` da versão em teste.

**Nome do arquivo:** `analise-critica-v{N}-pre-avaliacao.md`

---

## CABEÇALHO

```
Versão analisada    : system-prompt-v{N}-{contexto}.md
Data da análise     : AAAA-MM-DD
Analista            : [nome]
Screenshots revisados: v{N}_q1.png, v{N}_q2.png, v{N}_q3.png
```

---

## SEÇÃO 1 — Inventário de testes

Liste cada pergunta testada, com o comportamento esperado conforme o system prompt desta versão.
Preencher antes de rever os screenshots — força comparação sem viés retrospectivo.

| ID | Pergunta testada | Comportamento esperado (segundo guardrails da versão) |
|---|---|---|
| Q1 | [texto da pergunta] | [o que o prompt instrui que deve acontecer] |
| Q2 | [texto da pergunta] | [o que o prompt instrui que deve acontecer] |
| Q3 | [texto da pergunta] | [o que o prompt instrui que deve acontecer] |

---

## SEÇÃO 2 — Análise por resposta

Repetir este bloco para cada pergunta (Q1, Q2, Q3…).

---

### Q{M} — [título curto da pergunta]

**Screenshot:** `v{N}_q{M}.png`

#### 2.1 Comportamento observado
[Descrever em 2–4 linhas o que a resposta fez, sem julgamento ainda. Apenas o que aconteceu.]

#### 2.2 Verificação técnica

| Critério | Resultado | Observação |
|---|---|---|
| Usou o chunk correto? | ✓ / ✗ / parcial | [qual chunk foi usado, qual deveria ter sido] |
| Dado técnico correto? | ✓ / ✗ / parcial | [se ✗ ou parcial: qual valor estava errado e qual é o correto] |
| Citou a fonte explicitamente? | ✓ / ✗ / parcial | [ex: "conforme Chunk B — Tabela SLA-2024" ou ausência da citação] |
| Resposta em português formal? | ✓ / ✗ | |

#### 2.3 Verificação de guardrails

Marcar cada guardrail que era aplicável a esta pergunta.

| Guardrail aplicável | Respeitado? | Observação |
|---|---|---|
| Regra de Segurança Crítica (carga proibida → escalada imediata) | ✓ / ✗ / n.a. | |
| Não inventar prazos, valores ou informações | ✓ / ✗ / n.a. | |
| Solicitar dados faltantes antes de calcular | ✓ / ✗ / n.a. | |
| Tier inexistente → redirecionar para Gold/Silver/Standard | ✓ / ✗ / n.a. | |
| Lacuna de conhecimento → declarar explicitamente + sugerir escalada | ✓ / ✗ / n.a. | |
| Prioridade de fontes (versão mais recente sobrescreve) | ✓ / ✗ / n.a. | |

#### 2.4 Onde o prompt falhou (se aplicável)

[Se algum critério acima foi ✗ ou parcial: identificar a instrução no system prompt que deveria ter coberto esse caso e por que não funcionou. Pode ser: instrução ausente, instrução ambígua, instrução presente mas não proeminente o suficiente, conflito entre instruções.]

Exemplos de diagnóstico:
- "O guardrail de carga proibida existe mas usa linguagem condicional ('quando perguntar sobre...'), permitindo que o modelo interprete como sugestão e não como barreira absoluta."
- "O Chunk C não explicita o escopo de >500kg, então o modelo aplicou os multiplicadores também a cargas menores."
- "A instrução de citação de fonte está no final do prompt, depois de 4 outras seções, e foi ignorada na resposta."

---

## SEÇÃO 3 — Diagnóstico geral do prompt

### 3.1 Padrão de falha observado

[Há um padrão comum entre os problemas identificados nas Q's acima? Ex: "o modelo consistentemente ignora as exceções listadas"; "as instruções de escalada são seguidas mas sem a frase exata solicitada".]

### 3.2 Instruções ausentes ou ambíguas

Liste as lacunas identificadas no prompt desta versão:

| # | Lacuna identificada | Tipo | Impacto observado |
|---|---|---|---|
| 1 | [descrição da lacuna] | ausente / ambígua / conflitante | [qual pergunta evidenciou o problema] |
| 2 | | | |

**Tipos:**
- `ausente`: o caso existe no mundo real mas o prompt não instrui sobre ele
- `ambígua`: a instrução existe mas pode ser interpretada de mais de uma forma
- `conflitante`: duas instruções do prompt levam a comportamentos opostos no mesmo cenário

### 3.3 O que funcionou corretamente

[Registrar comportamentos que o prompt elicitou corretamente — especialmente os não óbvios, para garantir que não sejam quebrados na v{N+1}.]

---

## SEÇÃO 4 — Hipótese para próxima iteração

[Com base nos problemas identificados nas seções anteriores, quais mudanças específicas no system prompt devem resolver os problemas? Ser concreto: "adicionar regra X antes da seção Y" é mais útil do que "melhorar a clareza das instruções".]

| Problema identificado | Mudança proposta no prompt | Prioridade |
|---|---|---|
| [problema da seção 2 ou 3] | [mudança específica: adicionar / remover / mover / reformular qual instrução] | alta / média |
| | | |

---

## SEÇÃO 5 — Decisão de submissão

```
[ ] Pronto para avaliação externa  — todos os guardrails críticos respeitados nas perguntas de teste
[ ] Necessita nova iteração        — falha em guardrail crítico identificada (ver Seção 2)
[ ] Necessita nova iteração        — dado técnico incorreto identificado (ver Seção 2)
```

**Justificativa da decisão:**
[1–3 linhas explicando o critério que levou à decisão acima.]

---

## NOTAS DE USO

- **Não altere este documento após ver o resultado da avaliação externa.** O valor deste artefato está em capturar a perspectiva interna *antes* do feedback externo. Se quiser registrar como a avaliação externa se relaciona com esta análise, crie um documento separado (`retrospectiva-v{N}.md`).
- **Se uma seção não se aplica** (ex: nenhuma pergunta testou a regra de segurança crítica), marcar explicitamente como "não testado nesta rodada" em vez de deixar em branco — branco é ambíguo entre "não aplicável" e "esqueceu de preencher".
- **O template é um mínimo, não um teto.** Se uma resposta levantou um problema que não cabe em nenhuma linha da tabela, adicione uma subseção livre abaixo do bloco da pergunta correspondente.
