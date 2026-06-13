# Evidencias de Execucao - Exercicio 2.2 (Desenvolvedor)

Data: 12/06/2026  
Projeto: novatech-assistant  
Diretorio de execucao: Exercicio-2/novatech-assistant/novatech-assistant

## 1) Evidencia de testes automatizados

Comando executado:

```powershell
npm test
```

Saida:

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
   Duration  44.04s
```

Interpretacao:
- VC-001, VC-002, VC-003 e VC-004 cobertos por testes do handler.
- VC-005 coberto por teste de policy de logging.

## 2) Evidencia de compilacao

Comando executado:

```powershell
npm run build
```

Saida:

```text
> novatech-assistant@0.1.0 build
> tsc -p .
```

Interpretacao:
- Baseline do endpoint compila com TypeScript strict sem erros de build.

## 3) Evidencia de artefatos atualizados (SDD + codigo + testes)

Arquivos alterados para atender aos pontos de melhoria da avaliacao:
- specs/query-endpoint/requirements.md
- specs/query-endpoint/plan.md
- specs/query-endpoint/tasks.md
- src/functions/query/validator.ts
- src/functions/query/handler.ts
- tests/unit/query-handler.test.ts
- tests/fixtures/queries.ts
- tests/fixtures/expected-responses.ts
- tests/fixtures/chunks.ts

## 4) Rastreabilidade para cenario 1

Rastreabilidade registrada em:
- specs/query-endpoint/requirements.md (ADRs e continuidade arquitetural)
- specs/query-endpoint/plan.md (matriz de traceability)
- specs/query-endpoint/tasks.md (Architectural Traceability)

ADRs referenciadas:
- ADR-0002: context budget (materializado em QUERY-005)
- ADR-0003: documentos contraditorios (materializado em QUERY-004)

## 5) Evidencia visual sugerida para anexar

Para fortalecer avaliacao humana, anexar:
1. Screenshot do terminal com `npm test` passando.
2. Screenshot do terminal com `npm run build` sem erro.
3. Screenshot do diff dos arquivos acima em staged/unstaged (prova de iteracao).
4. (Opcional) Screenshot do arquivo `review-notes.md` com pontos tratados no codigo.
