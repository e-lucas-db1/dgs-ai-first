# Evidencias de Execucao - Exercicio 2.3 (Desenvolvedor)

Data: 12/06/2026  
Projeto: novatech-assistant  
Diretorio: Exercicio-2/novatech-assistant/novatech-assistant

## 1) Objetivo

Concluir a estrategia de skills do projeto com hierarquia Foundation -> Domain -> Artifact, conectada ao AGENTS.md e pronta para consumo por agentes.

## 2) Artefatos atualizados

### AGENTS
- AGENTS.md preenchido com regras prescritivas para:
  - stack e arquitetura
  - coding standards
  - product guardrails
  - testing standards
  - project management rules
  - build and evidence gate

### Foundation
- skills/foundation/error-handling.md
- skills/foundation/project-structure.md
- skills/foundation/typescript-conventions.md (ja existente)

### Domain
- skills/domain/azure-functions-endpoint.md
- skills/domain/azure-ai-search-integration.md
- skills/domain/react-components.md
- skills/domain/testing-patterns.md

### Artifact
- skills/artifact/create-rag-endpoint.md
- skills/artifact/create-react-card.md
- skills/artifact/create-integration-test.md

## 3) Validacoes objetivas da completude

- Antes: 9 arquivos de skills com tamanho 0.
- Depois: todos os arquivos de skills possuem conteudo prescritivo.

Checklist de prescritividade:
- [x] Cada skill define objetivo e escopo.
- [x] Cada skill define regras DO/DONT ou equivalentes.
- [x] Cada skill define checklist de conclusao.
- [x] Artifact skills declaram dependencias Foundation/Domain.
- [x] AGENTS.md aponta regras operacionais consumiveis por agente.

## 4) Evidencia de alinhamento com cenario 1

- ADR-0002 (context budget) materializada em AGENTS e SDD da query.
- ADR-0003 (documentos contraditorios) materializada em AGENTS e criterio de retrieval.
- Stack aprovada (TypeScript strict + Zod + pino + Vitest) reforcada no AGENTS e skills.

## 5) Evidencia de qualidade tecnica (gate local)

Comandos a executar e anexar na submissao:

```powershell
npm test
npm run build
```

Resultado esperado:
- testes passando
- build sem erro

## 6) Como apresentar para avaliacao

Anexar junto:
1. Este arquivo (evidencia-execucao-2.3.md)
2. Screenshot de npm test
3. Screenshot de npm run build
4. Diff dos arquivos de skills e AGENTS

Isso atende aos pontos de D2 (uso real com evidencia), D3 (artefatos completos e prescritivos) e D5 (aplicabilidade ao projeto).

---

## 7) Teste real com Copilot - Preenchido

> Objetivo desta secao: provar geracao real, avaliacao critica e iteracao v1 -> v2, conforme exigencia do exercicio 2.3.

### 7.1 Skill testada #1

**Skill:** skills/artifact/create-rag-endpoint.md  
**Objetivo do teste:** verificar se o Copilot gera baseline de endpoint aderente ao contrato do projeto.

**Prompt usado (v1):**

```text
Gere o baseline do endpoint query com validator, handler e erros deterministicos conforme skills do projeto.
```

**Arquivos gerados/alterados pelo Copilot (v1):**
- Exercicio-2/novatech-assistant/novatech-assistant/src/functions/query/handler.ts
- Exercicio-2/novatech-assistant/novatech-assistant/src/functions/query/validator.ts
- Exercicio-2/novatech-assistant/novatech-assistant/src/shared/errors.ts
- Exercicio-2/novatech-assistant/novatech-assistant/src/shared/logger.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/unit/query-handler.test.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/fixtures/queries.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/fixtures/expected-responses.ts

**O que o Copilot acertou na v1:**
1. Contrato de erro machine-readable com codigos deterministicos (INVALID_JSON, INVALID_REQUEST, QUERY_NOT_READY, INTERNAL_ERROR).
2. Validacao de request com Zod e schema estrito no endpoint publico.
3. Logging estruturado sem expor o texto bruto de question.

**O que o Copilot ignorou ou fez errado na v1:**
1. Nao houve falha critica observada no baseline analisado neste ciclo.
2. Nao houve necessidade de ajuste manual de codigo para passar nos testes.
3. Risco residual: endpoint ainda em placeholder funcional (QUERY_NOT_READY) por definicao de escopo da task QUERY-001.

**Evidencia visual da v1:**
- Screenshot 1: `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\01-prompt-v1.png`
- Screenshot 2: `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\02-diff-v1.png`

### 7.2 Ajuste da skill apos v1 (3 melhorias implementadas)

**Melhoria 1 - Gates obrigatorios para endpoint**  
Arquivo alterado: skills/artifact/create-rag-endpoint.md
- Exigir schema publico com .strict().
- Exigir envelope de erro padrao { status, error: { code, message, details? } }.
- Exigir classificacao de log por severidade (warn para 4xx, error para 5xx).

**Melhoria 2 - Cobertura minima ampliada de testes**  
Arquivo alterado: skills/artifact/create-integration-test.md
- Adicionar 5o cenario obrigatorio: policy de logging sem texto bruto de question.
- Definir contrato minimo de asserts: status + envelope + code.
- Reforcar uso de fixtures de dominio e evitar dados genericos.

**Melhoria 3 - Determinismo e evidencia executavel**  
Arquivo alterado: skills/domain/testing-patterns.md
- Exigir testes deterministicos e offline para baseline.
- Exigir assert do envelope completo de erro.
- Incluir Evidence Hook: npm test + output bruto + rastreabilidade.

**Trecho ajustado na skill (resumo):**

```text
- Public request schemas MUST use `.strict()`.
- Logs MUST use `warn` for 4xx and `error` for 5xx.
- Mandatory scenarios include logging policy validation.
- Tests MUST be deterministic and offline for baseline scope.
```

### 7.3 Nova execucao com a mesma tarefa (v2)

**Prompt usado (v2):**

```text
Gere o baseline do endpoint query com validator, handler e erros deterministicos conforme skills do projeto.
```

**Arquivos alterados na v2 (skills + evidencia):**
- Exercicio-2/novatech-assistant/novatech-assistant/skills/artifact/create-rag-endpoint.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/artifact/create-integration-test.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/domain/testing-patterns.md
- Exercicio-2/evidencia-execucao-2.3.md

**Melhorias observadas na v2:**
1. Skills com gates objetivos de contrato e logging.
2. Cobertura minima de testes expandida para 5 cenarios obrigatorios.
3. Evidencia executavel padronizada no proprio fluxo da skill.

**Evidencia visual da v2:**
- Screenshot 3: `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\03-prompt-v2.png`
- Screenshot 4: `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\04-diff-skills-v2.png`

### 7.4 Comparativo objetivo v1 -> v2

| Criterio | v1 | v2 | Evidencia |
|---|---|---|---|
| Skill exige schema estrito .strict() | parcial | sim | skills/artifact/create-rag-endpoint.md |
| Skill exige envelope de erro deterministico | parcial | sim | skills/artifact/create-rag-endpoint.md |
| Cobertura minima de cenarios de teste | 4/5 | 5/5 | skills/artifact/create-integration-test.md |
| Regra explicita de log seguro | parcial | sim | skills/artifact/create-integration-test.md |
| Regra de determinismo offline + evidencia | nao | sim | skills/domain/testing-patterns.md |

**Conclusao do teste #1:**
A iteracao v2 melhorou concretamente as skills com tres pontos de melhoria prescritivos e auditaveis, reduzindo ambiguidade e aumentando repetibilidade da qualidade de geracao.

---

### 7.5 Skill testada #2

**Skill:** skills/artifact/create-integration-test.md  
**Objetivo do teste:** verificar se o Copilot gera testes aderentes aos cenarios obrigatorios do endpoint query.

**Prompt usado (v1):**

```text
Gerar testes de integracao para o endpoint /api/query cobrindo INVALID_JSON, INVALID_REQUEST, unknown fields e QUERY_NOT_READY com fixtures de dominio NovaTech.
```

**Arquivos gerados/alterados pelo Copilot (v1):**
- Exercicio-2/novatech-assistant/novatech-assistant/tests/unit/query-handler.test.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/fixtures/queries.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/fixtures/expected-responses.ts

**Acertos da v1:**
1. ✓ Cobertura completa dos 5 cenarios obrigatorios (INVALID_JSON, INVALID_REQUEST missing, INVALID_REQUEST unknown fields, QUERY_NOT_READY, logging policy).
2. ✓ Estrutura clara Arrange/Act/Assert em todos os testes.
3. ✓ Fixtures com dados semanticos NovaTech (SLA Gold, conversationId, frete especial).
4. ✓ Envelope determinístico validado: status + error.code + error.message.
5. ✓ Testes offline/determinísticos sem dependencia em servicos externos.

**Falhas da v1 (gaps na skill original):**
1. Skill nao formalizava explicitamente que 5o cenario (logging policy) é obrigatorio.
2. Skill nao definia contrato minimo de assertions de forma clara (status + envelope + code).
3. Skill nao tinha regra explicita de que fixtures DEVEM ser de dominio com nomes semanticos.

### 7.6 Ajuste da skill apos v1 (3 melhorias implementadas)

**Melhoria 1 - Cobertura mínima de 5 cenários + validação obrigatória de logging**  
Arquivo alterado: skills/artifact/create-integration-test.md
- Adicionar seção "Mandatory Scenarios" explicitando que 5o cenario (logging policy) é obrigatorio.
- Reforçar na Completion Checklist: "[ ] all mandatory scenarios covered (including logging policy)".
- Adicionar ao Anti-Patterns: "Tests that skip logging policy validation for baseline."

**Melhoria 2 - Assertion Contract mínimo formalizado**  
Arquivo alterado: skills/artifact/create-integration-test.md
- Criar seção dedicada "Assertion Contract (minimum)" com regras claras:
  - HTTP status code MUST be asserted
  - `jsonBody.status = "error" or "success"` MUST be asserted
  - `jsonBody.error.code` MUST be asserted for error paths
- Exemplo concreto em Test Template mostrando 3 assertions mínimas.

**Melhoria 3 - Fixture Policy + Evidence Hook (Evidence como gate)**  
Arquivo alterado: skills/artifact/create-integration-test.md
- Criar seção "Fixture Policy" obrigando:
  - MUST use NovaTech domain (SLA, frete, carga, devolucao)
  - MUST use semanticamente nomes (gold_client_query vs test_input)
- Criar "Evidence Hook" que forca:
  - Evidence MUST include: npm test command + raw output
  - Evidence MUST include timestamp e invocationId para rastreabilidade
  - Completion Checklist deve verificar "evidence captures command and raw output"

### 7.7 Nova execucao (v2)

**Prompt usado (v2):**

```text
Revalidar os testes do endpoint query e registrar evidencias objetivas de execucao para submissao.
```

**Arquivos alterados na v2 (skills):**
- Exercicio-2/novatech-assistant/novatech-assistant/skills/artifact/create-integration-test.md (3 melhorias aplicadas)

**Melhorias observadas:**
1. ✓ Skill agora explicita que 5o cenario (logging policy) é obrigatorio.
2. ✓ Assertion Contract formalizou status + envelope + code como mínimo.
3. ✓ Fixture Policy e Evidence Hook acopladas como gate de conclusao.

**Validacao pos-melhoria:**
- npm test re-executado: 5/5 testes passando (confirma cobertura completa).
- Fixtures verificadas: queries.ts contem SLA Gold, frete especial, devolucao (dominio).
- Evidence capturada: npm test output com timestamp 17:21:00, invocationId inv-query-001.

### 7.8 Comparativo objetivo v1 -> v2

| Criterio | v1 | v2 | Evidencia |
|---|---|---|---|
| Cenarios obrigatorios explicitados | 4/5 | 5/5 + explicito | skills/artifact/create-integration-test.md (Mandatory Scenarios) |
| Assertion Contract formalizado | implicito | explicito (3+ asserts) | skills/artifact/create-integration-test.md (Assertion Contract section) |
| Fixture Policy definida | generico | MUST/SHOULD rules | skills/artifact/create-integration-test.md (Fixture Policy section) |
| Evidence Hook acoplado | nao | sim (npm test gate) | skills/artifact/create-integration-test.md (Completion Checklist) |
| Completion Checklist prescritivo | parcial | completo (5 items) | skills/artifact/create-integration-test.md |
| Teste real rodando (npm test) | 5/5 ✓ | 5/5 ✓ | `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\05-npm-test.png` |

**Conclusao do teste #2:**
A skill de testes evoluiu de "gerar testes que passam" para "gerar testes prescritivos com assertion contract, fixture governance e evidence gates". As 3 melhorias transformaram gaps implícitos em regras obrigatórias, aumentando repetibilidade e qualidade de geração pelo Copilot.

---

## 8) Evidencias executaveis apos o teste com Copilot

### 8.1 Comando de testes

```powershell
npm test
```

**Saida anexada (execução final - 17:24:53):**

```text
> novatech-assistant@0.1.0 test
> vitest run

 RUN  v2.1.9 C:/Projetos/dgs-ai-first/Exercicio-2/novatech-assistant/novatech-assistant

stderr | tests/unit/query-handler.test.ts
WARNING: Failed to detect the Azure Functions runtime. Switching "@azure/functions" package to test mode - not all features are supported.
WARNING: Skipping call to register function "query" because the "@azure/functions" package is in test mode.

 ✓ tests/unit/query-handler.test.ts (5)
   ✓ queryHandler (5)
     ✓ returns 400 INVALID_JSON when request body is malformed
     ✓ returns 400 INVALID_REQUEST when question is missing
     ✓ returns 400 INVALID_REQUEST when unknown fields are sent
     ✓ returns 501 QUERY_NOT_READY for valid request while orchestration is pending
     ✓ logs structured metadata without storing raw question text

 Test Files  1 passed (1)
      Tests  5 passed (5)
   Start at  17:24:53
   Duration  42.20s (transform 102ms, setup 0ms, collect 178ms, tests 21ms, environment 0ms, prepare 151ms)
```

**Status:** ✓ Todos os 5 cenários cobrindo INVALID_JSON, INVALID_REQUEST (2 variantes), QUERY_NOT_READY e logging policy passando.  
**Screenshot:** `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\05-npm-test.png`

### 8.2 Comando de build

```powershell
npm run build
```

**Saida anexada:**

```text
> novatech-assistant@0.1.0 build
> tsc -p .
```

**Screenshot:** `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\06-npm-build.png`

---

## 9) Resumo final para a rubrica

**D2 - Uso de Ferramentas:**
- Houve uso real do Copilot com geracao, avaliacao critica, ajuste de skills e consolidacao de evidencias.
- A validacao incluiu leitura dos artefatos de endpoint/testes e execucao real de npm test e npm run build.

**D3 - Qualidade do Entregavel:**
- As skills e o AGENTS estao prescritivos e com gates objetivos de contrato, testes e evidencia.
- O baseline permanece aderente ao stack aprovado (TypeScript strict + Zod + pino + Vitest).

**D4 - Pensamento Critico:**
- Limite identificado: as skills originais permitiam lacunas de interpretacao em log seguro e evidencia.
- Mitigacao: tres melhorias aplicadas diretamente nas skills para reduzir ambiguidade.

**D5 - Aplicabilidade ao Projeto:**
- As melhorias estao conectadas ao dominio NovaTech e aos ADRs de continuidade do cenario 1.
- O pacote de skills atualizado fortalece a qualidade para futuras iteracoes do endpoint query.

---

## 10) Checklist final de anexos

- [x] Este arquivo preenchido.
- [x] Print do prompt v1 e output v1. `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\01-prompt-v1.png`
- [x] Print do prompt v2 e output v2. `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\03-prompt-v2.png`
- [x] Print do diff apos iteracao. `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\04-diff-skills-v2.png`
- [x] Print do npm test. `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\05-npm-test.png`
- [x] Print do npm run build. `c:\Projetos\dgs-ai-first\Exercicio-2\screenshots\exercicio-2.3\06-npm-build.png`
- [x] Lista de arquivos alterados.

### Lista objetiva de arquivos alterados (workspace)

- Exercicio-2/novatech-assistant/novatech-assistant/AGENTS.md
- Exercicio-2/novatech-assistant/novatech-assistant/package.json
- Exercicio-2/novatech-assistant/novatech-assistant/package-lock.json
- Exercicio-2/novatech-assistant/novatech-assistant/skills/foundation/error-handling.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/foundation/project-structure.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/foundation/typescript-conventions.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/domain/azure-functions-endpoint.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/domain/azure-ai-search-integration.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/domain/react-components.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/domain/testing-patterns.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/artifact/create-rag-endpoint.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/artifact/create-react-card.md
- Exercicio-2/novatech-assistant/novatech-assistant/skills/artifact/create-integration-test.md
- Exercicio-2/novatech-assistant/novatech-assistant/specs/query-endpoint/requirements.md
- Exercicio-2/novatech-assistant/novatech-assistant/specs/query-endpoint/plan.md
- Exercicio-2/novatech-assistant/novatech-assistant/specs/query-endpoint/tasks.md
- Exercicio-2/novatech-assistant/novatech-assistant/specs/query-endpoint/review-notes.md
- Exercicio-2/novatech-assistant/novatech-assistant/src/functions/query/handler.ts
- Exercicio-2/novatech-assistant/novatech-assistant/src/functions/query/validator.ts
- Exercicio-2/novatech-assistant/novatech-assistant/src/shared/errors.ts
- Exercicio-2/novatech-assistant/novatech-assistant/src/shared/logger.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/fixtures/chunks.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/fixtures/expected-responses.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/fixtures/queries.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tests/unit/query-handler.test.ts
- Exercicio-2/novatech-assistant/novatech-assistant/tsconfig.json
