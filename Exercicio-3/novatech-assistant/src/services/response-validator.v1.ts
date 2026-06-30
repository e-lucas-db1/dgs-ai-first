// response-validator.ts — v1 gerado pelo Copilot
// ATENÇÃO: esta versão contém 4 problemas identificados no code review (ver entregavel-dev-3.1.md)
// Não usar em produção — consulte response-validator.ts para a versão corrigida.

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
  const hasNegation = answer.toLowerCase().includes('não pode ser devolvida');  // ← PROBLEMA 3: string pura, muito específica
  return hasCargaPerigosa && hasDevolucao && !hasNegation;
}

export function validateResponse(raw: unknown): ValidatedResponse {
  const result = ResponseSchema.safeParse(raw);

  if (!result.success) {
    log.error(                               // ← PROBLEMA 4: loga payload bruto (possível PII)
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
