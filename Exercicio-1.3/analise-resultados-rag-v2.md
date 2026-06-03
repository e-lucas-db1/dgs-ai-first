# Análise de Resultados — Pipeline RAG NovaTech v2

**Data de execução:** 03/06/2026  
**Modelo de embeddings:** paraphrase-multilingual-MiniLM-L12-v2  
**N_RESULTS:** 8 | **Melhorias:** M1 (N=8) + M2 (multilíngue) + M3 (expansão geo)  

---

## Resultado geral

```
SUMÁRIO: 5/10 queries passaram | 8/14 chunks obrigatórios encontrados (57%)
```

| Status | Queries |
|--------|---------|
| ✓ PASS (5) | Posso devolver carga perigosa?, Qual o SLA do cliente Platinum?, Frete para 300kg para Salvador?, O que acontece com carga danificada?, Qual o multiplicador para o Sudeste? |
| ✗ FAIL (5) | Qual o prazo de devolução?, Qual o SLA do cliente Gold?, Frete para 600kg para Manaus?, Carga perigosa com frete expresso?, Prazo de devolução, carga perigosa e frete especial |

---

## Resultados por query

### Query 1 — "Qual o prazo de devolução?" — ✗ FAIL

**Gabarito Anexo B:**
- DEVE: POL-001-A — ✓ encontrado
- DEVE: POL-001-B — ✗ não encontrado
- PODE: POL-001-C — — não encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5627 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 3. Prazo de entrega para frete especial | ✗ Ruído |
| 2 | 0.5351 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.1. Prazo geral | **✓ DEVE** |
| 3 | 0.5307 | PROC-042-frete-especial-v1.md (v1.0) | 3. Prazo de entrega para frete especial | ✗ Ruído |
| 4 | 0.4556 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 5. Medição e reportes | ✗ Ruído |
| 5 | 0.4525 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 41 — "Qual a diferença entre SLA de resposta e SLA de resolução?" | ✗ Ruído |
| 6 | 0.4386 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.5. Custos de devolução | ✗ Ruído |
| 7 | 0.4335 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 32 — "Pode enviar carga perigosa com frete expresso?" | ✗ Ruído |
| 8 | 0.4101 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | ✗ Ruído |

**Chunks obrigatórios não encontrados:**
- `POL-001-B` (fonte: `POL-001`, snippets: ['NÃO são elegíveis', 'classes 1 a 6 da ANTT'])

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 3. Prazo de entrega para frete especial | Score: 0.563 ---
O prazo de entrega para frete especial é calculado como o prazo padrão da rota + 3 dias úteis adicionais para manuseio e roteirização de carga pesada (anteriormente era + 2 dias na versão anterior).

--- Trecho 2 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.1. Prazo geral | Score: 0.535 ---
O cliente pode solicitar a devolução de mercadorias em até 7 (sete) dias úteis após a data de recebimento confirmada no sistema de tracking. A contagem de dias úteis exclui sábados, domingos e feriados nacionais.

--- Trecho 3 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 3. Prazo de entrega para frete especial | Score: 0.531 ---
O prazo de entrega para frete especial é calculado como o prazo padrão da rota + 2 dias úteis adicionais para manuseio de carga pesada.

--- Trecho 4 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 5. Medição e reportes | Score: 0.456 ---
Os SLAs são medidos pelo sistema de chamados (Azure DevOps) a partir do timestamp de abertura do chamado. O relógio de SLA pausa fora do horário comercial (08h-18h, dias úteis) para chamados gerais, mas não pausa para incidentes críticos de clientes Gold.

--- Trecho 5 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 41 — "Qual a diferença entre SLA de resposta e SLA de resolução?" | Score: 0.453 ---
Resposta é quando a gente dá o primeiro retorno ao cliente (mesmo que seja 'estamos verificando'). Resolução é quando o problema é efetivamente resolvido. O Gold tem 2h de resposta e 24h de resolução. Silver é 4h e 48h. Standard é 8h e 72h. Para incidentes críticos, os prazos são menores — veja a tabela SLA-2024.

--- Trecho 6 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.5. Custos de devolução | Score: 0.439 ---
- Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente.
- Desistência do cliente (carga correta, sem defeito): o custo do frete reverso é do cliente, calculado com os mesmos multiplicadores do frete original.
- Prazo expirado (solicitação após 7 dias úteis): não elegível para devolução padrão. Encaminhar ao Comercial para negociação caso a caso.

--- Trecho 7 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 32 — "Pode enviar carga perigosa com frete expresso?" | Score: 0.433 ---
Sim, mas precisa de autorização do Compliance e a documentação ANTT tem que estar atualizada. Na prática, demora uns 2 dias para conseguir a autorização, então o 'expresso' acaba não sendo tão expresso. Avise o cliente sobre isso.

--- Trecho 8 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.410 ---
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Qual o prazo de devolução?

──────────────────────────────────────────────────────────────────────
Com base nos trechos recuperados, aqui está a resposta que o assistente RAG deveria gerar:

Prazo de devolução: 7 dias úteis

Conforme a POL-001-politica-devolucao.md (v3.1), o cliente pode solicitar a devolução em até 7 (sete) dias úteis após a data de recebimento confirmada no sistema de tracking. A contagem exclui sábados, domingos e feriados nacionais.

Sobre os custos (mesma fonte, seção 3.5):

Defeito/erro da NovaTech (carga errada ou avaria em trânsito): devolução sem custo.
Desistência do cliente (carga correta, sem defeito): frete reverso por conta do cliente.
Prazo expirado (após 7 dias úteis): não elegível para devolução padrão — encaminhar ao Comercial para negociação caso a caso.
Nota: O Trecho 8 (FAQ-atendimento.md — versão não controlada) menciona um processo diferenciado para carga danificada em trânsito (48h para registrar ocorrência, encaminhar para sinistros@novatech.com.br). Por se tratar de fonte informal, recomendo confirmar o procedimento na documentação normativa correspondente.

O RAG performou bem nessa pergunta: recuperou os dois trechos mais relevantes da POL-001 com scores razoáveis (0.535 e 0.439) e o contexto era suficiente para uma resposta completa e correta.
```

</details>

---

### Query 2 — "Posso devolver carga perigosa?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: POL-001-B — ✓ encontrado
- PODE: FAQ-03 — ✓ encontrado
- PODE: POL-001-A — — não encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5180 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | ✗ Ruído |
| 2 | 0.5058 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 3. Definição de incidente crítico | ✗ Ruído |
| 3 | 0.5023 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 4. Condições especiais | ✗ Ruído |
| 4 | 0.4521 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.5. Custos de devolução | ✗ Ruído |
| 5 | 0.4372 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | ✗ Ruído |
| 6 | 0.4350 | PROC-042-frete-especial-v1.md (v1.0) | 4. Condições especiais | ✗ Ruído |
| 7 | 0.4082 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.2. Exceções ao prazo geral | **✓ DEVE** |
| 8 | 0.3406 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 3 — "Cliente perguntou se pode devolver carga perigosa. O que respondo?" | ✓ PODE |

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.518 ---
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

--- Trecho 2 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 3. Definição de incidente crítico | Score: 0.506 ---
Um incidente é classificado como crítico quando atende a pelo menos um dos seguintes critérios:

- Carga com valor declarado acima de R$ 100.000 está com status desconhecido há mais de 6 horas.
- Carga perigosa com qualquer irregularidade de documentação ou rastreamento.
- Mais de 5 chamados do mesmo cliente nas últimas 24 horas sobre o mesmo problema.
- Qualquer situação que envolva risco à segurança de pessoas.

--- Trecho 3 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.502 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 4 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.5. Custos de devolução | Score: 0.452 ---
- Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente.
- Desistência do cliente (carga correta, sem defeito): o custo do frete reverso é do cliente, calculado com os mesmos multiplicadores do frete original.
- Prazo expirado (solicitação após 7 dias úteis): não elegível para devolução padrão. Encaminhar ao Comercial para negociação caso a caso.

--- Trecho 5 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.437 ---
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

--- Trecho 6 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 4. Condições especiais | Score: 0.435 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas).
- Descontos de volume (mais de 10 fretes especiais/mês para o mesmo cliente) devem ser negociados pelo Comercial e registrados em aditivo contratual.

--- Trecho 7 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.2. Exceções ao prazo geral | Score: 0.408 ---
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1), gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4), oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa especificada na nota fiscal por mais de 30 minutos contínuos, conforme registro do sensor IoT).
- Cargas com lacre de segurança violado, salvo quando a violação for documentada no ato de entrega com assinatura do motorista e do recebedor.

Para essas categorias, o cliente deve entrar em

--- Trecho 8 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 3 — "Cliente perguntou se pode devolver carga perigosa. O que respondo?" | Score: 0.341 ---
Na prática, a gente orienta o cliente a ligar no ramal 4500 (Gestão de Riscos). Oficialmente não pode pelo processo padrão, mas já tiveram casos em que o pessoal de Riscos autorizou exceção. Então não diga que é impossível — diga que precisa de tratamento especial.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Posso devolver carga perigosa?

──────────────────────────────────────────────────────────────────────
Resposta do assistente NovaTech:

Não, carga perigosa não é elegível para devolução pelo processo padrão.

Conforme a POL-001-politica-devolucao.md (v3.1, seção 3.2) — fonte normativa — as seguintes cargas estão explicitamente excluídas do processo padrão de devolução:

Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Resolução ANTT nº 5.947/2021): explosivos, gases, líquidos inflamáveis, sólidos inflamáveis, oxidantes/peróxidos e substâncias tóxicas/infectantes.

Ação obrigatória: Escale imediatamente para o ramal 4500 (Gestão de Riscos), conforme regra do sistema.

Nota sobre a fonte informal (FAQ-atendimento, Item 3 — versão não controlada):

O FAQ menciona que casos excepcionais já foram autorizados pela equipe de Riscos. Contudo, por ser fonte não controlada, não utilize essa informação como garantia — a decisão final cabe exclusivamente ao ramal 4500. Confirme o procedimento aplicável na documentação normativa (POL-001).

Por que essa query passou (PASS) no gabarito com scores baixos:

O chunk obrigatório POL-001-B foi recuperado em posição #7 (score 0.408) e o FAQ-03 em posição #8 (score 0.341). O pipeline encontrou os dois chunks necessários apesar dos scores modestos — o ruído nos primeiros 6 posições não impediu a cobertura, mas a posição tardia é um sinal de alerta: qualquer redução em N_RESULTS abaixo de 7 faria essa query falhar.
```

</details>

---

### Query 3 — "Qual o SLA do cliente Gold?" — ✗ FAIL

**Gabarito Anexo B:**
- DEVE: SLA-2024-B — ✗ não encontrado
- PODE: SLA-2024-A — ✓ encontrado
- PODE: SLA-2024-C — — não encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5139 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 15 — "Cliente diz que é Platinum. Existe esse tier?" | ✗ Ruído |
| 2 | 0.4901 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 41 — "Qual a diferença entre SLA de resposta e SLA de resolução?" | ✗ Ruído |
| 3 | 0.4422 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 5. Medição e reportes | ✗ Ruído |
| 4 | 0.4189 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 4. Penalidades por descumprimento | ✗ Ruído |
| 5 | 0.3775 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 27 — "O tracking mostra 'em trânsito' há 5 dias. O que faço?" | ✗ Ruído |
| 6 | 0.3541 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 1. Classificação de clientes | ✓ PODE |
| 7 | 0.3464 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.3. Procedimento de devolução | ✗ Ruído |
| 8 | 0.2935 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 45 — "O cliente quer desconto no frete. Posso dar?" | ✗ Ruído |

**Chunks obrigatórios não encontrados:**
- `SLA-2024-B` (fonte: `SLA-2024`, snippets: ['Gold', '2h úteis', '24h úteis'])

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 15 — "Cliente diz que é Platinum. Existe esse tier?" | Score: 0.514 ---
Não existe tier Platinum na NovaTech. Às vezes o cliente confunde com outra transportadora ou com o programa de fidelidade antigo que foi descontinuado em 2022. Oriente que nossos tiers são Gold, Silver e Standard e peça o número do contrato para verificar.

--- Trecho 2 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 41 — "Qual a diferença entre SLA de resposta e SLA de resolução?" | Score: 0.490 ---
Resposta é quando a gente dá o primeiro retorno ao cliente (mesmo que seja 'estamos verificando'). Resolução é quando o problema é efetivamente resolvido. O Gold tem 2h de resposta e 24h de resolução. Silver é 4h e 48h. Standard é 8h e 72h. Para incidentes críticos, os prazos são menores — veja a tabela SLA-2024.

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 5. Medição e reportes | Score: 0.442 ---
Os SLAs são medidos pelo sistema de chamados (Azure DevOps) a partir do timestamp de abertura do chamado. O relógio de SLA pausa fora do horário comercial (08h-18h, dias úteis) para chamados gerais, mas não pausa para incidentes críticos de clientes Gold.

--- Trecho 4 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 4. Penalidades por descumprimento | Score: 0.419 ---
- Primeira violação de SLA no mês: registro interno, sem impacto contratual.
- Segunda violação no mesmo mês: crédito de 5% sobre o valor do frete do chamado afetado.
- Terceira violação ou mais no mesmo mês: crédito de 10% + reunião obrigatória com o gerente de conta (Gold) ou gerente de operações (Silver/Standard).

--- Trecho 5 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 27 — "O tracking mostra 'em trânsito' há 5 dias. O que faço?" | Score: 0.378 ---
Depende da rota. Rotas para o Norte podem levar até 10 dias úteis. Para Sul/Sudeste, mais de 3 dias parado é estranho. Abra um chamado de rastreamento e classifique como prioridade alta se for Gold ou se o valor da carga for acima de R$ 50.000.

--- Trecho 6 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.354 ---
A NovaTech classifica seus clientes em 3 (três) tiers com base no volume mensal de operações e no valor do contrato:

| Tier | Critério de elegibilidade | Revisão |
|------|--------------------------|---------|
| Gold | Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais clientes | Anual |

Nota: Não existem outros tiers além dos três listados acima. Solicitações de SLA diferenciado fora desses tiers devem ser encaminhadas ao Comercial para análise de viabilidade.

--- Trecho 7 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.3. Procedimento de devolução | Score: 0.346 ---
1. O cliente abre chamado no Portal do Cliente (portal.novatech.com.br), selecionando a categoria "Devolução de Mercadoria".
2. O chamado deve incluir: número do CT-e (Conhecimento de Transporte Eletrônico), fotos da mercadoria no estado atual (mínimo 3 fotos: embalagem externa, etiqueta de identificação, e conteúdo), e motivo da devolução.
3. O time de atendimento tem 4 horas úteis para triagem do chamado (verificar elegibilidade, documentação e prazo).
4. Se elegível, a coleta reversa é agendada em até 2 dias úteis após aprovação.
5. O reembolso ou crédito é processado em até 5 dias úteis após o recebimento da mercadoria devolvida no centro de distribuição.

--- Trecho 8 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 45 — "O cliente quer desconto no frete. Posso dar?" | Score: 0.293 ---
Atendente não tem autonomia para dar desconto. Para clientes com mais de 10 fretes especiais por mês, existe desconto automático na tabela (veja PROC-042). Para outros casos, encaminhe ao Comercial com justificativa.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Qual o SLA do cliente Gold?

──────────────────────────────────────────────────────────────────────
SLA do cliente Gold — NovaTech Logística

Com base na documentação disponível:

Prazos gerais (Fonte: FAQ-atendimento.md — versão não controlada, Trecho 2):

Resposta: 2 horas úteis
Resolução: 24 horas úteis
Atenção: como essa informação vem do FAQ (fonte não controlada), confirme os valores exatos na documentação normativa SLA-2024-tabela-sla-clientes.md.

Comportamento do relógio de SLA (Fonte: SLA-2024-tabela-sla-clientes.md v2024.1, Trecho 3):

Para chamados gerais: o relógio pausa fora do horário comercial (08h–18h, dias úteis).
Para incidentes críticos Gold: o relógio não pausa — corre 24/7.
Para incidentes críticos, os prazos são menores do que os gerais — a tabela completa está no documento SLA-2024.

Por que essa resposta está correta:

Usou ambas as fontes disponíveis (FAQ + SLA normativo)
Sinalizou a fonte informal (FAQ) conforme regra 6
Não inventou valores para incidentes críticos (não estavam nos trechos recuperados)
Complementou com a informação normativa sobre o clock behavior do Gold
O único gap é que os SLAs de incidentes críticos Gold não foram recuperados — o retrieval trouxe o Trecho 3 que menciona o comportamento do relógio, mas não os valores numéricos de prazos críticos. Isso é um ponto de melhoria no chunking/indexação do SLA-2024.
```

</details>

---

### Query 4 — "Qual o SLA do cliente Platinum?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: SLA-2024-A — ✓ encontrado
- PODE: FAQ-15 — ✓ encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.6720 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 15 — "Cliente diz que é Platinum. Existe esse tier?" | ✓ PODE |
| 2 | 0.4249 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 1. Classificação de clientes | **✓ DEVE** |
| 3 | 0.3543 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 41 — "Qual a diferença entre SLA de resposta e SLA de resolução?" | ✗ Ruído |
| 4 | 0.3541 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 5. Medição e reportes | ✗ Ruído |
| 5 | 0.3471 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 8 — "Como funciona o frete especial?" | ✗ Ruído |
| 6 | 0.3429 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 4. Condições especiais | ✗ Ruído |
| 7 | 0.3300 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.3. Procedimento de devolução | ✗ Ruído |
| 8 | 0.3157 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | ✗ Ruído |

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 15 — "Cliente diz que é Platinum. Existe esse tier?" | Score: 0.672 ---
Não existe tier Platinum na NovaTech. Às vezes o cliente confunde com outra transportadora ou com o programa de fidelidade antigo que foi descontinuado em 2022. Oriente que nossos tiers são Gold, Silver e Standard e peça o número do contrato para verificar.

--- Trecho 2 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.425 ---
A NovaTech classifica seus clientes em 3 (três) tiers com base no volume mensal de operações e no valor do contrato:

| Tier | Critério de elegibilidade | Revisão |
|------|--------------------------|---------|
| Gold | Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais clientes | Anual |

Nota: Não existem outros tiers além dos três listados acima. Solicitações de SLA diferenciado fora desses tiers devem ser encaminhadas ao Comercial para análise de viabilidade.

--- Trecho 3 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 41 — "Qual a diferença entre SLA de resposta e SLA de resolução?" | Score: 0.354 ---
Resposta é quando a gente dá o primeiro retorno ao cliente (mesmo que seja 'estamos verificando'). Resolução é quando o problema é efetivamente resolvido. O Gold tem 2h de resposta e 24h de resolução. Silver é 4h e 48h. Standard é 8h e 72h. Para incidentes críticos, os prazos são menores — veja a tabela SLA-2024.

--- Trecho 4 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 5. Medição e reportes | Score: 0.354 ---
Os SLAs são medidos pelo sistema de chamados (Azure DevOps) a partir do timestamp de abertura do chamado. O relógio de SLA pausa fora do horário comercial (08h-18h, dias úteis) para chamados gerais, mas não pausa para incidentes críticos de clientes Gold.

--- Trecho 5 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 8 — "Como funciona o frete especial?" | Score: 0.347 ---
Acima de 500kg, aplica a tabela de multiplicadores por região. Cuidado: existem duas versões da PROC-042. A mais recente tem multiplicadores mais altos. Na dúvida, use a mais recente (v2), mas se o cliente reclamar do valor, pode ser que o contrato dele ainda esteja na tabela antiga.

--- Trecho 6 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.343 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 7 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.3. Procedimento de devolução | Score: 0.330 ---
1. O cliente abre chamado no Portal do Cliente (portal.novatech.com.br), selecionando a categoria "Devolução de Mercadoria".
2. O chamado deve incluir: número do CT-e (Conhecimento de Transporte Eletrônico), fotos da mercadoria no estado atual (mínimo 3 fotos: embalagem externa, etiqueta de identificação, e conteúdo), e motivo da devolução.
3. O time de atendimento tem 4 horas úteis para triagem do chamado (verificar elegibilidade, documentação e prazo).
4. Se elegível, a coleta reversa é agendada em até 2 dias úteis após aprovação.
5. O reembolso ou crédito é processado em até 5 dias úteis após o recebimento da mercadoria devolvida no centro de distribuição.

--- Trecho 8 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.316 ---
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Qual o SLA do cliente Platinum?

──────────────────────────────────────────────────────────────────────
Resposta do Assistente:

O tier Platinum não existe na NovaTech Logística. A NovaTech possui apenas três tiers: Gold, Silver e Standard (conforme SLA-2024-tabela-sla-clientes.md, versão 2024.1).

Possivelmente o cliente está confundindo com outra transportadora ou com um programa de fidelidade antigo descontinuado em 2022 (FAQ-atendimento.md, Item 15).

Oriente o cliente sobre os SLAs reais conforme o tier correto dele:

Tier	Resposta	Resolução
Gold	2h	24h
Silver	4h	48h
Standard	8h	72h
Para identificar o tier correto, solicite o número do contrato e verifique no sistema.

Nota: Os dados de SLA do FAQ (fonte não controlada) devem ser confirmados na tabela normativa SLA-2024.

Por que essa resposta está correta sob as regras RAG:

Aplica a regra 5 (corrigir tier inexistente)
Usa exclusivamente os trechos 1, 2 e 3 do contexto
Não inventa SLA para Platinum
Sinaliza a fonte informal do FAQ (regra 6)
Score mais alto (0.672) foi justamente o trecho sobre Platinum — a recuperação foi precisa
```

</details>

---

### Query 5 — "Frete para 600kg para Manaus?" — ✗ FAIL

> **Expansão geográfica aplicada:** `Frete para 600kg para Manaus?` → `Frete para 600kg para Manaus? (Norte)`

**Gabarito Anexo B:**
- DEVE: PROC-042v2-B — ✗ não encontrado
- DEVE: PROC-042v2-A — ✓ encontrado
- PODE: PROC-042-B — — não encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.4750 | PROC-042-frete-especial-v1.md (v1.0) | 2. Fórmula de cálculo | ✗ Ruído |
| 2 | 0.4682 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 2. Fórmula de cálculo | **✓ DEVE** |
| 3 | 0.4322 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 4. Condições especiais | **✓ DEVE** |
| 4 | 0.4299 | PROC-042-frete-especial-v1.md (v1.0) | 1. Objetivo | ✗ Ruído |
| 5 | 0.4275 | PROC-042-frete-especial-v1.md (v1.0) | 4. Condições especiais | ✗ Ruído |
| 6 | 0.3321 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 1. Classificação de clientes | ✗ Ruído |
| 7 | 0.3061 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 1. Objetivo | ✗ Ruído |
| 8 | 0.2867 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | ✗ Ruído |

**Chunks obrigatórios não encontrados:**
- `PROC-042v2-B` (fonte: `PROC-042-v2`, snippets: ['Norte', '1.8'])

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 2. Fórmula de cálculo | Score: 0.475 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.2 para cargas de 1.001kg a 3.000kg; 1.5 para cargas acima de 3.000kg.

--- Trecho 2 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 2. Fórmula de cálculo | Score: 0.468 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.15 para cargas de 1.001kg a 3.000kg; 1.4 para cargas acima de 3.000kg.

--- Trecho 3 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.432 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 4 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 1. Objetivo | Score: 0.430 ---
Definir a fórmula e os parâmetros para cálculo de frete especial aplicável a cargas com peso acima de 500kg.

--- Trecho 5 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 4. Condições especiais | Score: 0.427 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas).
- Descontos de volume (mais de 10 fretes especiais/mês para o mesmo cliente) devem ser negociados pelo Comercial e registrados em aditivo contratual.

--- Trecho 6 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 1. Classificação de clientes | Score: 0.332 ---
A NovaTech classifica seus clientes em 3 (três) tiers com base no volume mensal de operações e no valor do contrato:

| Tier | Critério de elegibilidade | Revisão |
|------|--------------------------|---------|
| Gold | Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês | Semestral |
| Silver | Contrato anual entre R$ 100.000 e R$ 500.000 OU entre 50 e 200 operações/mês | Semestral |
| Standard | Todos os demais clientes | Anual |

Nota: Não existem outros tiers além dos três listados acima. Solicitações de SLA diferenciado fora desses tiers devem ser encaminhadas ao Comercial para análise de viabilidade.

--- Trecho 7 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 1. Objetivo | Score: 0.306 ---
Definir a fórmula e os parâmetros atualizados para cálculo de frete especial aplicável a cargas com peso acima de 500kg. Os multiplicadores foram revisados para refletir os custos operacionais atualizados de cada região.

--- Trecho 8 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.287 ---
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Frete para 600kg para Manaus?

──────────────────────────────────────────────────────────────────────
Resposta do Assistente:

Para 600kg com destino a Manaus, a carga se enquadra em frete especial (acima de 500kg).

Atenção — contradição detectada: Existem duas versões da PROC-042 no contexto. Para a faixa de 600kg (500–1.000kg), ambas concordam:

Fórmula aplicável (PROC-042 v2.0 — versão mais recente):

Valor do frete = Valor base × Multiplicador regional × Fator de peso (1.0)

O que os trechos confirmam:

Fator de peso para 600kg = 1.0 (ambas as versões concordam nesta faixa)
O que está ausente do contexto recuperado:

Valor base: definido na tabela mensal de fretes — não está nos trechos
Multiplicador regional de Manaus: referenciado na seção 2.1 da PROC-042, mas essa seção não foi recuperada
Não encontrei essas informações na documentação disponível.

Para fechar o valor, consulte a tabela mensal de fretes e o multiplicador regional da seção 2.1 da PROC-042 v2.

Por que esta resposta é correta:

Sinaliza a contradição entre v1 e v2 (regra 3), mas mostra que para esta faixa específica não há impacto prático
Usa a versão mais recente (v2) como mandatado
Aplica o fallback apenas para os dados realmente ausentes, não no meio do raciocínio — diferente da resposta problemática da mensagem anterior
```

</details>

---

### Query 6 — "Frete para 300kg para Salvador?" — ✓ PASS

> **Expansão geográfica aplicada:** `Frete para 300kg para Salvador?` → `Frete para 300kg para Salvador? (Nordeste)`

**Gabarito Anexo B:**
- DEVE: Nenhum (ausência de cobertura é o comportamento correto)
- PODE: PROC-042v2-B — ✓ encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.4667 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 4. Condições especiais | ✓ PODE |
| 2 | 0.4344 | PROC-042-frete-especial-v1.md (v1.0) | 2. Fórmula de cálculo | ✗ Ruído |
| 3 | 0.4191 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 2. Fórmula de cálculo | ✓ PODE |
| 4 | 0.4130 | PROC-042-frete-especial-v1.md (v1.0) | 4. Condições especiais | ✗ Ruído |
| 5 | 0.3821 | PROC-042-frete-especial-v1.md (v1.0) | 1. Objetivo | ✗ Ruído |
| 6 | 0.3105 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 27 — "O tracking mostra 'em trânsito' há 5 dias. O que faço?" | ✗ Ruído |
| 7 | 0.3078 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 1. Objetivo | ✓ PODE |
| 8 | 0.2962 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 8 — "Como funciona o frete especial?" | ✗ Ruído |

> **Comportamento correto:** query sem cobertura retornou scores baixos.

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.467 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 2 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 2. Fórmula de cálculo | Score: 0.434 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.2 para cargas de 1.001kg a 3.000kg; 1.5 para cargas acima de 3.000kg.

--- Trecho 3 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 2. Fórmula de cálculo | Score: 0.419 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.15 para cargas de 1.001kg a 3.000kg; 1.4 para cargas acima de 3.000kg.

--- Trecho 4 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 4. Condições especiais | Score: 0.413 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas).
- Descontos de volume (mais de 10 fretes especiais/mês para o mesmo cliente) devem ser negociados pelo Comercial e registrados em aditivo contratual.

--- Trecho 5 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 1. Objetivo | Score: 0.382 ---
Definir a fórmula e os parâmetros para cálculo de frete especial aplicável a cargas com peso acima de 500kg.

--- Trecho 6 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 27 — "O tracking mostra 'em trânsito' há 5 dias. O que faço?" | Score: 0.310 ---
Depende da rota. Rotas para o Norte podem levar até 10 dias úteis. Para Sul/Sudeste, mais de 3 dias parado é estranho. Abra um chamado de rastreamento e classifique como prioridade alta se for Gold ou se o valor da carga for acima de R$ 50.000.

--- Trecho 7 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 1. Objetivo | Score: 0.308 ---
Definir a fórmula e os parâmetros atualizados para cálculo de frete especial aplicável a cargas com peso acima de 500kg. Os multiplicadores foram revisados para refletir os custos operacionais atualizados de cada região.

--- Trecho 8 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 8 — "Como funciona o frete especial?" | Score: 0.296 ---
Acima de 500kg, aplica a tabela de multiplicadores por região. Cuidado: existem duas versões da PROC-042. A mais recente tem multiplicadores mais altos. Na dúvida, use a mais recente (v2), mas se o cliente reclamar do valor, pode ser que o contrato dele ainda esteja na tabela antiga.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Frete para 300kg para Salvador?

──────────────────────────────────────────────────────────────────────
Frete para 300kg para Salvador não se enquadra no procedimento de frete especial.

Conforme PROC-042 (v1 e v2, seção 1 — Objetivo), a tabela de frete especial é aplicável somente a cargas com peso acima de 500kg. Uma carga de 300kg está abaixo desse limite.

Para o cálculo do frete regular (abaixo de 500kg) com destino a Salvador, não encontrei essa informação na documentação disponível nos trechos fornecidos. Recomendo consultar a tabela mensal de fretes padrão ou acionar o setor responsável pelo frete convencional.
```

</details>

---

### Query 7 — "O que acontece com carga danificada?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: FAQ-38 — ✓ encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.5022 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.2. Exceções ao prazo geral | ✗ Ruído |
| 2 | 0.4699 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | **✓ DEVE** |
| 3 | 0.4429 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 4. Condições especiais | ✗ Ruído |
| 4 | 0.4359 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | ✗ Ruído |
| 5 | 0.3972 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 3. Definição de incidente crítico | ✗ Ruído |
| 6 | 0.3972 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 1. Objetivo | ✗ Ruído |
| 7 | 0.3786 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.5. Custos de devolução | ✗ Ruído |
| 8 | 0.3593 | PROC-042-frete-especial-v1.md (v1.0) | 1. Objetivo | ✗ Ruído |

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.2. Exceções ao prazo geral | Score: 0.502 ---
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1), gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4), oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa especificada na nota fiscal por mais de 30 minutos contínuos, conforme registro do sensor IoT).
- Cargas com lacre de segurança violado, salvo quando a violação for documentada no ato de entrega com assinatura do motorista e do recebedor.

Para essas categorias, o cliente deve entrar em

--- Trecho 2 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.470 ---
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

--- Trecho 3 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.443 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 4 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.436 ---
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

--- Trecho 5 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 3. Definição de incidente crítico | Score: 0.397 ---
Um incidente é classificado como crítico quando atende a pelo menos um dos seguintes critérios:

- Carga com valor declarado acima de R$ 100.000 está com status desconhecido há mais de 6 horas.
- Carga perigosa com qualquer irregularidade de documentação ou rastreamento.
- Mais de 5 chamados do mesmo cliente nas últimas 24 horas sobre o mesmo problema.
- Qualquer situação que envolva risco à segurança de pessoas.

--- Trecho 6 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 1. Objetivo | Score: 0.397 ---
Definir a fórmula e os parâmetros atualizados para cálculo de frete especial aplicável a cargas com peso acima de 500kg. Os multiplicadores foram revisados para refletir os custos operacionais atualizados de cada região.

--- Trecho 7 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.5. Custos de devolução | Score: 0.379 ---
- Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente.
- Desistência do cliente (carga correta, sem defeito): o custo do frete reverso é do cliente, calculado com os mesmos multiplicadores do frete original.
- Prazo expirado (solicitação após 7 dias úteis): não elegível para devolução padrão. Encaminhar ao Comercial para negociação caso a caso.

--- Trecho 8 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 1. Objetivo | Score: 0.359 ---
Definir a fórmula e os parâmetros para cálculo de frete especial aplicável a cargas com peso acima de 500kg.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
O que acontece com carga danificada?

──────────────────────────────────────────────────────────────────────
Carga Danificada em Trânsito — NovaTech Logística

O processo para carga danificada é diferente do processo padrão de devolução. Com base nos trechos disponíveis:

Procedimento (Fonte: FAQ-atendimento.md, Item 38 — versão não controlada):

O cliente deve registrar a ocorrência em até 48h após o recebimento
O registro deve incluir fotos e laudo, se possível
A NovaTech investiga; se comprovada responsabilidade da empresa, o reembolso é integral
O caso não segue pelo atendimento normal — deve ser encaminhado para: sinistros@novatech.com.br (equipe Jurídico)
Confirmação normativa (POL-001-politica-devolucao.md v3.1, seção 3.5):

"Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente."

Nota sobre fonte: O procedimento detalhado (48h, fotos, laudo, e-mail de sinistros) vem do FAQ — fonte não controlada. Confirme o fluxo completo na documentação normativa de sinistros, pois o POL-001 confirma apenas a isenção de custo, não os passos do processo.
```

</details>

---

### Query 8 — "Carga perigosa com frete expresso?" — ✗ FAIL

**Gabarito Anexo B:**
- DEVE: FAQ-32 — ✗ não encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.6107 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | ✗ Ruído |
| 2 | 0.5773 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 4. Condições especiais | ✗ Ruído |
| 3 | 0.5682 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 3. Definição de incidente crítico | ✗ Ruído |
| 4 | 0.5510 | PROC-042-frete-especial-v1.md (v1.0) | 4. Condições especiais | ✗ Ruído |
| 5 | 0.5064 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.2. Exceções ao prazo geral | ✗ Ruído |
| 6 | 0.4112 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | ✗ Ruído |
| 7 | 0.3610 | PROC-042-frete-especial-v1.md (v1.0) | 3. Prazo de entrega para frete especial | ✗ Ruído |
| 8 | 0.3572 | POL-001-politica-devolucao.md (v3.1) | 2. Escopo | ✗ Ruído |

**Chunks obrigatórios não encontrados:**
- `FAQ-32` (fonte: `FAQ-atendimento`, snippets: ['autorização do Compliance', 'documentação ANTT'])

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.611 ---
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

--- Trecho 2 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.577 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 3. Definição de incidente crítico | Score: 0.568 ---
Um incidente é classificado como crítico quando atende a pelo menos um dos seguintes critérios:

- Carga com valor declarado acima de R$ 100.000 está com status desconhecido há mais de 6 horas.
- Carga perigosa com qualquer irregularidade de documentação ou rastreamento.
- Mais de 5 chamados do mesmo cliente nas últimas 24 horas sobre o mesmo problema.
- Qualquer situação que envolva risco à segurança de pessoas.

--- Trecho 4 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 4. Condições especiais | Score: 0.551 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas).
- Descontos de volume (mais de 10 fretes especiais/mês para o mesmo cliente) devem ser negociados pelo Comercial e registrados em aditivo contratual.

--- Trecho 5 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.2. Exceções ao prazo geral | Score: 0.506 ---
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1), gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4), oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa especificada na nota fiscal por mais de 30 minutos contínuos, conforme registro do sensor IoT).
- Cargas com lacre de segurança violado, salvo quando a violação for documentada no ato de entrega com assinatura do motorista e do recebedor.

Para essas categorias, o cliente deve entrar em

--- Trecho 6 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.411 ---
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

--- Trecho 7 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 3. Prazo de entrega para frete especial | Score: 0.361 ---
O prazo de entrega para frete especial é calculado como o prazo padrão da rota + 2 dias úteis adicionais para manuseio de carga pesada.

--- Trecho 8 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 2. Escopo | Score: 0.357 ---
Aplica-se a todas as devoluções solicitadas por clientes da NovaTech após a entrega da mercadoria. Não se aplica a mercadorias ainda em trânsito (para essas, consultar PROC-088: Procedimento de Interceptação de Carga).

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Carga perigosa com frete expresso?

──────────────────────────────────────────────────────────────────────
Carga Perigosa com Frete Expresso — NovaTech Logística

Com base nos trechos recuperados:

Regra obrigatória aplicável (Regra 4):
Qualquer questão envolvendo carga perigosa deve ser escalada imediatamente para o ramal 4500 (Gestão de Riscos).

O que os trechos confirmam sobre carga perigosa + frete:

Cargas perigosas com peso acima de 500kg não seguem a PROC-042 (frete especial padrão) — seguem a PROC-043: Frete de Cargas Perigosas (Fonte: PROC-042-v2, Trecho 2)
Atenção: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações (Trecho 2)
Qualquer irregularidade de documentação ou rastreamento em carga perigosa é classificada como incidente crítico (Fonte: SLA-2024, Trecho 3)
O que NÃO está nos trechos recuperados:
Não encontrei informação específica sobre a combinação "carga perigosa + frete expresso" na documentação disponível — o chunk específico sobre esse procedimento (incluindo requisitos de autorização e documentação ANTT para essa modalidade) não foi recuperado.

Ação recomendada:
Escale para o ramal 4500 (Gestão de Riscos) e consulte diretamente a PROC-043 para verificar se frete expresso é permitido para carga perigosa e quais autorizações são necessárias.

Nota de diagnóstico RAG: Esta query resultou em FAIL — o chunk obrigatório FAQ-32 (snippets: autorização do Compliance, documentação ANTT) não foi recuperado. Os 8 trechos retornados são semanticamente próximos de "carga perigosa" e "frete", mas nenhum cobre especificamente a combinação com "expresso". Ponto de melhoria: adicionar sinônimos/expansão de query para "expresso" → urgente, prioritário, modalidade expressa.
```

</details>

---

### Query 9 — "Qual o multiplicador para o Sudeste?" — ✓ PASS

**Gabarito Anexo B:**
- DEVE: PROC-042v2-B — ✓ encontrado
- PODE: PROC-042-B — ✓ encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.6836 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 2. Fórmula de cálculo > 2.1. Multiplicadores regionais (atualizados em novembro/2023) | **✓ DEVE** |
| 2 | 0.6727 | PROC-042-frete-especial-v1.md (v1.0) | 2. Fórmula de cálculo > 2.1. Multiplicadores regionais | ✓ PODE |
| 3 | 0.4749 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 8 — "Como funciona o frete especial?" | ✗ Ruído |
| 4 | 0.3848 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 1. Objetivo | ✗ Ruído |
| 5 | 0.3562 | PROC-042-frete-especial-v1.md (v1.0) | 2. Fórmula de cálculo | ✗ Ruído |
| 6 | 0.3562 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 2. Fórmula de cálculo | ✗ Ruído |
| 7 | 0.3415 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 5. Disposições transitórias | ✗ Ruído |
| 8 | 0.3390 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 27 — "O tracking mostra 'em trânsito' há 5 dias. O que faço?" | ✗ Ruído |

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 2. Fórmula de cálculo > 2.1. Multiplicadores regionais (atualizados em novembro/2023) | Score: 0.684 ---
| Região | Multiplicador |
|--------|--------------|
| Sul | 1.3 |
| Sudeste | 1.1 |
| Centro-Oeste | 1.4 |
| Nordeste | 1.5 |
| Norte | 1.8 |

--- Trecho 2 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 2. Fórmula de cálculo > 2.1. Multiplicadores regionais | Score: 0.673 ---
| Região | Multiplicador |
|--------|--------------|
| Sul | 1.2 |
| Sudeste | 1.0 |
| Centro-Oeste | 1.3 |
| Nordeste | 1.4 |
| Norte | 1.6 |

--- Trecho 3 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 8 — "Como funciona o frete especial?" | Score: 0.475 ---
Acima de 500kg, aplica a tabela de multiplicadores por região. Cuidado: existem duas versões da PROC-042. A mais recente tem multiplicadores mais altos. Na dúvida, use a mais recente (v2), mas se o cliente reclamar do valor, pode ser que o contrato dele ainda esteja na tabela antiga.

--- Trecho 4 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 1. Objetivo | Score: 0.385 ---
Definir a fórmula e os parâmetros atualizados para cálculo de frete especial aplicável a cargas com peso acima de 500kg. Os multiplicadores foram revisados para refletir os custos operacionais atualizados de cada região.

--- Trecho 5 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 2. Fórmula de cálculo | Score: 0.356 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.2 para cargas de 1.001kg a 3.000kg; 1.5 para cargas acima de 3.000kg.

--- Trecho 6 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 2. Fórmula de cálculo | Score: 0.356 ---
O frete especial é calculado como:

Valor do frete = Valor base × Multiplicador regional × Fator de peso

Onde:
- Valor base = tarifa publicada na tabela mensal de fretes.
- Multiplicador regional = fator aplicado conforme a região de destino (seção 2.1).
- Fator de peso = 1.0 para cargas de 500kg a 1.000kg; 1.15 para cargas de 1.001kg a 3.000kg; 1.4 para cargas acima de 3.000kg.

--- Trecho 7 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 5. Disposições transitórias | Score: 0.342 ---
Durante o período de transição, chamados abertos antes de 01/12/2023 que ainda estejam em processamento devem usar os multiplicadores da versão anterior (PROC-042 v1). Chamados novos a partir de 01/12/2023 devem usar os multiplicadores desta versão.

--- Trecho 8 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 27 — "O tracking mostra 'em trânsito' há 5 dias. O que faço?" | Score: 0.339 ---
Depende da rota. Rotas para o Norte podem levar até 10 dias úteis. Para Sul/Sudeste, mais de 3 dias parado é estranho. Abra um chamado de rastreamento e classifique como prioridade alta se for Gold ou se o valor da carga for acima de R$ 50.000.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Qual o multiplicador para o Sudeste?

──────────────────────────────────────────────────────────────────────
Multiplicador regional para o Sudeste — NovaTech Logística

Contradição detectada entre versões da PROC-042:

Versão	Sudeste	Vigência
PROC-042 v1.0	1.0	Chamados abertos antes de 01/12/2023
PROC-042 v2.0	1.1	Chamados abertos a partir de 01/12/2023
Resposta aplicável: O multiplicador vigente para o Sudeste é 1.1 (PROC-042-v2-frete-especial-revisado.md, versão 2.0, seção 2.1 — atualizado em novembro/2023).

Exceção: Se o chamado foi aberto antes de 01/12/2023 e ainda está em processamento, use o multiplicador da versão anterior: 1.0 (conforme disposições transitórias, Trecho 7).

Nota (FAQ, fonte não controlada): confirma que a v2 possui multiplicadores mais altos e que, se o cliente reclamar do valor, pode ser que o contrato dele ainda esteja na tabela antiga — nesse caso, acione o Comercial para verificação.
```

</details>

---

### Query 10 — "Prazo de devolução, carga perigosa e frete especial" — ✗ FAIL

**Gabarito Anexo B:**
- DEVE: POL-001-A — ✗ não encontrado
- DEVE: POL-001-B — ✓ encontrado
- DEVE: PROC-042v2-A — ✓ encontrado
- DEVE: PROC-042v2-B — ✗ não encontrado
- PODE: FAQ-03 — — não encontrado

**Chunks recuperados (N=8):**

| # | Score | Fonte | Seção | Gabarito? |
|---|-------|-------|-------|-----------|
| 1 | 0.6388 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.2. Exceções ao prazo geral | **✓ DEVE** |
| 2 | 0.5843 | PROC-042-v2-frete-especial-revisado.md (v2.0) | 4. Condições especiais | **✓ DEVE** |
| 3 | 0.4887 | SLA-2024-tabela-sla-clientes.md (v2024.1) | 3. Definição de incidente crítico | ✗ Ruído |
| 4 | 0.4880 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | ✗ Ruído |
| 5 | 0.4834 | PROC-042-frete-especial-v1.md (v1.0) | 4. Condições especiais | ✗ Ruído |
| 6 | 0.4660 | FAQ-atendimento.md (vNão controlada) | Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | ✗ Ruído |
| 7 | 0.4228 | POL-001-politica-devolucao.md (v3.1) | 3. Regras de Devolução > 3.5. Custos de devolução | ✗ Ruído |
| 8 | 0.3964 | PROC-042-frete-especial-v1.md (v1.0) | 1. Objetivo | ✗ Ruído |

**Chunks obrigatórios não encontrados:**
- `POL-001-A` (fonte: `POL-001`, snippets: ['7 (sete) dias úteis'])
- `PROC-042v2-B` (fonte: `PROC-042-v2`, snippets: ['Norte', '1.8'])

<details>
<summary>Prompt montado para esta query (clique para expandir)</summary>

```
======================================================================
SISTEMA (instruções do assistente)
======================================================================
Você é um assistente de atendimento da NovaTech Logística. Sua função é responder perguntas de atendentes com base EXCLUSIVAMENTE nas informações presentes nos trechos de documentação fornecidos abaixo.

Regras obrigatórias:
1. USE APENAS informações dos trechos fornecidos. Não invente dados, valores ou prazos.
2. Se a resposta não estiver nos trechos, diga claramente: "Não encontrei essa informação na documentação disponível."
3. Se houver CONTRADIÇÃO entre documentos (ex.: PROC-042 v1 vs v2), aponte explicitamente e use a versão mais recente, salvo indicação contrária.
4. Para cargas perigosas: sempre escale para o ramal 4500 (Gestão de Riscos).
5. Tiers existentes: Gold, Silver, Standard. Se o cliente mencionar outro tier (ex.: Platinum), corrija gentilmente.
6. Para informações de fontes informais (FAQ), indique que a confirmação deve ser feita na documentação normativa (POL, PROC, SLA).

======================================================================
CONTEXTO (8 trechos recuperados por similaridade semântica)
======================================================================

--- Trecho 1 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.2. Exceções ao prazo geral | Score: 0.639 ---
As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1), gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4), oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa especificada na nota fiscal por mais de 30 minutos contínuos, conforme registro do sensor IoT).
- Cargas com lacre de segurança violado, salvo quando a violação for documentada no ato de entrega com assinatura do motorista e do recebedor.

Para essas categorias, o cliente deve entrar em

--- Trecho 2 | Fonte: PROC-042-v2-frete-especial-revisado.md (versão 2.0) | Seção: 4. Condições especiais | Score: 0.584 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas). Nota: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
- Descontos de volume: a partir de 8 fretes especiais/mês para o mesmo cliente, aplicar desconto de 5% sobre o multiplicador regional. Acima de 15 fretes/mês, desconto de 10%. Descontos maiores requerem aprovação da Diretoria Comercial.

--- Trecho 3 | Fonte: SLA-2024-tabela-sla-clientes.md (versão 2024.1) | Seção: 3. Definição de incidente crítico | Score: 0.489 ---
Um incidente é classificado como crítico quando atende a pelo menos um dos seguintes critérios:

- Carga com valor declarado acima de R$ 100.000 está com status desconhecido há mais de 6 horas.
- Carga perigosa com qualquer irregularidade de documentação ou rastreamento.
- Mais de 5 chamados do mesmo cliente nas últimas 24 horas sobre o mesmo problema.
- Qualquer situação que envolva risco à segurança de pessoas.

--- Trecho 4 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 38 — "Cliente quer saber a política para carga que chegou danificada." | Score: 0.488 ---
Carga danificada em trânsito tem processo diferente de devolução. O cliente precisa registrar a ocorrência em até 48h após o recebimento, com fotos e laudo se possível. A NovaTech investiga e, se comprovada responsabilidade nossa, reembolsa integralmente. Mas isso passa pelo Jurídico, não pelo atendimento normal — encaminhe para o e-mail sinistros@novatech.com.br.

--- Trecho 5 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 4. Condições especiais | Score: 0.483 ---
- Cargas acima de 5.000kg requerem aprovação prévia do gerente de operações regional.
- Cargas perigosas com peso acima de 500kg seguem tabela específica (PROC-043: Frete de Cargas Perigosas).
- Descontos de volume (mais de 10 fretes especiais/mês para o mesmo cliente) devem ser negociados pelo Comercial e registrados em aditivo contratual.

--- Trecho 6 | Fonte: FAQ-atendimento.md (versão Não controlada) | Seção: Perguntas selecionadas (das 47 do documento original) > Item 22 — "Cliente quer saber sobre seguro de carga. O que falar?" | Score: 0.466 ---
A NovaTech oferece seguro de carga como adicional. O valor é 0,3% do valor declarado da mercadoria para cargas padrão e 0,8% para cargas perigosas. Detalhe: isso vale para contratos a partir de 2023. Contratos mais antigos podem ter percentuais diferentes — confirme com o Comercial.

--- Trecho 7 | Fonte: POL-001-politica-devolucao.md (versão 3.1) | Seção: 3. Regras de Devolução > 3.5. Custos de devolução | Score: 0.423 ---
- Defeito ou erro da NovaTech (carga errada, avaria em trânsito): devolução sem custo para o cliente.
- Desistência do cliente (carga correta, sem defeito): o custo do frete reverso é do cliente, calculado com os mesmos multiplicadores do frete original.
- Prazo expirado (solicitação após 7 dias úteis): não elegível para devolução padrão. Encaminhar ao Comercial para negociação caso a caso.

--- Trecho 8 | Fonte: PROC-042-frete-especial-v1.md (versão 1.0) | Seção: 1. Objetivo | Score: 0.396 ---
Definir a fórmula e os parâmetros para cálculo de frete especial aplicável a cargas com peso acima de 500kg.

======================================================================
PERGUNTA DO ATENDENTE
======================================================================
Prazo de devolução, carga perigosa e frete especial

──────────────────────────────────────────────────────────────────────
Prazo de Devolução, Carga Perigosa e Frete Especial — NovaTech Logística

1. Prazo de Devolução
Prazo geral: Solicitações após 7 dias úteis da entrega não são elegíveis para devolução padrão — devem ser encaminhadas ao Comercial para negociação caso a caso.
(POL-001-politica-devolucao.md v3.1, seção 3.5 — Trecho 7)

Custos:

Defeito ou erro da NovaTech (avaria em trânsito): devolução sem custo para o cliente.
Desistência do cliente (carga correta): frete reverso por conta do cliente, com os mesmos multiplicadores do frete original.
2. Carga Perigosa
Regra obrigatória (Regra 4): Qualquer questão sobre carga perigosa deve ser escalada para o ramal 4500 (Gestão de Riscos).

Devolução: Cargas perigosas das classes 1 a 6 da ANTT (explosivos, gases, líquidos inflamáveis, sólidos inflamáveis, oxidantes, substâncias tóxicas) NÃO são elegíveis para o processo padrão de devolução.
(POL-001-politica-devolucao.md v3.1, seção 3.2 — Trecho 1)

Frete especial: Cargas perigosas acima de 500kg seguem tabela específica da PROC-043: Frete de Cargas Perigosas.
Atenção: a PROC-043 está em processo de revisão pelo Compliance e pode sofrer alterações.
(PROC-042-v2, seção 4 — Trecho 2)

Incidente crítico: Qualquer irregularidade de documentação ou rastreamento em carga perigosa é automaticamente classificada como incidente crítico.
(SLA-2024-tabela-sla-clientes.md v2024.1, seção 3 — Trecho 3)

3. Frete Especial (PROC-042)
Contradição detectada entre versões:

Condição	PROC-042 v1.0	PROC-042 v2.0 (vigente)
Carga acima de 5.000kg	Aprovação do gerente regional	Aprovação do gerente regional
Desconto de volume (início)	Acima de 10 fretes/mês — negociação Comercial	A partir de 8 fretes/mês — 5% sobre multiplicador
Desconto de volume (adicional)	—	Acima de 15 fretes/mês — 10%
Descontos maiores	—	Requerem aprovação da Diretoria Comercial
Usar PROC-042 v2.0 como referência para chamados a partir de 01/12/2023.
(Trechos 2 e 5)

O que não está nos trechos recuperados
O texto completo da seção 3.1 da POL-001 (prazo geral de devolução em dias úteis está inferido indiretamente pelo Trecho 7, não explicitado em chunk próprio).
Os multiplicadores regionais da PROC-042 v2 (seção 2.1) não foram recuperados para esta query — consulte diretamente a PROC-042 v2, seção 2.1 para valores por região.
O procedimento específico para carga perigosa pós-prazo de devolução: o Trecho 1 está truncado ("Para essas categorias, o cliente deve entrar em...") — consultar POL-001 completo.
```

</details>

---

## Lacunas remanescentes

- **POL-001-B** (`POL-001`) — snippets: `['NÃO são elegíveis', 'classes 1 a 6 da ANTT']`
- **SLA-2024-B** (`SLA-2024`) — snippets: `['Gold', '2h úteis', '24h úteis']`
- **PROC-042v2-B** (`PROC-042-v2`) — snippets: `['Norte', '1.8']`
- **FAQ-32** (`FAQ-atendimento`) — snippets: `['autorização do Compliance', 'documentação ANTT']`
- **POL-001-A** (`POL-001`) — snippets: `['7 (sete) dias úteis']`

## Comparativo v1 vs v2

| Métrica | v1 (all-MiniLM-L6-v2, N=5) | v2 (multilíngue, N=8, geo) |
|---------|---------------------------|----------------------------|
| Queries PASS | 3/10 (30%) | 5/10 (50%) |
| Chunks obrigatórios | 3/14 (21%) | 8/14 (57%) |
| N_RESULTS | 5 | 8 |
| Modelo | all-MiniLM-L6-v2 | paraphrase-multilingual-MiniLM-L12-v2 |
| Expansão geo | Não | Sim |
