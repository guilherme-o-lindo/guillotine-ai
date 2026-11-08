# Guillotine --- Estado do Projeto e Plano de Evolução

> Documento de continuidade do projeto. Registra o diagnóstico do MVP
> `v0.1.0`, as prioridades identificadas na revisão do código e o plano
> de evolução acordado.
>
> **Objetivo:** manter o contexto técnico e as decisões do projeto
> disponível no próprio repositório, facilitando a continuidade do
> desenvolvimento em outras sessões.

## 1. Visão geral

O Guillotine é um agente pessoal de IA desenvolvido em Python, com
arquitetura modular e foco em integração com modelos, gerenciamento de
conversas, memória e, futuramente, ferramentas e autonomia controlada.

A versão `v0.1.0` representa um MVP funcional. A prioridade imediata não
é adicionar muitas funcionalidades, mas fortalecer a base existente para
que as próximas evoluções sejam confiáveis e testáveis.

### Stack e tecnologias identificadas

-   Python `>=3.12`
-   `uv` para gerenciamento do projeto e dependências
-   PydanticAI para interação com o modelo
-   API compatível com OpenAI
-   9Router como endpoint local utilizado no desenvolvimento
-   SQLite e `aiosqlite` para persistência
-   LangGraph e checkpoints SQLite
-   Pytest, Ruff e Pyright para qualidade e validação
-   Commitizen e Python Semantic Release para versionamento e releases

> A presença de uma dependência no projeto não significa necessariamente
> que ela já esteja integrada ao fluxo principal. Antes de utilizá-la ou
> removê-la, verificar seu uso real no código.

## 2. Estado atual do MVP (`v0.1.0`)

### Capacidades existentes

-   Integração com modelo por meio de uma API compatível com OpenAI.
-   Criação e gerenciamento de conversas.
-   Persistência de conversas e mensagens em SQLite.
-   Recuperação do histórico para envio ao modelo.
-   CLI para operações com conversas.
-   Estrutura inicial de memória.
-   Estrutura inicial de grafo e checkpoints com LangGraph.
-   Inicialização e encerramento centralizados dos componentes da
    aplicação.
-   Configuração por variáveis de ambiente.

### Estrutura de diretórios observada

``` text
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

A estrutura acima é um registro da revisão do pacote enviado. Se o
código tiver sido reorganizado posteriormente, atualizar este documento
para refletir a estrutura vigente.

### Avaliação arquitetural

A separação inicial de responsabilidades é coerente com a proposta:

-   `core/`: componentes centrais do agente e ciclo de vida.
-   `interfaces/`: pontos de entrada e interação com o usuário.
-   `memory/`: gerenciamento, repositórios e armazenamento da memória.
-   `models/`: integração e seleção de modelos.
-   `services/`: casos de uso e coordenação entre componentes.
-   `tools/`: execução e integração futura de ferramentas e servidores
    MCP.

**Decisão:** preservar a arquitetura geral. Evitar criar camadas,
abstrações ou diretórios sem uma necessidade concreta.

## 3. Pontos de atenção identificados

Os itens abaixo foram observados na revisão do snapshot do MVP. Devem
ser revalidados no código antes de cada alteração, pois podem ter sido
corrigidos depois da análise.

### 3.1. Testes automatizados

**Prioridade: alta**

Os arquivos de teste analisados continham scripts de execução manual com
`main()` e saídas em `print()`, mas não apresentavam testes Pytest
convencionais com funções `test_...`.

Scripts manuais podem continuar sendo úteis para experimentação, mas não
substituem testes automatizados.

**Direção:**

-   Converter verificações relevantes em testes Pytest.
-   Criar fixtures reutilizáveis.
-   Isolar o banco utilizado nos testes.
-   Testar repositórios, serviços, memória e integração com o agente.
-   Simular o provedor nos testes que não precisam de rede.

**Regra:** testes não devem depender do banco de desenvolvimento nem de
um provedor externo real, salvo quando forem testes de integração
explicitamente identificados.

### 3.2. Configuração de ambiente

**Prioridade: alta**

Foi identificada divergência entre os nomes das variáveis no
`.env.example` e os nomes consultados pelo código.

Nomes esperados pelo código:

``` env
GUILLOTINE_MODEL=seu-modelo
GUILLOTINE_BASE_URL=http://localhost:20128/v1
GUILLOTINE_API_KEY=sua-chave
```

**Direção:**

-   Corrigir o `.env.example`.
-   Centralizar a leitura das configurações.
-   Validar configurações obrigatórias na inicialização.
-   Exibir erros claros quando uma configuração estiver ausente ou
    inválida.

Nunca versionar `.env` nem compartilhar chaves, tokens ou credenciais.

### 3.3. Cliente e provedor de modelo

**Prioridade: média**

A revisão identificou clientes independentes para o mesmo serviço: um
cliente OpenAI assíncrono e um `OpenAIProvider` utilizado pelo
PydanticAI. O cliente independente aparecia em um script de conexão.

Isso não é necessariamente incorreto, mas exige uma estratégia
explícita.

**Direção:**

-   Definir quem cria e gerencia os clientes.
-   Definir como os recursos e conexões são encerrados.
-   Configurar timeout.
-   Tratar indisponibilidade e erros do provedor.
-   Permitir simulação do provedor nos testes.

### 3.4. LangGraph e checkpoints

**Prioridade: média**

O grafo observado no MVP era simples, com um nó principal do agente. O
histórico da conversa era recuperado pelo gerenciamento de memória,
enquanto o checkpoint do LangGraph ainda não coordenava um fluxo
complexo de execução.

**Direção:**

-   Manter a integração por enquanto.
-   Não aumentar a complexidade do grafo sem um caso de uso real.
-   Definir com clareza a responsabilidade do histórico persistido e dos
    checkpoints.
-   Verificar a consistência entre exclusão de conversas e exclusão dos
    checkpoints associados.

### 3.5. Tratamento de erros e CLI

**Prioridade: média**

A revisão identificou tratamento limitado de exceções na CLI e uso de
`input()` em fluxo assíncrono.

**Direção:**

-   Tratar erros esperados do serviço e do provedor.
-   Evitar encerramentos inesperados por falhas recuperáveis.
-   Exibir mensagens compreensíveis para o usuário.
-   Avaliar uma estratégia de entrada assíncrona caso a CLI passe a
    exigir maior concorrência.

### 3.6. Componentes ainda não implementados ou incompletos

Na revisão, alguns módulos estavam vazios ou ainda sem implementação
funcional identificada:

-   `memory/repositories/knowledge.py`
-   `memory/repositories/preferences.py`
-   `models/router.py`
-   `tools/registry.py`
-   `tools/executor.py`
-   `tools/mcp/client.py` e `tools/mcp/manager.py` (estrutura inicial)
-   `interfaces/api.py`
-   `interfaces/voice.py`
-   `core/permissions.py`
-   `core/context.py`
-   `core/prompt.py`

Esses módulos representam possibilidades de evolução, não tarefas que
precisam ser implementadas imediatamente.

### 3.7. Dependências

Foram identificadas dependências cuja utilização direta no fluxo
principal não estava evidente na revisão, incluindo bibliotecas
relacionadas a SQLAlchemy, Alembic, Structlog, Sentry, OpenTelemetry,
Playwright, Tenacity e MCP.

**Direção:** revisar cada dependência individualmente. Manter quando
houver uso atual ou uma decisão concreta de implementação próxima;
evitar dependências preventivas sem necessidade.

### 3.8. Documentação

Foram observados dois ajustes:

-   O comando de clonagem e navegação no README não correspondia ao nome
    padrão do repositório `guillotine-ai`.
-   O CHANGELOG apresentava entradas duplicadas para `v0.1.0`.

Revisar esses arquivos e manter a documentação alinhada ao estado real
do projeto.

## 4. Roadmap

  -----------------------------------------------------------------------
  Versão                  Tema                    Objetivo
  ----------------------- ----------------------- -----------------------
  `v0.1.0`                MVP                     Agente funcional, CLI e
                                                  persistência inicial

  `v0.2.0`                Confiabilidade          Testes, configuração,
                                                  tratamento de erros e
                                                  consistência

  `v0.3.0`                Ferramentas             Registry, executor,
                                                  validação e integração
                                                  MCP

  `v0.4.0`                Memória inteligente     Conhecimento,
                                                  preferências,
                                                  recuperação e
                                                  gerenciamento

  `v0.5.0`                Interfaces              Evolução da CLI e
                                                  implementação da API

  `v0.6.0`                Autonomia controlada    Planejamento, execução
                                                  em etapas, checkpoints
                                                  e aprovação humana

  `v0.7.0`                Segurança e             Permissões, logs,
                          observabilidade         métricas e rastreamento

  `v1.0.0`                Estabilidade            Arquitetura consolidada
                                                  e comportamento
                                                  confiável
  -----------------------------------------------------------------------

O roadmap é uma direção, não um compromisso de implementar todos os
itens exatamente nessa ordem. As prioridades podem mudar após cada
revisão técnica.

## 5. Escopo da próxima versão: `v0.2.0`

**Tema:** Reliability & Testing.

**Objetivo:** transformar a base atual em uma aplicação testável,
previsível e preparada para receber novas capacidades.

### 5.1. Testes automatizados

-   [ ] Revisar a configuração atual do Pytest.
-   [ ] Criar fixtures para banco SQLite isolado.
-   [ ] Converter scripts manuais relevantes em testes automatizados.
-   [ ] Testar operações de conversas.
-   [ ] Testar operações de mensagens.
-   [ ] Testar o serviço de conversas.
-   [ ] Testar o gerenciamento de memória.
-   [ ] Simular respostas e falhas do provedor.

### 5.2. Configuração

-   [ ] Corrigir `.env.example`.
-   [ ] Centralizar a leitura de configurações.
-   [ ] Validar valores obrigatórios.
-   [ ] Melhorar mensagens de erro na inicialização.
-   [ ] Garantir que segredos não sejam registrados nos logs.

### 5.3. Provedor

-   [ ] Definir o ciclo de vida dos clientes.
-   [ ] Configurar timeout.
-   [ ] Tratar falhas de conexão e respostas inválidas.
-   [ ] Preparar substituição ou simulação do provedor nos testes.

### 5.4. Conversas, memória e checkpoints

-   [ ] Revisar a persistência de mensagens.
-   [ ] Testar a continuidade do histórico.
-   [ ] Testar criação, listagem, abertura e exclusão de conversas.
-   [ ] Verificar a remoção dos checkpoints associados à conversa.
-   [ ] Documentar a responsabilidade de cada mecanismo de persistência.

### 5.5. CLI e documentação

-   [ ] Melhorar o tratamento de erros.
-   [ ] Revisar o comportamento dos comandos.
-   [ ] Corrigir README.
-   [ ] Corrigir CHANGELOG.
-   [ ] Documentar configuração e execução local.

### Critérios de conclusão da `v0.2.0`

-   [ ] Pytest executa testes reais e apresenta resultados.
-   [ ] Os testes utilizam armazenamento isolado.
-   [ ] Configuração ausente ou inválida gera mensagens claras.
-   [ ] Falhas do provedor são tratadas de forma previsível.
-   [ ] O histórico de conversas permanece consistente.
-   [ ] A exclusão de uma conversa trata seus checkpoints associados.
-   [ ] Ruff, Pyright e Pre-commit continuam funcionando.
-   [ ] README e CHANGELOG refletem o projeto.

## 6. Ordem de implementação sugerida

A implementação da `v0.2.0` deve ocorrer em pequenas etapas:

1.  **Infraestrutura de testes:** revisar Pytest, criar fixtures e
    preparar banco isolado.
2.  **Persistência:** testar banco, modelos e repositórios.
3.  **Conversas:** testar o serviço e o ciclo de vida das conversas.
4.  **Agente:** simular o modelo e testar o fluxo de execução.
5.  **Configuração:** corrigir variáveis, validação e inicialização.
6.  **Provedor:** organizar clientes, timeout e tratamento de erros.
7.  **CLI:** revisar erros e comportamento dos comandos.
8.  **Documentação e release:** atualizar documentos, validar a suíte e
    preparar a release.

A ordem pode ser ajustada quando uma dependência técnica exigir.

## 7. Processo de desenvolvimento

Cada tarefa deve seguir este ciclo:

1.  **Análise:** localizar o problema no código atual e entender seu
    comportamento.
2.  **Projeto:** definir a solução e as responsabilidades envolvidas.
3.  **Implementação:** alterar apenas o necessário.
4.  **Validação:** executar testes relevantes, Ruff e Pyright.
5.  **Revisão:** verificar efeitos colaterais, simplicidade e coerência
    arquitetural.
6.  **Commit:** registrar a mudança com Conventional Commits.

### Convenção de commits

Usar mensagens no padrão Conventional Commits, por exemplo:

``` text
test: add isolated sqlite fixtures
fix: validate model provider configuration
refactor: centralize provider lifecycle
docs: update development instructions
```

A geração de versão, tag e changelog deve continuar centralizada no
Python Semantic Release, conforme a configuração do projeto.

## 8. Princípios arquiteturais

Ao evoluir o Guillotine, preservar estes princípios:

-   **Simplicidade antes de abstração:** não criar estruturas genéricas
    sem necessidade demonstrada.
-   **Modularidade com propósito:** cada módulo deve ter
    responsabilidade compreensível.
-   **Separação de responsabilidades:** interfaces não devem concentrar
    a lógica do agente.
-   **Testabilidade:** componentes importantes devem poder ser testados
    sem depender de serviços externos.
-   **Controle de recursos:** conexões, clientes e tarefas assíncronas
    devem ter ciclo de vida definido.
-   **Falhas previsíveis:** erros devem ser tratados e comunicados
    adequadamente.
-   **Segurança por padrão:** segredos não devem ser versionados ou
    expostos em logs.
-   **Evolução incremental:** implementar, validar e revisar antes de
    avançar.

## 9. Estado de acompanhamento

Atualizar esta seção ao concluir tarefas ou iniciar uma nova versão.

  -----------------------------------------------------------------------
  Campo                               Estado
  ----------------------------------- -----------------------------------
  Versão publicada registrada         `v0.1.0`

  Próxima versão planejada            `v0.2.0`

  Tema atual                          Confiabilidade e testes

  Próxima tarefa                      Preparar infraestrutura do Pytest e
                                      isolamento do SQLite

  Estratégia                          Implementação incremental
  -----------------------------------------------------------------------

### Registro de decisões e progresso

Adicionar entradas curtas conforme o projeto evoluir:

``` text
## Histórico de progresso

- [AAAA-MM-DD] Decisão ou tarefa concluída.
- [AAAA-MM-DD] Problema encontrado e solução adotada.
```

------------------------------------------------------------------------

**Nota:** este documento registra o diagnóstico de uma revisão do
snapshot `v0.1.0`. Antes de executar qualquer tarefa, conferir o estado
atual do repositório e atualizar este documento quando uma decisão,
implementação ou prioridade mudar.
