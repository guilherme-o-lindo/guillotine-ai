 <div align="center">

![Guillotine — Estado do Projeto e Plano de Evolução](assets/Estado%20do%20Projeto%20Guillotine.png)

**Documento de continuidade e acompanhamento técnico**

<p align="center">
  <img src="https://img.shields.io/static/v1?label=Version&message=0.1.0&color=7C3AED&style=flat-square" alt="Version 0.1.0">
  <img src="https://img.shields.io/static/v1?label=Next%20Version&message=0.2.0&color=9333EA&style=flat-square" alt="Next Version 0.2.0">
  <img src="https://img.shields.io/static/v1?label=Python&message=3.12%2B&color=3776AB&style=flat-square&logo=python&logoColor=white" alt="Python 3.12+">
</p>

*Diagnóstico, prioridades e roadmap do Guillotine.*

</div>

> **Objetivo deste documento**
>
> Registrar o diagnóstico do MVP `v0.1.0`, as prioridades identificadas na revisão do código e o plano de evolução acordado. O documento mantém o contexto técnico e as decisões do projeto disponíveis no próprio repositório, facilitando a continuidade do desenvolvimento em outras sessões.

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

## 1. Visão geral

O **Guillotine** é um agente pessoal de IA desenvolvido em Python, com arquitetura modular e foco em integração com modelos, gerenciamento de conversas, memória e, futuramente, ferramentas e autonomia controlada.

A versão `v0.1.0` representa um MVP funcional. A prioridade imediata não é adicionar muitas funcionalidades, mas fortalecer a base existente para que as próximas evoluções sejam confiáveis, testáveis e sustentáveis.

### Stack e tecnologias identificadas

| Categoria | Tecnologia | Finalidade |
|---|---|---|
| Linguagem | Python `>=3.12` | Desenvolvimento da aplicação |
| Gerenciamento | `uv` | Gerenciamento do projeto e dependências |
| Agente | PydanticAI | Interação com o modelo |
| Integração | API compatível com OpenAI | Comunicação com provedores |
| Endpoint local | 9Router | Endpoint utilizado no desenvolvimento |
| Persistência | SQLite + `aiosqlite` | Armazenamento local |
| Orquestração | LangGraph | Estrutura inicial de fluxo |
| Checkpoints | SQLite | Persistência do estado do grafo |
| Testes | Pytest | Testes automatizados |
| Qualidade | Ruff + Pyright | Análise estática e padronização |
| Versionamento | Commitizen | Conventional Commits |
| Releases | Python Semantic Release | Versionamento e geração de releases |

> **Observação:** a presença de uma dependência no projeto não significa necessariamente que ela já esteja integrada ao fluxo principal. Antes de utilizá-la ou removê-la, verificar seu uso real no código.

## 2. Estado atual do MVP (`v0.1.0`)

<details>
<summary><strong>Capacidades existentes</strong></summary>

- Integração com modelo por meio de uma API compatível com OpenAI.
- Criação e gerenciamento de conversas.
- Persistência de conversas e mensagens em SQLite.
- Recuperação do histórico para envio ao modelo.
- CLI para operações com conversas.
- Estrutura inicial de memória.
- Estrutura inicial de grafo e checkpoints com LangGraph.
- Inicialização e encerramento centralizados dos componentes da aplicação.
- Configuração por variáveis de ambiente.

</details>

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

A estrutura acima representa o snapshot analisado durante a revisão do MVP. Caso o código tenha sido reorganizado posteriormente, atualizar este documento para refletir a estrutura vigente.

### Avaliação arquitetural

A separação inicial de responsabilidades é coerente com a proposta do projeto:

| Diretório | Responsabilidade |
|---|---|
| `core/` | Componentes centrais do agente, configuração e ciclo de vida. |
| `interfaces/` | Pontos de entrada e interação com o usuário. |
| `memory/` | Gerenciamento, repositórios e armazenamento da memória. |
| `models/` | Integração e seleção de modelos. |
| `services/` | Casos de uso e coordenação entre componentes. |
| `tools/` | Execução e integração de ferramentas e servidores MCP. |

**Decisão arquitetural:** preservar a arquitetura geral. Evitar criar camadas, abstrações ou diretórios sem uma necessidade concreta.

## 3. Pontos de atenção identificados

Os itens abaixo foram observados na revisão do snapshot do MVP. Devem ser revalidados no código antes de cada alteração, pois podem ter sido corrigidos depois da análise.

### 3.1. Testes automatizados

![Priority](https://img.shields.io/static/v1?label=Priority&message=High&color=DC2626&style=flat-square)

Os arquivos de teste analisados continham scripts de execução manual com `main()` e saídas em `print()`, mas não apresentavam testes Pytest convencionais com funções `test_...`.

Scripts manuais podem continuar sendo úteis para experimentação, mas não substituem testes automatizados.

**Direção**

- Converter verificações relevantes em testes Pytest.
- Criar fixtures reutilizáveis.
- Isolar o banco utilizado nos testes.
- Testar repositórios, serviços, memória e integração com o agente.
- Simular o provedor nos testes que não precisam de rede.

> **Regra:** testes não devem depender do banco de desenvolvimento nem de um provedor externo real, salvo quando forem testes de integração explicitamente identificados.

### 3.2. Configuração de ambiente

![Priority](https://img.shields.io/static/v1?label=Priority&message=High&color=DC2626&style=flat-square)

Foi identificada divergência entre os nomes das variáveis no `.env.example` e os nomes consultados pelo código.

**Nomes esperados pelo código:**

```env
GUILLOTINE_MODEL=seu-modelo
GUILLOTINE_BASE_URL=http://localhost:20128/v1
GUILLOTINE_API_KEY=sua-chave
```

**Direção**

- Corrigir o `.env.example`.
- Centralizar a leitura das configurações.
- Validar configurações obrigatórias na inicialização.
- Exibir erros claros quando uma configuração estiver ausente ou inválida.

Nunca versionar `.env` nem compartilhar chaves, tokens ou credenciais.

### 3.3. Cliente e provedor de modelo

![Priority](https://img.shields.io/static/v1?label=Priority&message=Medium&color=F59E0B&style=flat-square)

A revisão identificou clientes independentes para o mesmo serviço: um cliente OpenAI assíncrono e um `OpenAIProvider` utilizado pelo PydanticAI. O cliente independente aparecia em um script de conexão.

Isso não é necessariamente incorreto, mas exige uma estratégia explícita.

**Direção**

- Definir quem cria e gerencia os clientes.
- Definir como os recursos e conexões são encerrados.
- Configurar timeout.
- Tratar indisponibilidade e erros do provedor.
- Permitir simulação do provedor nos testes.

### 3.4. LangGraph e checkpoints

![Priority](https://img.shields.io/static/v1?label=Priority&message=Medium&color=F59E0B&style=flat-square)

O grafo observado no MVP era simples, com um nó principal do agente. O histórico da conversa era recuperado pelo gerenciamento de memória, enquanto o checkpoint do LangGraph ainda não coordenava um fluxo complexo de execução.

**Direção**

- Manter a integração por enquanto.
- Não aumentar a complexidade do grafo sem um caso de uso real.
- Definir com clareza a responsabilidade do histórico persistido e dos checkpoints.
- Verificar a consistência entre exclusão de conversas e exclusão dos checkpoints associados.

### 3.5. Tratamento de erros e CLI

![Priority](https://img.shields.io/static/v1?label=Priority&message=Medium&color=F59E0B&style=flat-square)

A revisão identificou tratamento limitado de exceções na CLI e uso de `input()` em fluxo assíncrono.

**Direção**

- Tratar erros esperados do serviço e do provedor.
- Evitar encerramentos inesperados por falhas recuperáveis.
- Exibir mensagens compreensíveis para o usuário.
- Avaliar uma estratégia de entrada assíncrona caso a CLI passe a exigir maior concorrência.

### 3.6. Componentes ainda não implementados ou incompletos

Na revisão, alguns módulos estavam vazios ou ainda sem implementação funcional identificada:

| Módulo | Situação observada |
|---|---|
| `memory/repositories/knowledge.py` | Sem implementação funcional identificada |
| `memory/repositories/preferences.py` | Sem implementação funcional identificada |
| `models/router.py` | Sem implementação funcional identificada |
| `tools/registry.py` | Sem implementação funcional identificada |
| `tools/executor.py` | Sem implementação funcional identificada |
| `tools/mcp/client.py` | Estrutura inicial |
| `tools/mcp/manager.py` | Estrutura inicial |
| `interfaces/api.py` | Sem implementação funcional identificada |
| `interfaces/voice.py` | Sem implementação funcional identificada |
| `core/permissions.py` | Sem implementação funcional identificada |
| `core/context.py` | Sem implementação funcional identificada |
| `core/prompt.py` | Sem implementação funcional identificada |

Esses módulos representam possibilidades de evolução, não tarefas que precisam ser implementadas imediatamente.

### 3.7. Dependências

Foram identificadas dependências cuja utilização direta no fluxo principal não estava evidente na revisão, incluindo bibliotecas relacionadas a:

- SQLAlchemy e Alembic;
- Structlog;
- Sentry;
- OpenTelemetry;
- Playwright;
- Tenacity;
- MCP.

**Direção:** revisar cada dependência individualmente. Manter quando houver uso atual ou uma decisão concreta de implementação próxima; evitar dependências preventivas sem necessidade.

### 3.8. Documentação

Foram observados dois ajustes:

- O comando de clonagem e navegação no README não correspondia ao nome padrão do repositório `guillotine-ai`.
- O CHANGELOG apresentava entradas duplicadas para `v0.1.0`.

Revisar esses arquivos e manter a documentação alinhada ao estado real do projeto.

## 4. Roadmap

O desenvolvimento do Guillotine será dividido em versões incrementais. Cada versão terá um tema e um conjunto de objetivos, permitindo evoluir a aplicação sem antecipar complexidade desnecessária.

| Versão | Tema | Objetivo |
|---|---|---|
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

<div align="center">

<div align="center">

  <img src="https://img.shields.io/static/v1?label=Release&message=v0.2.0&color=7C3AED&style=for-the-badge" alt="Release v0.2.0">

  <img src="https://img.shields.io/static/v1?label=Theme&message=Reliability%20and%20Testing&color=9333EA&style=for-the-badge" alt="Theme Reliability and Testing">

</div>

</div>

**Objetivo:** transformar a base atual em uma aplicação testável, previsível e preparada para receber novas capacidades.

### 5.1. Testes automatizados

- [ ] Revisar a configuração atual do Pytest.
- [ ] Criar fixtures para banco SQLite isolado.
- [ ] Converter scripts manuais relevantes em testes automatizados.
- [ ] Testar operações de conversas.
- [ ] Testar operações de mensagens.
- [ ] Testar o serviço de conversas.
- [ ] Testar o gerenciamento de memória.
- [ ] Simular respostas e falhas do provedor.

### 5.2. Configuração

- [ ] Corrigir `.env.example`.
- [ ] Centralizar a leitura de configurações.
- [ ] Validar valores obrigatórios.
- [ ] Melhorar mensagens de erro na inicialização.
- [ ] Garantir que segredos não sejam registrados nos logs.

### 5.3. Provedor

- [ ] Definir o ciclo de vida dos clientes.
- [ ] Configurar timeout.
- [ ] Tratar falhas de conexão e respostas inválidas.
- [ ] Preparar substituição ou simulação do provedor nos testes.

### 5.4. Conversas, memória e checkpoints

- [ ] Revisar a persistência de mensagens.
- [ ] Testar a continuidade do histórico.
- [ ] Testar criação, listagem, abertura e exclusão de conversas.
- [ ] Verificar a remoção dos checkpoints associados à conversa.
- [ ] Documentar a responsabilidade de cada mecanismo de persistência.

### 5.5. CLI e documentação

- [ ] Melhorar o tratamento de erros.
- [ ] Revisar o comportamento dos comandos.
- [ ] Corrigir README.
- [ ] Corrigir CHANGELOG.
- [ ] Documentar configuração e execução local.

### Critérios de conclusão da `v0.2.0`

A versão será considerada concluída quando os seguintes critérios forem atendidos:

- [ ] Pytest executa testes reais e apresenta resultados.
- [ ] Os testes utilizam armazenamento isolado.
- [ ] Configuração ausente ou inválida gera mensagens claras.
- [ ] Falhas do provedor são tratadas de forma previsível.
- [ ] O histórico de conversas permanece consistente.
- [ ] A exclusão de uma conversa trata seus checkpoints associados.
- [ ] Ruff, Pyright e Pre-commit continuam funcionando.
- [ ] README e CHANGELOG refletem o projeto.

## 6. Ordem de implementação sugerida

A implementação da `v0.2.0` deve ocorrer em pequenas etapas:

| Etapa | Área | Atividade |
|---|---|---|
| 01 | Infraestrutura de testes | Revisar Pytest, criar fixtures e preparar banco isolado |
| 02 | Persistência | Testar banco, modelos e repositórios |
| 03 | Conversas | Testar o serviço e o ciclo de vida das conversas |
| 04 | Agente | Simular o modelo e testar o fluxo de execução |
| 05 | Configuração | Corrigir variáveis, validação e inicialização |
| 06 | Provedor | Organizar clientes, timeout e tratamento de erros |
| 07 | CLI | Revisar erros e comportamento dos comandos |
| 08 | Documentação e release | Atualizar documentos, validar a suíte e preparar a release |

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
|---|---|
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
|---|---|
| Versão publicada | `v0.1.0` |
| Próxima versão planejada | `v0.2.0` |
| Tema atual | Confiabilidade e testes |
| Próxima tarefa | Preparar infraestrutura do Pytest e isolamento do SQLite |
| Estratégia | Implementação incremental |

### Registro de decisões e progresso

Adicionar entradas curtas conforme o projeto evoluir:

```text
## Histórico de progresso

- [AAAA-MM-DD] Decisão ou tarefa concluída.
- [AAAA-MM-DD] Problema encontrado e solução adotada.
```

---

<div align="center">

![Guillotine](assets/banner.png)

<sub>Documento de acompanhamento técnico do projeto Guillotine.</sub>

</div>