# Guia de Nomenclatura de Evidências

Referência obrigatória para nomear artefatos em rodadas de teste iterativas de system prompts.
O nome do arquivo deve comunicar, sozinho: **tipo**, **versão do prompt** e **posição na sequência**.

---

## Padrão por tipo de artefato

### System prompts

```
system-prompt-v{N}-{contexto}.md
```

- `{N}`: número da versão (1, 2, 3…)
- `{contexto}`: identificador curto do domínio, sem espaços (ex: `assistente-logistica`, `suporte-tecnico`)

Exemplos:
```
system-prompt-v1-assistente-logistica.md   ✓
system-prompt-v2-assistente-logistica.md   ✓
system_prompt_final.md                     ✗  (sem versão, sem contexto)
prompt_novo.txt                            ✗  (tipo ambíguo, sem versão)
```

---

### Screenshots de resposta

```
v{N}_q{M}.png
```

- `{N}`: versão do system prompt **ativo no momento da captura**
- `{M}`: número da pergunta de teste naquela rodada (sequencial por versão)

Exemplos:
```
v1_q1.png    ✓  primeira pergunta testada com system prompt v1
v1_q2.png    ✓  segunda pergunta testada com system prompt v1
v2_q1.png    ✓  mesma primeira pergunta, agora com system prompt v2
```

Antipadrões:
```
first_response.png      ✗  sem versão, sem número de pergunta
response_safety.png     ✗  nome semântico não rastreável entre versões
second_response.png     ✗  "second" é posição absoluta na pasta, não relativa ao prompt
```

**Regra complementar:** se uma resposta exige mais de um screenshot, use sufixo alfabético:
```
v1_q2a.png   (primeira parte da resposta à pergunta 2, versão 1)
v1_q2b.png   (segunda parte)
```

---

### Screenshots de avaliação externa

```
v{N}_evaluate.png
```

Quando houver mais de um avaliador ou mais de uma rodada de avaliação para a mesma versão:
```
v{N}_evaluate_{identificador}.png
```

Exemplos:
```
v1_evaluate.png             ✓  avaliação externa da v1
v2_evaluate.png             ✓  avaliação externa da v2
v1_evaluate_rubrica-a.png   ✓  quando há múltiplas rubricas
second_evaluate.png         ✗  não comunica qual versão foi avaliada
first_evaluate.png          ✗  idem
```

---

### Documento de análise crítica interna

```
analise-critica-v{N}-pre-avaliacao.md
```

- Deve ser criado **antes** de submeter a versão para avaliação externa
- O sufixo `-pre-avaliacao` é intencional: sinaliza que é a perspectiva do analista sem contaminação do resultado externo

Exemplos:
```
analise-critica-v1-pre-avaliacao.md   ✓
analise-critica-v2-pre-avaliacao.md   ✓
```

---

### Rascunhos com problemas ou descartados

```
prompt-rascunho-{descricao-curta}.txt
```

- Nunca nomear como `prompt_after_evaluate.txt` ou `prompt_novo.txt` — sem marcação de status, esses nomes sugerem que o arquivo está pronto para uso
- A palavra `rascunho` no nome é o sinal de que **não deve ser usado em produção sem auditoria**

Exemplos:
```
prompt-rascunho-pos-avaliacao.txt       ✓
prompt-rascunho-experimento-chunks.txt  ✓
prompt_after_evaluate.txt               ✗  (parece arquivo ativo)
```

---

## Cadeia completa de rastreabilidade

Para cada ciclo de iteração, os artefatos devem seguir esta sequência:

```
system-prompt-v{N}.md
        │
        ▼  gera (testado com as perguntas Q1, Q2, Q3…)
v{N}_q1.png
v{N}_q2.png
v{N}_q3.png
        │
        ▼  analisados internamente em (OBRIGATÓRIO antes do próximo passo)
analise-critica-v{N}-pre-avaliacao.md
        │
        ▼  submetidos à avaliação externa
v{N}_evaluate.png
        │
        ▼  motiva
system-prompt-v{N+1}.md
```

**Regra inviolável:** `v{N}_evaluate.png` nunca deve preceder `analise-critica-v{N}-pre-avaliacao.md` no histórico de criação.

---

## Aplicação ao Exercicio 1.2

| Arquivo atual | Nome canônico | Conforme? |
|---|---|---|
| `system-prompt-v1-assistente-logistica.md` | — (correto) | ✓ |
| `system-prompt-v2-assistente-logistica.md` | — (correto) | ✓ |
| `v1_q1.png` | — (correto) | ✓ |
| `v1_q2.png` | — (correto) | ✓ |
| `v1_q3.png` | — (correto) | ✓ |
| `v2_q1.png` | — (correto) | ✓ |
| `v2_q2.png` | — (correto) | ✓ |
| `v2_q3.png` | — (correto) | ✓ |
| `second_evaluate.png` | `v1_evaluate.png` | ✗ renomear |
| `prompt_after_evaluate.txt` | `prompt-rascunho-pos-avaliacao.txt` | ✗ renomear + ver Nota 1 do index |

---

## Casos especiais

**Mesma pergunta, múltiplas versões do modelo:** o `{N}` muda, o `{M}` permanece igual. Isso permite comparação direta: `v1_q2.png` vs `v2_q2.png` são a mesma pergunta sob prompts diferentes.

**Testes exploratórios (não parte do conjunto oficial):** adicionar sufixo `-exp`:
```
v2_q4-exp.png   (pergunta exploratória, fora do conjunto de testes padrão)
```

**Múltiplos avaliadores externos:** se dois avaliadores independentes avaliam a mesma versão, nomear com identificador para evitar sobrescrição:
```
v1_evaluate-avaliador-a.png
v1_evaluate-avaliador-b.png
```
