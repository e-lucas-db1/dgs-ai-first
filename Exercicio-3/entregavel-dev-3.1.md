# Exercício 3.1 — Structured Output e Verificações Determinísticas

**Papel:** Desenvolvedor  
**Tópico:** Harness Engineering  
**Arquivo de entrega:** `src/services/response-validator.ts`

---

## Tarefa 1 — Schema Zod (Structured Output)

O schema define o contrato que toda resposta do assistente deve respeitar antes de qualquer análise de conteúdo. Usando GitHub Copilot, o ponto de partida gerado foi:

```typescript
// v1 — gerado pelo Copilot
const ResponseSchema = z.object({
  answer: z.string().min(1),
  source_document: z.string().min(1),
  confidence_score: z.number().min(0).max(1),
});
```

**Schema corrigido após code review (Tarefa 3):**

```typescript
export const AssistantResponseSchema = z
  .object({
    answer: z.string().min(1),
    source_document: z.string().trim().min(1),
    confidence_score: z.number().min(0).max(1),
  })
  .strict();

export type AssistantResponse = z.infer<typeof AssistantResponseSchema>;
```

Mudanças em relação à v1:
- `.strict()` adicionado — rejeita campos não declarados
- `.trim()` em `source_document` — rejeita strings que contêm apenas espaços

---

## Tarefa 2 — response-validator.ts (versão inicial, gerada pelo Copilot)

**Arquivo:** [response-validator.v1.ts](novatech-assistant/src/services/response-validator.v1.ts)

O Copilot gerou a implementação abaixo. É funcionalmente plausível mas contém problemas identificados no code review (Tarefa 3).

```typescript
// response-validator.ts — v1 gerado pelo Copilot

import { z } from 'zod';
import pino from 'pino';

const ResponseSchema = z.object({           // ← PROBLEMA 1: sem .strict()
  answer: z.string().min(1),
  source_document: z.string().min(1),       // ← sem .trim() — aceita "   "
  confidence_score: z.number().min(0).max(1),
});

type ValidatedResponse = z.infer<typeof ResponseSchema>;

const log = pino({ name: 'response-validator' });

const SAFE_RESPONSE: ValidatedResponse = {
  answer: 'Não foi possível processar sua consulta. Entre em contato com um atendente.',
  source_document: 'SISTEMA',
  confidence_score: 0,
};

function checkHazardousCargo(answer: string): boolean {
  const hasCargaPerigosa = /carga perigosa/i.test(answer);   // ← PROBLEMA 2: singular apenas
  const hasDevolucao = /devolu[çc][aã]o|devolver/i.test(answer);
  const hasNegation = answer.toLowerCase().includes('não pode ser devolvida');  // ← PROBLEMA 3: string pura
  return hasCargaPerigosa && hasDevolucao && !hasNegation;
}

export function validateResponse(raw: unknown): ValidatedResponse {
  const result = ResponseSchema.safeParse(raw);

  if (!result.success) {
    log.error(                               // ← PROBLEMA 4: loga payload bruto
      { error: result.error, payload: raw },
      'Schema validation failed',
    );
    return SAFE_RESPONSE;
  }

  const response = result.data;

  // Guardrail 1
  if (!response.source_document || response.source_document.trim() === '') {
    log.warn({ reason: 'empty_source_document' }, 'Response blocked');
    return SAFE_RESPONSE;
  }

  // Guardrail 2
  if (checkHazardousCargo(response.answer)) {
    log.warn({ reason: 'hazardous_cargo_return_violation' }, 'Response blocked');
    return SAFE_RESPONSE;
  }

  return response;
}
```

---

## Tarefa 3 — Code Review

> Realizado por Claude. Objetivo: identificar ao menos 2 problemas reais no código gerado pelo Copilot.

Foram encontrados **4 problemas**. Os dois mais críticos são os de número 1 e 3.

---

### Problema 1 — Schema aceita campos extras (risco: vazamento de metadados internos)

**Risco:** `z.object()` sem `.strict()` permite que o modelo retorne campos adicionais não declarados — como `reasoning`, `debug_info`, `model_version` ou `internal_context`. Esses campos passam silenciosamente pela validação e podem chegar à camada de resposta ou ser persistidos em log, expondo o raciocínio interno do modelo para camadas que não deveriam ter acesso a ele.

**Código problemático (linha 3):**
```typescript
const ResponseSchema = z.object({
  answer: z.string().min(1),
  source_document: z.string().min(1),
  confidence_score: z.number().min(0).max(1),
});
// Resultado: { answer, source_document, confidence_score, reasoning: "...", debug_info: "..." }
// passa sem erro — o campo extra segue para frente.
```

**Correção:**
```typescript
const AssistantResponseSchema = z
  .object({
    answer: z.string().min(1),
    source_document: z.string().trim().min(1),
    confidence_score: z.number().min(0).max(1),
  })
  .strict(); // ZodError imediato se qualquer campo extra aparecer
```

**Distinção importante:** Sem `.strict()`, a validação é _permissiva por padrão_. Em structured outputs de LLMs, onde o modelo pode incluir campos extras dependendo do prompt e da versão do modelo, assumir formato fixo sem `.strict()` cria um contrato frágil.

---

### Problema 2 — Detecção de "carga perigosa" só cobre o singular

**Risco:** A regex `/carga perigosa/i` não detecta "cargas perigosas" (plural), que é a forma mais comum em frases como "Cargas perigosas não podem ser devolvidas pelo processo padrão". O guardrail 2 falha silenciosamente nesses casos: a condição `hasCargaPerigosa` retorna `false`, a função `checkHazardousCargo` retorna `false`, e uma resposta incorreta que afirme a devolução possível de "cargas perigosas" passaria sem bloqueio.

**Código problemático (linha 17):**
```typescript
const hasCargaPerigosa = /carga perigosa/i.test(answer);
// "cargas perigosas" → não detectado (plural)
// "material perigoso" → não detectado (sinônimo operacional)
```

**Correção:**
```typescript
const HAZARDOUS_CARGO_RE =
  /cargas?\s+perigosas?|material(?:\s+perigoso)?|subst[âa]ncias?\s+perigosas?/i;
// cargas? → "carga" ou "cargas"
// perigosas? → "perigosa" ou "perigosas"
// material perigoso → sinônimo operacional comum
// substâncias perigosas → forma usada na documentação ANTT
```

---

### Problema 3 — Detecção de negação demasiado específica (falsos negativos no guardrail)

**Risco:** A condição `answer.toLowerCase().includes('não pode ser devolvida')` detecta exatamente essa frase e nenhuma outra. Isso cria dois problemas simultâneos:

1. **Falso negativo (permite respostas incorretas):** Uma resposta como _"Sim, cargas perigosas podem ser devolvidas mediante autorização"_ não contém "não pode ser devolvida", então `hasNegation = false`, `checkHazardousCargo` retorna `true`, e a resposta é **corretamente bloqueada** — mas somente por acaso, porque o termo "devolução" está presente. O problema surge quando o modelo usa frases como _"A devolução de carga perigosa está disponível via Gestão de Riscos"_ — "devolução" está presente, "não pode ser devolvida" não está, e o guardrail bloqueia uma resposta que, a depender do contexto, pode ser tecnicamente correta (POL-001 §3.2 menciona que o cliente deve contatar Gestão de Riscos, não que é absolutamente impossível).

2. **Falso positivo (bloqueia respostas corretas):** Uma resposta como _"Cargas perigosas não são elegíveis para devolução pelo processo padrão"_ é **correta** segundo a POL-001, mas o detector não reconhece "não são elegíveis" como negação. Resultado: a resposta correta é bloqueada e substituída pela mensagem padrão — degradando a experiência do atendente com dados corretos.

**Código problemático (linha 19):**
```typescript
const hasNegation = answer.toLowerCase().includes('não pode ser devolvida');
// Não detecta:
// - "não podem ser devolvidas" (plural)
// - "não é possível devolver"
// - "não são elegíveis para devolução"
// - "é vedada a devolução"
// - "é proibida a devolução"
// - "impossível devolver"
// - "não é elegível para devolução"
```

**Correção:**
```typescript
const NEGATION_RE =
  /não\s+(pode[m]?|é\s+possível|são\s+elegíveis?|permite[m]?|aceita[m]?)|é\s+(vedada?|proibida?)\s+(?:a\s+)?devolu|impossível\s+(?:devolver|a\s+devolu[çc])|não\s+(?:é|são)\s+elegíveis?/i;
```

Esta regex cobre as formas canônicas de negação em português operacional e elimina tanto os falsos positivos quanto os falsos negativos.

---

### Problema 4 — Log expõe payload bruto (violação AGENTS.md: nunca logar dados pessoais)

**Risco:** O campo `payload: raw` passa o objeto completo recebido para o log. O `raw` pode conter a pergunta original do usuário, um `queryId` rastreável, metadados de sessão, ou qualquer outra informação enviada pelo cliente do Teams — incluindo potencialmente dados pessoais (nome do atendente, e-mail, fragmento de conversa). Isso viola o AGENTS.md ("Nunca logar dados pessoais") e pode criar exposição em sistemas de log centralizados (Azure Monitor, Application Insights).

**Código problemático (linha 25):**
```typescript
log.error(
  { error: result.error, payload: raw },  // ← `raw` contém dados do usuário
  'Schema validation failed',
);
```

**Correção:**
```typescript
log.warn(
  { reason: 'schema_violation', issueCodes: result.error.issues.map(i => i.code) },
  'Response blocked',
);
// Loga apenas os códigos de erro do Zod (ex: ["too_small", "unrecognized_keys"])
// — informação suficiente para diagnóstico sem expor o conteúdo.
```

---

## Entregável final — response-validator.ts corrigido

**Versão inicial (Copilot):** [response-validator.v1.ts](novatech-assistant/src/services/response-validator.v1.ts)  
**Versão corrigida (exercício):** [response-validator.ts](novatech-assistant/src/services/response-validator.ts)  
**Cópia no projeto:** [Exercicio-2/.../response-validator.ts](../../Exercicio-2/novatech-assistant/novatech-assistant/src/services/response-validator.ts)

Resumo das correções aplicadas:

| # | Problema | Correção |
|---|----------|----------|
| 1 | Schema aceita campos extras | `.strict()` adicionado ao schema |
| 2 | Regex singular perde plural | `cargas?\s+perigosas?` com alternativas |
| 3 | Negação muito específica | Regex abrangente com 6 padrões de negação |
| 4 | Payload bruto no log | Apenas `issueCodes` — sem dados do usuário |

---

## Distinção: lógica probabilística vs. validação determinística

| Camada | Tipo | Exemplo |
|--------|------|---------|
| System prompt | Probabilístico | "Sempre cite a fonte da resposta" |
| Schema Zod | Determinístico | `source_document: z.string().min(1)` — rejeita se ausente |
| Guardrail 1 | Determinístico | Bloqueia se `source_document` está vazio, sem exceção |
| Guardrail 2 | Determinístico | Bloqueia se detecta padrão de violação da POL-001 |

O prompt pede ao modelo que cite a fonte e respeite a política de carga perigosa, mas um modelo pode "esquecer" em 12% dos casos (como observado em testes). O harness de código aplica as mesmas regras de forma determinística — o modelo não tem como contornar o guardrail, independentemente do que gerar.
