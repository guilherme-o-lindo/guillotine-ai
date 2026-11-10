# Guillotine — Estado do Projeto e Plano de Evolução

**Documento de continuidade e acompanhamento técnico**

![Version](https://img.shields.io/static/v1?label=Version&message=0.1.0&color=7C3AED&style=flat-square)
![Next Version](https://img.shields.io/static/v1?label=Next%20Version&message=0.2.0&color=9333EA&style=flat-square)
![Python](https://img.shields.io/static/v1?label=Python&message=3.12%2B&color=3776AB&style=flat-square&logo=python&logoColor=white)

*Diagnóstico, prioridades e roadmap do Guillotine.*

> **Objetivo deste documento**
>
> Registrar o diagnóstico do MVP `v0.1.0`, as prioridades identificadas durante as revisões técnicas e o plano de evolução acordado. O documento mantém o contexto técnico e as decisões do projeto disponíveis no próprio repositório, facilitando a continuidade do desenvolvimento.

## Índice

- [1. Visão geral](#1-visão-geral)
- [2. Estado atual do MVP](#2-estado-atual-do-mvp-v010)
- [3. Pontos de atenção identificados](#3-pontos-de-atenção-identificados)
- [4. Roadmap](#4-roadmap)
- [5. Escopo da próxima versão](#5-escopo-da-próxima-versão-v020)
- [6. Ordem de implementação](#6-ordem-de-implementação-sugerida)
- [7. Processo de desenvolvimento](#7-processo-de-desenvolvimento)
- [8. Princípios arquiteturais](#8-princípios-arquiteturais)
- [9. Estado de acompanhamento](#9-estado-de-acompanhamento)

---

## 1. Visão geral

O **Guillotine** é um agente pessoal de IA desenvolvido em Python, com arquitetura modular e foco em integração com modelos, gerenciamento de conversas, memória e, futuramente, ferramentas e autonomia controlada.

A versão `v0.1.0` representa o MVP funcional. A prioridade atual não é adicionar muitas funcionalidades, mas fortalecer a base existente para que as próximas evoluções sejam confiáveis, testáveis e sustentáveis.

### Stack e tecnologias identificadas

| Categoria | Tecnologia | Finalidade |
|:---|:---|:---|
| Linguagem | Python `>=3.12` | Desenvolvimento da aplicação |
| Gerenciamento | `uv` | Gerenciamento do projeto e dependências |
| Agente | PydanticAI | Construção e execução do agente |
| Integração | API compatível com OpenAI | Comunicação com provedores |
| Endpoint local | 9Router | Endpoint utilizado no desenvolvimento |
| Cliente HTTP | `httpx2` | Comunicação HTTP assíncrona com o provedor |
| Persistência | SQLite + `aiosqlite` | Armazenamento local |
| Orquestração | LangGraph | Estrutura do fluxo de execução |
| Checkpoints | LangGraph Checkpoint SQLite | Persistência do estado do grafo |
| Testes | Pytest + pytest-asyncio | Testes automatizados |
| Qualidade | Ruff + Pyright | Análise estática e padronização |
| Versionamento | Commitizen | Conventional Commits |
| Releases | Python Semantic Release | Versionamento e geração de releases |

> **Observação:** a presença de uma dependência no projeto não significa necessariamente que ela já esteja integrada ao fluxo principal. Antes de utilizá-la ou removê-la, verificar seu uso real no código.

## 2. Estado atual do MVP (`v0.1.0`)

### Capacidades existentes

- Integração com modelo por meio de uma API compatível com OpenAI.
- Criação e gerenciamento de conversas.
- Persistência de conversas e mensagens em SQLite.
- Recuperação do histórico para envio ao modelo.
- CLI para operações com conversas.
- Estrutura inicial de memória.
- Estrutura de grafo e checkpoints com LangGraph.
- Inicialização e encerramento centralizados dos componentes da aplicação.
- Configuração por variáveis de ambiente.
- Tratamento de erros conhecidos do provedor.
- Testes automatizados para os principais componentes.

### Estrutura de diretórios observada

```text
src/guillotine/
├── core/
│   ├── agent.py
│   ├── checkpoint.py
│   ├── config.py
│   ├── context.py
│   ├── datetime.py
│   ├── graph.py
│   ├── lifecycle.py
│   ├── permissions.py
│   └── prompt.py
│
├── interfaces/
│   ├── api.py
│   ├── cli.py
│   └── voice.py
│
├── memory/
│   ├── manager.py
│   ├── types.py
│   ├── repositories/
│   │   ├── conversations.py
│   │   ├── knowledge.py
│   │   ├── messages.py
│   │   └── preferences.py
│   └── storage/
│       ├── database.py
│       └── models.py
│
├── models/
│   ├── errors.py
│   ├── provider.py
│   └── router.py
│
├── services/
│   └── conversations.py
│
├── tools/
│   ├── executor.py
│   ├── registry.py
│   └── mcp/
│       ├── client.py
│       └── manager.py
│
└── main.py
```

A estrutura representa o snapshot conhecido durante o acompanhamento. Caso o código seja reorganizado, atualizar este documento e o README para refletir a estrutura vigente.

### Avaliação arquitetural

A separação inicial de responsabilidades é coerente com a proposta do projeto:

| Diretório | Responsabilidade |
|:---|:---|
| `core/` | Componentes centrais do agente, configuração e ciclo de vida |
| `interfaces/` | Pontos de entrada e interação com o usuário |
| `memory/` | Gerenciamento, repositórios e armazenamento da memória |
| `models/` | Integração, seleção e tratamento de erros dos modelos |
| `services/` | Casos de uso e coordenação entre componentes |
| `tools/` | Execução e integração de ferramentas e servidores MCP |

**Decisão arquitetural:** preservar a arquitetura geral. Evitar criar camadas, abstrações ou diretórios sem uma necessidade concreta.

### Estado dos testes

<details>
<summary><strong>Resultado da suíte automatizada</strong></summary>

**Última execução registrada: 10/11/2026**

```text
77 passed in 3.74s
```

| Arquivo | Testes |
|:---|---:|
| `test_cli.py` | 15 |
| `test_config.py` | 6 |
| `test_conversation_repository.py` | 8 |
| `test_conversation_service_unit.py` | 14 |
| `test_database_setup.py` | 2 |
| `test_graph_unit.py` | 5 |
| `test_lifecycle.py` | 4 |
| `test_message_repository.py` | 9 |
| `test_model_errors.py` | 11 |
| `test_provider.py` | 3 |
| **Total** | **77** |

</details>

A suíte cobre configuração, persistência, serviços, grafo, lifecycle, provedor, tratamento de erros e CLI.

## 3. Pontos de atenção identificados

Os itens desta seção foram observados durante a revisão do MVP. O estado abaixo considera as correções e validações realizadas posteriormente.

### 3.1. Testes automatizados

![Priority](https://img.shields.io/static/v1?label=Priority&message=High&color=DC2626&style=flat-square)
![Status](https://img.shields.io/static/v1?label=Status&message=Conclu%C3%ADdo&color=16A34A&style=flat-square)

Inicialmente, os arquivos de teste continham scripts de execução manual com `main()` e saídas em `print()`, sem testes Pytest convencionais.

**Correções realizadas:**

- Configuração do Pytest.
- Criação de fixtures reutilizáveis.
- Isolamento do banco SQLite utilizado nos testes.
- Testes de repositórios e persistência.
- Testes do serviço de conversas.
- Testes do agente e do grafo.
- Testes de lifecycle e checkpointer.
- Simulação do provedor nos testes.
- Testes de tratamento de erros.
- Testes da CLI.

**Resultado atual:** 77 testes aprovados.

### 3.2. Configuração de ambiente

![Priority](https://img.shields.io/static/v1?label=Priority&message=High&color=DC2626&style=flat-square)
![Status](https://img.shields.io/static/v1?label=Status&message=Implementado&color=16A34A&style=flat-square)

A revisão identificou divergências entre os nomes das variáveis do `.env.example` e os nomes consultados pelo código.

**Variáveis principais esperadas pelo código:**

```env
GUILLOTINE_MODEL=seu-modelo
GUILLOTINE_BASE_URL=http://localhost:20128/v1
GUILLOTINE_API_KEY=sua-chave
GUILLOTINE_TIMEOUT=60
```

O arquivo `.env.example` também contém uma variável opcional para integração com GitHub:

```env
GH_TOKEN=seu-token-do-github
```

**Direção adotada:**

- Centralizar a leitura das configurações.
- Validar configurações obrigatórias.
- Validar o timeout.
- Apresentar erros claros quando uma configuração estiver ausente ou inválida.
- Testar o comportamento das configurações.
- Manter credenciais fora do controle de versão.

A implementação da configuração principal e seus testes já foram realizados.

**Pendências:**

- [ ] Confirmar a correspondência integral entre `.env.example` e as variáveis efetivamente utilizadas pelo código.
- [ ] Confirmar se `GH_TOKEN` já é consumido por algum componente da aplicação.
- [ ] Confirmar que segredos não são registrados nos logs.

Nunca versionar `.env` nem compartilhar chaves, tokens ou credenciais.

### 3.3. Cliente e provedor de modelo

![Priority](https://img.shields.io/static/v1?label=Priority&message=Medium&color=F59E0B&style=flat-square)
![Status](https://img.shields.io/static/v1?label=Status&message=Implementado&color=16A34A&style=flat-square)

A revisão identificou clientes independentes para o mesmo serviço: um cliente OpenAI assíncrono e um `OpenAIProvider` utilizado pelo PydanticAI.

A estratégia atual passou a centralizar a criação e o gerenciamento do cliente no ciclo de vida do provedor.

**Correções realizadas:**

- Utilização do `OpenAIProvider`.
- Injeção do cliente HTTP no provedor.
- Gerenciamento assíncrono do cliente.
- Configuração de timeout.
- Separação da criação do agente e do lifecycle do modelo.
- Tratamento de erros conhecidos do provedor.
- Testes do provedor e do lifecycle.

O cliente HTTP utilizado atualmente é `httpx2`, adotado para acompanhar a compatibilidade exigida pela versão instalada do PydanticAI.

### 3.4. LangGraph e checkpoints

![Priority](https://img.shields.io/static/v1?label=Priority&message=Medium&color=F59E0B&style=flat-square)
![Status](https://img.shields.io/static/v1?label=Status&message=Validado&color=16A34A&style=flat-square)

O grafo continua simples, com um nó principal do agente. O histórico da conversa é recuperado pelo gerenciamento de memória, enquanto o LangGraph mantém os checkpoints da execução.

**Direção adotada:**

- Manter a integração atual.
- Não aumentar a complexidade do grafo sem um caso de uso real.
- Preservar a separação entre histórico de mensagens e checkpoints.
- Utilizar o identificador da conversa como identificador da thread.
- Verificar a consistência entre exclusão de conversas e exclusão dos checkpoints associados.

**Validações realizadas:**

- Testes do fluxo do grafo.
- Testes de persistência das mensagens.
- Testes da exclusão de conversas.
- Teste de exclusão em cascata das mensagens.
- Teste de falha na exclusão do checkpoint.
- Teste para impedir operações desnecessárias quando a conversa não existe.

**Observação sobre concorrência:** chamadas simultâneas para a mesma conversa ainda não possuem serialização explícita. A implementação de locks foi adiada até existir um consumidor concorrente que justifique essa complexidade.

### 3.5. Tratamento de erros e CLI

![Priority](https://img.shields.io/static/v1?label=Priority&message=Medium&color=F59E0B&style=flat-square)
![Status](https://img.shields.io/static/v1?label=Status&message=Implementado&color=16A34A&style=flat-square)

A revisão inicial identificou tratamento limitado de exceções na CLI e uso de `input()` em fluxo assíncrono.

**Correções realizadas:**

- Implementação de mensagens amigáveis para erros conhecidos do modelo.
- Criação de `models/errors.py`.
- Tratamento de erros esperados na CLI.
- Testes de erros do provedor.
- Testes de erros do serviço.
- Verificação de que erros inesperados continuam sendo propagados.

A estratégia de entrada da CLI pode ser revisada futuramente caso surja uma necessidade real de maior concorrência.

### 3.6. Componentes ainda não implementados ou incompletos

Os seguintes módulos representam possibilidades de evolução. Sua presença na estrutura não significa que precisem ser implementados imediatamente.

| Módulo | Estado conhecido |
|:---|:---|
| `memory/repositories/knowledge.py` | Implementação funcional ainda não confirmada na revisão |
| `memory/repositories/preferences.py` | Implementação funcional ainda não confirmada na revisão |
| `models/router.py` | Roteamento inteligente planejado |
| `tools/registry.py` | Estrutura criada; integração com o fluxo principal pendente |
| `tools/executor.py` | Estrutura criada; execução de ferramentas pendente |
| `tools/mcp/client.py` | Integração MCP a evoluir |
| `tools/mcp/manager.py` | Gerenciamento MCP a evoluir |
| `interfaces/api.py` | Interface planejada |
| `interfaces/voice.py` | Interface planejada |
| `core/permissions.py` | Permissões e controle de acesso futuros |
| `core/context.py` | Gerenciamento de contexto a evoluir |
| `core/prompt.py` | Gerenciamento de prompts a evoluir |

Esses módulos não fazem parte do escopo obrigatório da `v0.2.0`, salvo necessidade identificada durante a revisão.

### 3.7. Dependências

Foram identificadas dependências cuja utilização direta no fluxo principal não estava evidente na revisão, incluindo:

- SQLAlchemy e Alembic;
- Structlog;
- Sentry;
- OpenTelemetry;
- Playwright;
- Tenacity;
- MCP.

**Direção:** revisar cada dependência individualmente. Manter quando houver uso atual ou uma decisão concreta de implementação próxima; evitar dependências preventivas sem necessidade.

### 3.8. Documentação e ferramentas de desenvolvimento

![Priority](https://img.shields.io/static/v1?label=Priority&message=Medium&color=F59E0B&style=flat-square)
![Status](https://img.shields.io/static/v1?label=Status&message=Em%20revis%C3%A3o&color=F59E0B&style=flat-square)

Foram observados alguns ajustes na documentação e no processo de desenvolvimento:

- O README precisava refletir melhor o estado atual da implementação.
- O CHANGELOG apresentava entradas duplicadas para `v0.1.0`.
- O `.env.example` precisava ser conferido com as configurações efetivamente utilizadas.
- A configuração do Pre-commit precisava ser revisada e validada.

**Correções e avanços realizados:**

- [x] Atualização inicial do README.
- [x] Correção proposta para a duplicação do CHANGELOG.
- [x] Definição da configuração dos hooks do Pre-commit.
- [x] Inclusão das instruções de desenvolvimento no README.

**Pendências:**

- [ ] Revisar o README após conferência com o código atual.
- [ ] Aplicar e validar a correção do CHANGELOG.
- [ ] Confirmar a correspondência do `.env.example`.
- [ ] Validar os hooks do Pre-commit.
- [ ] Validar o processo de release.

## 4. Roadmap

O desenvolvimento do Guillotine será dividido em versões incrementais. Cada versão terá um tema e um conjunto de objetivos, permitindo evoluir a aplicação sem antecipar complexidade desnecessária.

| Versão | Tema | Objetivo |
|:---|:---|:---|
| `v0.1.0` | MVP | Agente funcional, CLI e persistência inicial |
| `v0.2.0` | Confiabilidade | Testes, configuração, tratamento de erros e consistência |
| `v0.3.0` | Ferramentas | Registry, executor, validação e integração MCP |
| `v0.4.0` | Memória inteligente | Conhecimento, preferências, recuperação e gerenciamento |
| `v0.5.0` | Interfaces | Evolução da CLI e implementação da API |
| `v0.6.0` | Autonomia controlada | Planejamento, execução em etapas, checkpoints e aprovação humana |
| `v0.7.0` | Segurança e observabilidade | Permissões, logs, métricas e rastreamento |
| `v1.0.0` | Estabilidade | Arquitetura consolidada e comportamento confiável |

> O roadmap é uma direção, não um compromisso de implementar todos os itens exatamente nessa ordem. As prioridades podem mudar após cada revisão técnica.

## 5. Escopo da próxima versão (`v0.2.0`)

![Release](https://img.shields.io/static/v1?label=Release&message=v0.2.0&color=7C3AED&style=for-the-badge)
![Theme](https://img.shields.io/static/v1?label=Theme&message=Reliability%20and%20Testing&color=9333EA&style=for-the-badge)

**Objetivo:** transformar a base atual em uma aplicação testável, previsível e preparada para receber novas capacidades.

### 5.1. Testes automatizados

- [x] Revisar a configuração atual do Pytest.
- [x] Criar fixtures para banco SQLite isolado.
- [x] Converter verificações relevantes em testes automatizados.
- [x] Testar operações de conversas.
- [x] Testar operações de mensagens.
- [x] Testar o serviço de conversas.
- [x] Testar o fluxo do agente e do grafo.
- [x] Testar lifecycle e checkpoints.
- [x] Simular respostas e falhas do provedor.
- [x] Testar tratamento de erros.

**Resultado registrado:** 77 testes aprovados.

### 5.2. Configuração

- [x] Centralizar a leitura de configurações.
- [x] Validar valores obrigatórios.
- [x] Validar o timeout.
- [x] Testar configurações válidas e inválidas.
- [ ] Revisar e alinhar o `.env.example`.
- [ ] Confirmar a utilização de `GH_TOKEN`.
- [ ] Confirmar que segredos não são registrados nos logs.

### 5.3. Provedor

- [x] Definir o ciclo de vida do cliente.
- [x] Configurar timeout.
- [x] Tratar erros conhecidos do provedor.
- [x] Preparar substituição ou simulação do provedor nos testes.
- [x] Testar o lifecycle do provedor.

### 5.4. Conversas, memória e checkpoints

- [x] Revisar a persistência de mensagens.
- [x] Testar a continuidade do histórico.
- [x] Testar criação, listagem e exclusão de conversas.
- [x] Verificar a remoção das mensagens associadas.
- [x] Verificar a remoção dos checkpoints associados.
- [x] Testar falhas durante a exclusão.
- [x] Documentar a responsabilidade de cada mecanismo de persistência.
- [x] Verificar que a gravação de uma troca de mensagens é atômica.

### 5.5. CLI e documentação

- [x] Melhorar o tratamento de erros da CLI.
- [x] Testar o comportamento dos comandos.
- [x] Atualizar a primeira versão do README.
- [x] Definir a configuração do Pre-commit.
- [ ] Realizar revisão final do README.
- [ ] Corrigir e validar o CHANGELOG.
- [ ] Revisar o `.env.example`.
- [ ] Validar os hooks do Pre-commit.
- [ ] Validar o processo de release.

### Critérios de conclusão da `v0.2.0`

A versão será considerada concluída quando os seguintes critérios forem atendidos:

- [x] Pytest executa testes reais e apresenta resultados.
- [x] Os testes utilizam armazenamento isolado.
- [x] Configuração ausente ou inválida gera mensagens claras.
- [x] Falhas conhecidas do provedor são tratadas de forma previsível.
- [x] O histórico de conversas permanece consistente.
- [x] A exclusão de uma conversa trata suas mensagens e checkpoints associados.
- [ ] Ruff, Pyright e Pre-commit validados na revisão final.
- [ ] README e CHANGELOG refletem o projeto.
- [ ] Processo de release revisado e validado.

## 6. Ordem de implementação sugerida

A implementação da `v0.2.0` deve ocorrer em pequenas etapas:

| Etapa | Área | Atividade | Estado |
|:---:|:---|:---|:---|
| 01 | Infraestrutura de testes | Revisar Pytest, criar fixtures e preparar banco isolado | Concluída |
| 02 | Persistência | Testar banco, modelos e repositórios | Concluída |
| 03 | Conversas | Testar o serviço e o ciclo de vida das conversas | Concluída |
| 04 | Agente | Simular o modelo e testar o fluxo de execução | Concluída |
| 05 | Configuração | Corrigir variáveis, validação e inicialização | Implementada; documentação pendente |
| 06 | Provedor | Organizar clientes, timeout e tratamento de erros | Concluída |
| 07 | CLI | Revisar erros e comportamento dos comandos | Concluída |
| 08 | Documentação e release | Atualizar documentos, validar ferramentas e preparar a release | Em andamento |

A ordem pode ser ajustada quando uma dependência técnica exigir.

## 7. Processo de desenvolvimento

Cada tarefa deve seguir um ciclo de desenvolvimento consistente:

1. **Análise:** localizar o problema no código atual e entender seu comportamento.
2. **Projeto:** definir a solução e as responsabilidades envolvidas.
3. **Implementação:** alterar apenas o necessário.
4. **Validação:** executar testes relevantes, Ruff e Pyright.
5. **Revisão:** verificar efeitos colaterais, simplicidade e coerência arquitetural.
6. **Commit:** registrar a mudança com Conventional Commits.

### Convenção de commits

Usar mensagens no padrão Conventional Commits.

Exemplos:

```text
test: add isolated sqlite fixtures
fix: validate model provider configuration
refactor: centralize provider lifecycle
docs: update development instructions
```

A geração de versão, tag e changelog deve continuar centralizada no Python Semantic Release, conforme a configuração do projeto.

## 8. Princípios arquiteturais

Ao evoluir o Guillotine, preservar estes princípios:

| Princípio | Diretriz |
|:---|:---|
| **Simplicidade antes de abstração** | Não criar estruturas genéricas sem necessidade demonstrada. |
| **Modularidade com propósito** | Cada módulo deve ter responsabilidade compreensível. |
| **Separação de responsabilidades** | Interfaces não devem concentrar a lógica do agente. |
| **Testabilidade** | Componentes importantes devem poder ser testados sem depender de serviços externos. |
| **Controle de recursos** | Conexões, clientes e tarefas assíncronas devem ter ciclo de vida definido. |
| **Falhas previsíveis** | Erros devem ser tratados e comunicados adequadamente. |
| **Segurança por padrão** | Segredos não devem ser versionados ou expostos em logs. |
| **Evolução incremental** | Implementar, validar e revisar antes de avançar. |

## 9. Estado de acompanhamento

Atualizar esta seção ao concluir tarefas ou iniciar uma nova versão.

| Campo | Estado registrado |
|:---|:---|
| Versão publicada | `v0.1.0` |
| Próxima versão planejada | `v0.2.0` |
| Tema atual | Confiabilidade e testes |
| Testes automatizados | 77 aprovados |
| Estado da implementação | Testes, persistência, configuração principal, provedor e CLI implementados e testados |
| Documentação | Primeira atualização do README realizada; revisão final pendente |
| Pre-commit | Configuração definida; validação pendente |
| Próxima tarefa | Revisar README, CHANGELOG, `.env.example` e validar Pre-commit |
| Etapa posterior | Validar a release `v0.2.0` |
| Estratégia | Implementação incremental |

### Registro de decisões e progresso

Adicionar entradas curtas conforme o projeto evoluir:

```text
## Histórico de progresso

- [2026-11-10] Suíte automatizada alcançou 77 testes aprovados.
- [2026-11-10] Testada a exclusão em cascata das mensagens associadas a uma conversa.
- [2026-11-10] Testada a integridade da exclusão diante de falhas no checkpointer.
- [2026-11-10] Validado que conversas inexistentes não provocam exclusão de checkpoints.
- [2026-11-10] Concluída a revisão da integridade da exclusão de conversas.
- [AAAA-MM-DD] Decisão ou tarefa concluída.
- [AAAA-MM-DD] Problema encontrado e solução adotada.
```

---

<p align="center">
  <img src="assets/banner.png" alt="Guillotine" width="100%">
</p>

<p align="center">
  <em>Documento de acompanhamento técnico do projeto Guillotine.</em>
</p>