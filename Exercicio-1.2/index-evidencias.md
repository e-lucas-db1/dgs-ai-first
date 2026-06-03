# Index de Evidências — Exercicio 1.2

Registro de metadados de cada artefato nesta pasta. Garante rastreabilidade da cadeia:
`system-prompt_vN → screenshot_vN_qM → analise-critica-vN-pre-avaliacao → avaliação externa → próxima iteração`.

---

## Glossário de campos

| Campo | Significado |
|---|---|
| **Versão** | Número da iteração à qual o artefato pertence |
| **Gerado por** | Prompt ou evento que originou o artefato |
| **Data** | Data e hora de criação |
| **Status** | `ativo` / `rascunho-com-problema` / `rascunho-descartado` |
| **Nome canônico** | Como este arquivo deveria se chamar segundo o guia de nomenclatura |
| **Propósito** | Papel do artefato no fluxo de iteração |

---

## 1. System Prompts

| Arquivo | Versão | Data | Status | Nome canônico | Propósito |
|---|---|---|---|---|---|
| `system-prompt-v1-assistente-logistica.md` | v1 | 2026-06-03 10:47 | ativo | — (nome já correto) | System prompt base com 3 chunks (A: devolução, B: SLA, C: frete especial) e guardrails iniciais |
| `system-prompt-v2-assistente-logistica.md` | v2 | 2026-06-03 13:17 | ativo | — (nome já correto) | System prompt com regra de segurança crítica, protocolo de dados incompletos e cenários esperados |

**Diferenças v1 → v2** (registradas no cabeçalho do próprio arquivo v2):
- Adicionada Regra de Segurança Crítica (carga proibida → escalada imediata, sem cálculo)
- Adicionado protocolo para informações incompletas antes de calcular frete
- Adicionado tratamento para tier inexistente (Gold/Silver/Standard)
- Adicionada nota de escopo no Chunk C (somente cargas >500kg)
- Adicionada seção de Cenários Esperados
- Removido mapeamento de contexto estático/dinâmico (artefato de engenharia, não instrução operacional)

---

## 2. Prompts do operador / rascunhos

| Arquivo | Versão | Data | Status | Nome canônico | Propósito |
|---|---|---|---|---|---|
| `prompt_after_evaluate.txt` | rascunho | 2026-06-03 12:57 | **rascunho-com-problema** | `prompt-rascunho-pos-avaliacao.txt` | Rascunho escrito após `second_evaluate.png` — ver Nota 1 |

### Nota 1 — Inconsistência crítica em `prompt_after_evaluate.txt`

Este arquivo apresenta três categorias de problemas:

**1. Idioma:** o prompt está escrito em inglês. Os system prompts do exercício (v1 e v2) são em português. Um prompt em inglês não pode ser usado como base para iteração do assistente de logística sem adaptação completa.

**2. Tiers inexistentes na NovaTech:** o arquivo define tiers "Standard", "Professional" e "Enterprise". O sistema da NovaTech usa "Gold", "Silver" e "Standard". A regra de tier inexistente do exercício (ex: "Platinum" → redirecionar) seria violada pela própria instrução do rascunho.

**3. Estrutura e valores de frete incompatíveis:**

| Dado | Rascunho (`prompt_after_evaluate.txt`) | System prompt real (v1/v2) |
|---|---|---|
| Base Sul/Sudeste | R$45 base + R$8/kg | Valor base × 1.1 (Sul: 1.3) |
| Base Norte | R$85 base + R$8/kg | Valor base × 1.8 |
| Multiplicadores | Metropolitano ×1.0, Rural ×1.5, Remoto ×2.0 | Não existe — apenas multiplicador regional |
| Chunk D | Política de devolução | Não existe — v1/v2 têm Chunk A para devolução |
| SLA Tiers | Standard 5-7 dias, Professional 2-3 dias | Gold 2h/24h, Silver 4h/48h, Standard 8h/72h |

**Conclusão:** este arquivo provavelmente foi gerado por um modelo de linguagem usando dados de outro domínio/exercício, ou copiado de um template externo incompatível. Não reflete o corpus da NovaTech. Deve ser mantido para rastreabilidade do processo, mas **não pode ser usado como base para v3** sem reescrita completa a partir de `system-prompt-v2-assistente-logistica.md`.

---

## 3. Screenshots de respostas

Nomenclatura atual já está correta (padrão `v{N}_q{M}.png`). Esta seção documenta o que cada screenshot captura.

| Arquivo | Versão do prompt | Data | Status | Pergunta testada |
|---|---|---|---|---|
| `v1_q1.png` | v1 | 2026-06-03 10:49 | ativo | Q1 — teste de comportamento com v1 |
| `v1_q2.png` | v1 | 2026-06-03 10:50 | ativo | Q2 — teste de comportamento com v1 |
| `v1_q3.png` | v1 | 2026-06-03 12:41 | ativo | Q3 — teste de comportamento com v1 |
| `v2_q1.png` | v2 | 2026-06-03 13:25 | ativo | Q1 — mesmo teste com v2 para comparação |
| `v2_q2.png` | v2 | 2026-06-03 13:25 | ativo | Q2 — mesmo teste com v2 para comparação |
| `v2_q3.png` | v2 | 2026-06-03 13:28 | ativo | Q3 — mesmo teste com v2 para comparação |

**Nota:** o conteúdo específico de cada pergunta deve ser documentado no artefato de análise crítica (`analise-critica-v{N}-pre-avaliacao.md`). Ver template em `template-analise-critica-independente.md`.

---

## 4. Avaliações externas

| Arquivo | Versão avaliada | Data | Status | Nome canônico | Propósito |
|---|---|---|---|---|---|
| `second_evaluate.png` | v1 | 2026-06-03 12:55 | ativo | `v1_evaluate.png` | Resultado da avaliação externa aplicada à v1 — motivou as mudanças da v2 |

**Problema de nomenclatura:** `second_evaluate.png` não comunica qual versão foi avaliada. O nome canônico seria `v1_evaluate.png`.

**Lacuna crítica:** não existe artefato de análise crítica interna criado antes de `second_evaluate.png`. O fluxo foi `v1_q3.png` capturado → avaliação externa submetida, sem revisão interna estruturada. Para iterações futuras, o arquivo `analise-critica-v{N}-pre-avaliacao.md` deve ser preenchido antes de qualquer submissão.

---

## 5. Artefatos de protocolo

| Arquivo | Data | Propósito |
|---|---|---|
| `index-evidencias.md` | 2026-06-03 | Este arquivo — índice e metadados de todos os artefatos |
| `guia-nomenclatura.md` | 2026-06-03 | Padrão de nomenclatura para screenshots, prompts e avaliações |
| `template-analise-critica-independente.md` | 2026-06-03 | Template obrigatório a ser preenchido antes de avaliação externa |

---

## 6. Artefatos ausentes que deveriam existir

| Artefato ausente | Por que deve existir | Quando criar |
|---|---|---|
| `analise-critica-v1-pre-avaliacao.md` | Revisão interna antes de submeter v1 à avaliação externa | Retroativamente, para documentar o que a avaliação identificou vs. o que seria identificável internamente |
| `analise-critica-v2-pre-avaliacao.md` | Revisão interna da v2 antes da próxima avaliação externa | Antes de submeter v2 para avaliação |

---

## 7. Recomendações de renomeação

| Arquivo atual | Renomear para | Motivo |
|---|---|---|
| `second_evaluate.png` | `v1_evaluate.png` | Comunicar explicitamente que é a avaliação da v1 |
| `prompt_after_evaluate.txt` | `prompt-rascunho-pos-avaliacao.txt` | Explicitar status de rascunho com inconsistências |

---

## 8. Status de conformidade

| Critério | Status |
|---|---|
| System prompts com nome versionado | ✓ Conforme |
| Screenshots com padrão `v{N}_q{M}` | ✓ Conforme |
| Avaliações externas com versão no nome | ✗ `second_evaluate.png` sem vinculação à v1 |
| Rascunhos marcados explicitamente | ✗ `prompt_after_evaluate.txt` sem marcação de status |
| Análise crítica interna antes de avaliação externa | ✗ Ausente para v1 e v2 |
| Índice de metadados | ✓ Este arquivo |
| Guia de nomenclatura | ✓ Ver `guia-nomenclatura.md` |
| Template de análise crítica | ✓ Ver `template-analise-critica-independente.md` |
