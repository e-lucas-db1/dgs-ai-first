# Exercício 3.2 — Revisão Crítica de Código Gerado por IA

**Papel:** Desenvolvedor  
**Tópico:** Revisão Crítica de Outputs de IA  
**Arquivo de entrega:** `src/functions/feedback/handler.ts`

---

## Parte 1 — Minha revisão (antes de usar o Claude)

Revisão feita lendo o código linha por linha contra o AGENTS.md e critérios de segurança, antes de qualquer ferramenta de IA.

### Problema A — `as any` sem validação Zod

**Classificação:** Violação do AGENTS.md + TypeScript strict mode

**Linha:**
```typescript
const body = await request.json() as any;
```

**Por que importa:** O `as any` desabilita a checagem de tipos do TypeScript para tudo que derivar de `body`. Combinado com a ausência de validação Zod, significa que `body.queryId`, `body.rating` e `body.attendantEmail` chegam ao Cosmos DB sem nenhum contrato de tipo ou presença garantida. Uma requisição com `{ "queryId": null, "rating": "abc" }` persiste dados corrompidos silenciosamente — e o registro de feedback quebrado pode comprometer o HITL que depende desses dados para decisões de revisão humana.

---

### Problema B — `console.log` em vez de pino

**Classificação:** Violação do AGENTS.md

**Linha:**
```typescript
console.log('Feedback recebido:', JSON.stringify(feedback));
```

**Por que importa:** O AGENTS.md é explícito: "pino para logging (nunca console.log)". Além da violação de convenção, `console.log` no Azure Functions não produz JSON estruturado — as entradas no Application Insights ficam como texto livre, sem campos pesquisáveis, sem correlação por `queryId`, sem níveis de severidade. Em produção, isso torna o diagnóstico de problemas desnecessariamente difícil.

---

### Problema C — `require()` dinâmico dentro da função

**Classificação:** Violação do AGENTS.md

**Linha:**
```typescript
const { CosmosClient } = require('@azure/cosmos');
```

**Por que importa:** O AGENTS.md proíbe "require dinâmico" — imports devem ser estáticos no topo do arquivo. O `require` dentro da função executa a resolução de módulo a cada invocação, adiciona overhead de I/O desnecessário, e mais importante: impede que o TypeScript verifique os tipos de `CosmosClient` em tempo de compilação. Se o pacote `@azure/cosmos` mudar a API, o erro aparece apenas em runtime.

---

### Problema D — `attendantEmail` incluído no log (dado pessoal)

**Classificação:** Violação do AGENTS.md + risco de conformidade LGPD

**Linha:**
```typescript
console.log('Feedback recebido:', JSON.stringify(feedback));
// `feedback` contém `attendantEmail`
```

**Por que importa:** O AGENTS.md é categórico: "Nunca logar dados pessoais (e-mail, nome)". E-mail de atendente em logs vai para o Azure Monitor / Application Insights, onde fica retido por até 90 dias por padrão e potencialmente replicado para workspaces de analytics. Isso cria um fluxo de dados pessoais não declarado — problema direto de conformidade com a LGPD. Diferente do armazenamento no Cosmos DB (que pode ter base legal de legítimo interesse para auditoria), presença em logs de operação não é justificável.

---

### Problema E — Ausência de tratamento de erro (try/catch)

**Classificação:** Bug potencial

**Código:**
```typescript
await container.items.create(feedback);
return { status: 200, body: 'OK' };
```

**Por que importa:** Se `container.items.create` lançar — throttling do Cosmos, credencial expirada, timeout de rede — a promise rejeitada não é capturada. O Azure Functions retorna HTTP 500 com stack trace potencialmente exposto. Do ponto de vista do harness de governança, uma falha silenciosa no feedback significa que dados de HITL se perdem sem que o sistema (ou o atendente) saiba — comprometendo o audit trail.

---

### Problema F — `COSMOS_CONNECTION_STRING` sem validação de presença

**Classificação:** Bug potencial

**Linha:**
```typescript
const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
```

**Por que importa:** Se a variável de ambiente não estiver configurada (ex: deploy em ambiente novo, ou misconfiguration), `process.env.COSMOS_CONNECTION_STRING` é `undefined`. O `CosmosClient` pode aceitar `undefined` sem jogar imediatamente, resultando em erro profundo dentro do SDK na hora do `items.create` — mensagem de erro críptica, difícil de correlacionar com a causa raiz. Fail-fast explícito é melhor: verificar e retornar 500 com mensagem clara antes de qualquer operação.

---

**Resumo da minha revisão: 6 problemas (4 AGENTS.md + 2 bugs potenciais)**

| # | Problema | Classificação |
|---|----------|---------------|
| A | `as any` sem Zod | Violação AGENTS.md |
| B | `console.log` | Violação AGENTS.md |
| C | `require` dinâmico | Violação AGENTS.md |
| D | `attendantEmail` no log | Violação AGENTS.md + LGPD |
| E | Sem try/catch | Bug potencial |
| F | Env var sem validação | Bug potencial |

---

## Parte 2 — Revisão do Claude (segunda passagem independente)

Executei o mesmo módulo no Claude como revisor independente, sem mostrar minha lista prévia.

### Achados do Claude

O Claude identificou os mesmos 6 problemas (A–F) com as seguintes adições:

**Problema G — `CosmosClient` instanciado por requisição (performance/reliability)**

```typescript
// Dentro da função — cria novo cliente a cada POST
const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
const database = client.database('novatech');
const container = database.container('feedbacks');
```

O `CosmosClient` gerencia internamente um pool de conexões TCP e caches de token de autenticação. Instanciar um novo cliente por requisição descarta esse pool a cada chamada — em volumes moderados de feedback, isso gera latência adicional de handshake e potencialmente esgota sockets no plano de Azure Functions Consumption. O padrão correto é um singleton no escopo do módulo.

**Problema H — Documento Cosmos DB sem campo `id` explícito**

```typescript
const feedback = {
  queryId: body.queryId,
  rating: body.rating,
  comment: body.comment,
  attendantEmail: body.attendantEmail,
  timestamp: new Date().toISOString()
  // ← sem campo `id`
};
```

O SDK do Cosmos DB para JavaScript gera um UUID aleatório quando `id` está ausente. Isso funciona, mas produz documentos com `id` desvinculado do `queryId` — impossível fazer `container.item(id, partitionKey)` para buscar ou atualizar um feedback específico sem uma query full-scan. Para um módulo de governança onde feedback pode precisar ser associado a uma query para revisão HITL, um `id` derivável (ex: `${queryId}-${timestamp}`) é necessário.

**Problema I — Response body `'OK'` não é JSON**

```typescript
return { status: 200, body: 'OK' };
```

Clientes que chamam o endpoint (Teams bot, painel web) provavelmente esperam JSON. Retornar texto puro sem `Content-Type: application/json` pode causar erros de parse silenciosos no frontend e dificulta contratos de API claros.

---

## Parte 3 — Comparação: minha revisão vs. Claude

### Sobreposição total (6 problemas)

Os 4 critérios mínimos do exercício (A, B, C, D) foram identificados por ambos. Os problemas E e F (ausência de try/catch e env var não validada) também foram capturados por ambos de forma independente.

### O que o Claude adicionou (3 problemas extras)

| # | Problema | Por que eu não peguei |
|---|----------|-----------------------|
| G | CosmosClient por request | Requer conhecimento de SDK internals (pool de conexões) — não visível na leitura estática do código |
| H | `id` ausente no documento | Requer conhecimento específico de Cosmos DB e como querys por `id` funcionam — não derivável só do código |
| I | Response body não-JSON | Eu notei, mas descartei como estilo — o Claude tratou como problema de contrato de API |

### O que eu peguei que o Claude não adicionou

Nada. Na comparação honesta: minha revisão manual foi suficiente para os critérios mínimos e cobriu os bugs mais críticos. O Claude adicionou profundidade em padrões de plataforma (SDK, Cosmos, HTTP contracts) que exigem conhecimento além da leitura do código em si.

### Insight da comparação

A revisão humana é mais rápida em identificar violações explícitas de padrão (AGENTS.md listava exatamente o que procurar). O Claude é mais eficaz em problemas implícitos de plataforma que não aparecem no checklist — mas exigem conhecimento contextual que o modelo carrega do treinamento. **A combinação é mais forte que qualquer uma isolada.**

---

## Parte 4 — Código reescrito (corrigido com Copilot, seguindo AGENTS.md)

**Arquivo:** [handler.ts](novatech-assistant/src/functions/feedback/handler.ts)  
**Cópia no projeto:** [Exercicio-2/.../handler.ts](../../Exercicio-2/novatech-assistant/novatech-assistant/src/functions/feedback/handler.ts)

Correções aplicadas:

| Problema | Correção |
|----------|----------|
| A — `as any` | Schema Zod com tipos estritos e validação em runtime |
| B — `console.log` | `pino` com nome do serviço |
| C — `require` dinâmico | Import estático no topo do arquivo |
| D — PII no log | Desestruturação: loga apenas `queryId` e `rating` |
| E — Sem try/catch | Dois blocos try/catch com retornos HTTP corretos |
| F — Env var | Verificação com fail-fast antes de qualquer operação |
| G — Client por request | Singleton no escopo do módulo |
| H — `id` ausente | `id` derivado de `queryId` + timestamp |
| I — Body não-JSON | `JSON.stringify({ success: true })` com status 200 |

```typescript
// Código final — ver handler.ts para o arquivo completo
```
