import { z } from 'zod';
import pino from 'pino';

// ── Structured Output Schema ──────────────────────────────────────────────────
//
// .strict() rejeita qualquer campo não declarado — impede que o modelo inclua
// campos como `reasoning` ou `debug_info` que vazar iam metadados internos.

export const AssistantResponseSchema = z
  .object({
    answer: z.string().min(1),
    source_document: z.string().trim().min(1),
    confidence_score: z.number().min(0).max(1),
  })
  .strict();

export type AssistantResponse = z.infer<typeof AssistantResponseSchema>;

// ── Constantes internas ───────────────────────────────────────────────────────

const SAFE_RESPONSE: AssistantResponse = {
  answer:
    'Não foi possível processar sua consulta no momento. Por favor, entre em contato com um atendente.',
  source_document: 'SISTEMA',
  confidence_score: 0,
};

const log = pino({ name: 'response-validator' });

// ── Guardrail 2 — carga perigosa + devolução (POL-001 §3.2) ──────────────────
//
// A POL-001 §3.2 proíbe devolução de cargas perigosas ANTT classes 1-6
// pelo processo padrão. O guardrail bloqueia qualquer resposta que mencione
// ambos os temas sem conter negativa explícita.

// Cobre singular/plural de "carga(s) perigosa(s)" e sinônimos operacionais
const HAZARDOUS_CARGO_RE =
  /cargas?\s+perigosas?|material(?:\s+perigoso)?|subst[âa]ncias?\s+perigosas?/i;

// Cobre noun (devolução), infinitive (devolver), particípio (devolvida/o),
// gerúndio (devolvendo) — as formas mais comuns em respostas de atendimento
const RETURN_RE =
  /devolu[çc][aã]o|devolver|devolvid[ao]|devolvendo/i;

// Cobre as formas canônicas de negação explícita em pt-BR:
//   "não pode/podem", "não é possível", "não são elegíveis",
//   "não permite/aceita", "é vedada/proibida a devolução",
//   "impossível devolver/a devolução", "não é/são elegíveis"
const NEGATION_RE =
  /não\s+(pode[m]?|é\s+possível|são\s+elegíveis?|permite[m]?|aceita[m]?)|é\s+(vedada?|proibida?)\s+(?:a\s+)?devolu|impossível\s+(?:devolver|a\s+devolu[çc])|não\s+(?:é|são)\s+elegíveis?/i;

function isHazardousReturnViolation(answer: string): boolean {
  if (!HAZARDOUS_CARGO_RE.test(answer)) return false;
  if (!RETURN_RE.test(answer)) return false;
  // Ambos presentes: bloqueia se NÃO há negativa explícita
  return !NEGATION_RE.test(answer);
}

// ── Validator principal ───────────────────────────────────────────────────────

export function validateResponse(raw: unknown): AssistantResponse {
  // Passo 1: validação estrutural contra o schema
  const result = AssistantResponseSchema.safeParse(raw);
  if (!result.success) {
    // Loga apenas os códigos de erro — nunca o payload bruto (pode conter PII)
    log.warn(
      { reason: 'schema_violation', issueCodes: result.error.issues.map(i => i.code) },
      'Response blocked',
    );
    return SAFE_RESPONSE;
  }

  const response = result.data;

  // Guardrail 1: source_document preenchido
  // O .trim().min(1) do schema garante que strings vazias/espaços são rejeitadas,
  // mas verificamos novamente para defesa em profundidade.
  if (response.source_document.trim().length === 0) {
    log.warn({ reason: 'missing_source_document' }, 'Response blocked');
    return SAFE_RESPONSE;
  }

  // Guardrail 2: carga perigosa + devolução sem negativa explícita (POL-001 §3.2)
  if (isHazardousReturnViolation(response.answer)) {
    log.warn({ reason: 'hazardous_cargo_return_violation' }, 'Response blocked');
    return SAFE_RESPONSE;
  }

  return response;
}
