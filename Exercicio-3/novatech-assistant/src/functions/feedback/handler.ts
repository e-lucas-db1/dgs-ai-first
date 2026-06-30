import { app, HttpRequest, HttpResponseInit } from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';
import { z } from 'zod';
import pino from 'pino';

// ── Logging ───────────────────────────────────────────────────────────────────

const log = pino({ name: 'feedback-handler' });

// ── Cosmos DB singleton ───────────────────────────────────────────────────────
// Singleton no escopo do módulo — reutiliza pool de conexões entre invocações.
// A validação da env var ocorre em runtime na primeira chamada ao handler.

let _container: ReturnType<typeof buildContainer> | undefined;

function buildContainer() {
  const connString = process.env.COSMOS_CONNECTION_STRING;
  if (!connString) throw new Error('COSMOS_CONNECTION_STRING not configured');
  return new CosmosClient(connString).database('novatech').container('feedbacks');
}

function getContainer() {
  return (_container ??= buildContainer());
}

// ── Input schema ──────────────────────────────────────────────────────────────

const FeedbackSchema = z.object({
  queryId: z.string().min(1),
  rating: z.number().int().min(1).max(5),
  comment: z.string().max(1000).optional(),
  attendantEmail: z.string().email(),
});

type FeedbackInput = z.infer<typeof FeedbackSchema>;

// ── Handler ───────────────────────────────────────────────────────────────────

export async function feedbackHandler(
  request: HttpRequest,
): Promise<HttpResponseInit> {
  // Fail-fast se a infraestrutura não está configurada
  let container: ReturnType<typeof getContainer>;
  try {
    container = getContainer();
  } catch {
    log.error({ reason: 'missing_config' }, 'Cosmos DB not configured');
    return { status: 500, body: JSON.stringify({ error: 'Erro de configuração do servidor.' }) };
  }

  // Parse e validação do corpo da requisição
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    log.warn({ reason: 'invalid_json' }, 'Failed to parse request body');
    return { status: 400, body: JSON.stringify({ error: 'Corpo da requisição inválido.' }) };
  }

  const parsed = FeedbackSchema.safeParse(body);
  if (!parsed.success) {
    log.warn(
      { reason: 'validation_failed', issues: parsed.error.issues.map(i => i.code) },
      'Feedback input invalid',
    );
    return { status: 400, body: JSON.stringify({ error: 'Dados de feedback inválidos.' }) };
  }

  const input: FeedbackInput = parsed.data;

  // Documento com id derivado — permite lookup direto sem full-scan
  const feedback = {
    id: `${input.queryId}-${Date.now()}`,
    queryId: input.queryId,
    rating: input.rating,
    comment: input.comment,
    attendantEmail: input.attendantEmail, // armazenado para auditabilidade, nunca logado
    timestamp: new Date().toISOString(),
  };

  try {
    await container.items.create(feedback);
  } catch (err) {
    log.error(
      { reason: 'cosmos_write_failed', queryId: input.queryId },
      'Failed to persist feedback',
    );
    return { status: 500, body: JSON.stringify({ error: 'Erro ao registrar feedback. Tente novamente.' }) };
  }

  // Loga apenas campos não-pessoais (AGENTS.md: nunca logar e-mail ou nome)
  log.info({ queryId: input.queryId, rating: input.rating }, 'Feedback registered');

  return { status: 200, body: JSON.stringify({ success: true }) };
}

app.http('feedback', {
  methods: ['POST'],
  handler: feedbackHandler,
});
