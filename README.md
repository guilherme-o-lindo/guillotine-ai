# Guillotine 🇫🇷

<h1 align="center">
  <a href="https://github.com/guilherme-o-lindo/guillotine-ai">
    <img align="center" src="assets/banner.png" alt="Guillotine — Seu assistente de IA, do seu jeito." width="100%" />
  </a>
</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>&#32;
  <img src="https://img.shields.io/badge/Version-0.1.0-blue?style=for-the-badge" alt="Version 0.1.0">&#32;
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+">&#32;
  <img src="https://img.shields.io/badge/uv-managed-6E40C9?style=for-the-badge&logo=uv&logoColor=white" alt="uv">&#32;
  <img src="https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge" alt="In Development">
</p>

<p align="center">
  <a href="#-sobre-o-projeto"><img alt="Sobre" src="https://img.shields.io/badge/🧠_Sobre-6E40C9?style=flat-square"></a>&#32;
  <a href="#-diferenciais"><img alt="Diferenciais" src="https://img.shields.io/badge/✨_Diferenciais-8B5CF6?style=flat-square"></a>&#32;
  <a href="#-funcionalidades"><img alt="Funcionalidades" src="https://img.shields.io/badge/🚀_Funcionalidades-6E40C9?style=flat-square"></a>&#32;
  <a href="#-tecnologias"><img alt="Tecnologias" src="https://img.shields.io/badge/🔌_Tecnologias-8B5CF6?style=flat-square"></a>&#32;
  <a href="#-instalação"><img alt="Instalação" src="https://img.shields.io/badge/📦_Instalação-6E40C9?style=flat-square"></a>&#32;
  <a href="#-roadmap"><img alt="Roadmap" src="https://img.shields.io/badge/🗺️_Roadmap-8B5CF6?style=flat-square"></a>&#32;
  <a href="#-contribuições"><img alt="Contribuições" src="https://img.shields.io/badge/🤝_Contribuições-6E40C9?style=flat-square"></a>
</p>

<p align="center">
  Um assistente pessoal de inteligência artificial modular, extensível e independente de provedores.
</p>

## 🌐 Idiomas

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇧🇷_Português-6E40C9?style=for-the-badge" alt="Português"></a>&#32;
  <img src="https://img.shields.io/badge/🇺🇸_English-8B5CF6?style=for-the-badge" alt="English — em breve">
</p>

## ⚡ Quick-start

O Guillotine busca reunir modelos, memória e ferramentas de inteligência artificial em um único assistente personalizável.

```bash
# Clone o repositório
git clone https://github.com/guilherme-o-lindo/guillotine-ai.git

# Entre na pasta
cd guillotine-ai

# Instale as dependências
uv sync

# Execute o assistente
uv run guillotine
```

Consulte a seção de [instalação](#-instalação) para obter mais informações sobre a configuração do ambiente.

## 🧠 Sobre o projeto

**Guillotine** é um assistente pessoal de inteligência artificial desenvolvido em Python, com o objetivo de centralizar e simplificar a interação com modelos de IA por meio de uma arquitetura modular.

A proposta é construir um sistema capaz de coordenar modelos, memória, ferramentas e diferentes interfaces de interação, mantendo flexibilidade sobre as tecnologias e os serviços utilizados.

Mais do que um simples cliente de IA, o Guillotine pretende funcionar como uma estrutura central de assistência pessoal, na qual diferentes componentes possam trabalhar em conjunto sem criar dependências desnecessárias entre eles.

A versão `v0.1.0` estabelece a base funcional do projeto, incluindo integração com modelos, gerenciamento de conversas, persistência local e interface de linha de comando.

## ✨ Diferenciais

<table>
  <tbody>
    <tr>
      <td><strong>Independência de provedores</strong></td>
      <td>Integração por meio de uma API compatível com OpenAI, permitindo utilizar serviços que implementem esse formato.</td>
    </tr>
    <tr>
      <td><strong>Arquitetura modular</strong></td>
      <td>Componentes organizados por responsabilidade, facilitando a manutenção e a evolução independente das partes do sistema.</td>
    </tr>
    <tr>
      <td><strong>Gerenciamento de conversas</strong></td>
      <td>Criação, recuperação, listagem e exclusão de conversas, com persistência do histórico de mensagens.</td>
    </tr>
    <tr>
      <td><strong>Persistência local</strong></td>
      <td>Armazenamento de conversas e mensagens utilizando SQLite, além de checkpoints para o fluxo de execução.</td>
    </tr>
    <tr>
      <td><strong>Execução estruturada</strong></td>
      <td>Utilização de PydanticAI e LangGraph na construção e organização do fluxo do agente.</td>
    </tr>
    <tr>
      <td><strong>Extensibilidade</strong></td>
      <td>Estrutura preparada para receber ferramentas, integrações MCP, novas interfaces e capacidades de memória.</td>
    </tr>
  </tbody>
</table>

## 🚀 Funcionalidades

O Guillotine está em desenvolvimento. Abaixo estão as funcionalidades disponíveis na versão atual e as capacidades planejadas para as próximas versões.

### Implementadas — v0.1.0

- [x] **Agente**
  - [x] Agente central utilizando PydanticAI.
  - [x] Execução assíncrona de solicitações.
  - [x] Fluxo de execução estruturado com LangGraph.
  - [x] Instruções próprias para o comportamento do agente.

- [x] **Modelos e provedores**
  - [x] Comunicação com APIs compatíveis com OpenAI.
  - [x] Configuração de modelo, endpoint e chave de API por variáveis de ambiente.

- [x] **Conversas e histórico**
  - [x] Criação e exclusão de conversas.
  - [x] Listagem e abertura de conversas existentes.
  - [x] Recuperação do histórico de mensagens.
  - [x] Continuidade do contexto entre mensagens.

- [x] **Persistência**
  - [x] Armazenamento local utilizando SQLite e aiosqlite.
  - [x] Persistência de checkpoints com LangGraph.

- [x] **Interface**
  - [x] Interface de linha de comando (CLI).
  - [x] Comandos para gerenciamento de conversas.

### Em desenvolvimento

- [ ] Testes automatizados abrangentes.
- [ ] Aprimoramento do tratamento de erros.
- [ ] Refinamento do gerenciamento de configurações.
- [ ] Melhorias no gerenciamento de contexto e histórico.
- [ ] Tratamento de falhas e ciclo de vida dos provedores.

### Planejadas

- [ ] **Modelos e provedores**
  - [ ] Suporte a diferentes provedores.
  - [ ] Roteamento inteligente entre modelos.
  - [ ] Seleção de modelos conforme a complexidade das tarefas.

- [ ] **Ferramentas**
  - [ ] Sistema de registro e execução de ferramentas internas.
  - [ ] Integração com servidores MCP.
  - [ ] Gerenciamento de permissões.
  - [ ] Confirmação de ações sensíveis.

- [ ] **Memória**
  - [ ] Memória de conhecimento.
  - [ ] Armazenamento e recuperação de preferências.
  - [ ] Recuperação contextual de informações.

- [ ] **Interfaces**
  - [ ] API para integração com outras aplicações.
  - [ ] Interação por voz.
  - [ ] Evolução da experiência de terminal.

- [ ] **Autonomia**
  - [ ] Planejamento de tarefas em múltiplas etapas.
  - [ ] Execução controlada de ações.
  - [ ] Checkpoints e aprovação humana.

## 🏗️ Arquitetura

O Guillotine utiliza uma arquitetura modular organizada por responsabilidades. A estrutura atual separa a lógica central do agente, os modelos, a memória, os serviços, as ferramentas e as interfaces.

```text
src/
└── guillotine/
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

### Responsabilidades

| Módulo | Responsabilidade |
|:---|:---|
| `core` | Lógica central do agente, contexto, fluxo de execução e ciclo de vida. |
| `models` | Integração com modelos e provedores. |
| `memory` | Gerenciamento de conversas, mensagens e persistência. |
| `services` | Coordenação dos casos de uso da aplicação. |
| `tools` | Estrutura para registro, execução e integração de ferramentas. |
| `interfaces` | Pontos de interação com o usuário e outros sistemas. |

A estrutura também contém módulos preparados para funcionalidades futuras. Nem todos os componentes estão implementados na `v0.1.0`.

## 🔌 Tecnologias

### Linguagem e gerenciamento

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/uv-6E40C9?style=for-the-badge&logo=uv&logoColor=white" alt="uv">
</p>

| Tecnologia | Finalidade |
|:---|:---|
| [Python](https://www.python.org/) | Linguagem principal do projeto. |
| [uv](https://docs.astral.sh/uv/) | Gerenciamento de dependências, ambientes virtuais e execução de comandos. |

### Agente e modelos

<p align="center">
  <img src="https://img.shields.io/badge/PydanticAI-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="PydanticAI">
  <img src="https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge" alt="LangGraph">
  <img src="https://img.shields.io/badge/OpenAI_API-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI API">
</p>

| Tecnologia | Finalidade |
|:---|:---|
| [PydanticAI](https://ai.pydantic.dev/) | Construção e execução do agente. |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | Estruturação do fluxo de execução e persistência de checkpoints. |
| [OpenAI Python SDK](https://github.com/openai/openai-python) | Comunicação com APIs compatíveis com o formato OpenAI. |

### Persistência

<p align="center">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
</p>

| Tecnologia | Finalidade |
|:---|:---|
| [SQLite](https://www.sqlite.org/) | Banco de dados local para conversas e mensagens. |
| [aiosqlite](https://aiosqlite.omnilib.dev/) | Operações assíncronas com SQLite. |
| [LangGraph Checkpoint SQLite](https://pypi.org/project/langgraph-checkpoint-sqlite/) | Persistência dos checkpoints do fluxo do agente. |

### Desenvolvimento e qualidade de código

<p align="center">
  <img src="https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black" alt="Ruff">
  <img src="https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
  <img src="https://img.shields.io/badge/Pyright-3776AB?style=for-the-badge" alt="Pyright">
  <img src="https://img.shields.io/badge/Pre--commit-FAB040?style=for-the-badge&logo=pre-commit&logoColor=black" alt="Pre-commit">
</p>

| Tecnologia | Finalidade |
|:---|:---|
| [Ruff](https://docs.astral.sh/ruff/) | Análise estática, identificação de problemas e formatação de código. |
| [Pytest](https://docs.pytest.org/) | Framework para criação e execução de testes automatizados. |
| [Pyright](https://github.com/microsoft/pyright) | Verificação estática de tipos. |
| [Pre-commit](https://pre-commit.com/) | Execução de verificações antes dos commits. |
| [Commitizen](https://commitizen-tools.github.io/commitizen/) | Padronização de mensagens de commit. |
| [Python Semantic Release](https://python-semantic-release.readthedocs.io/) | Automação de versões, tags e changelog. |

## 📦 Instalação

### Pré-requisitos

- Python 3.12 ou superior.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- [Git](https://git-scm.com/).

### 1. Clonando o repositório

```bash
git clone https://github.com/guilherme-o-lindo/guillotine-ai.git

cd guillotine-ai
```

### 2. Instalando as dependências

Utilize o uv para criar o ambiente virtual e instalar as dependências:

```bash
uv sync
```

### 3. Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
GUILLOTINE_MODEL=seu-modelo
GUILLOTINE_BASE_URL=http://localhost:20128/v1
GUILLOTINE_API_KEY=sua-chave
```

Configure os valores de acordo com o provedor utilizado.

O endpoint apresentado é um exemplo de configuração para um serviço local. Ele pode ser substituído por outro endpoint compatível com a API OpenAI.

> **Importante:** não compartilhe seu arquivo `.env` nem envie chaves de API para o repositório.

### 4. Executando o Guillotine

```bash
uv run guillotine
```

Também é possível executar diretamente pelo módulo:

```bash
uv run python -m guillotine.main
```

O banco de dados SQLite é armazenado localmente em `data/guillotine.db`.

## 💻 Comandos da CLI

A versão `v0.1.0` disponibiliza comandos para interação e gerenciamento de conversas:

| Comando | Descrição |
|:---|:---|
| `/nova` | Inicia uma nova conversa. |
| `/conversas` | Lista as conversas existentes. |
| `/abrir ID` | Abre uma conversa pelo identificador. |
| `/historico` | Exibe o histórico da conversa atual. |
| `/excluir` | Exclui a conversa atual e inicia outra. |
| `/ajuda` | Exibe os comandos disponíveis. |
| `/sair` | Encerra o Guillotine. |

Mensagens que não correspondem a comandos são encaminhadas ao agente.

## 🗺️ Roadmap

O desenvolvimento do Guillotine será dividido em versões incrementais, priorizando a confiabilidade da base antes da expansão de funcionalidades.

| Versão | Objetivo |
|:---|:---|
| `v0.1.0` | MVP: agente, conversas, persistência e CLI. |
| `v0.2.0` | Confiabilidade: testes, configuração e tratamento de erros. |
| `v0.3.0` | Ferramentas: registry, executor e integração MCP. |
| `v0.4.0` | Memória inteligente: conhecimento e preferências. |
| `v0.5.0` | Interfaces: evolução da CLI e implementação da API. |
| `v0.6.0` | Autonomia controlada: planejamento e execução em etapas. |
| `v0.7.0` | Segurança e observabilidade: permissões, logs e métricas. |
| `v1.0.0` | Estabilidade: consolidação da arquitetura e das funcionalidades. |

O roadmap representa a direção planejada do projeto e pode ser ajustado conforme as necessidades técnicas identificadas durante o desenvolvimento.

## 🤝 Contribuições

O Guillotine está em desenvolvimento e contribuições são bem-vindas.

Sugestões, correções e melhorias podem ser compartilhadas por meio das [Issues](https://github.com/guilherme-o-lindo/guillotine-ai/issues) ou de Pull Requests.

Ao contribuir:

- Mantenha os padrões de organização e nomenclatura do projeto.
- Utilize mensagens de commit no padrão [Conventional Commits](https://www.conventionalcommits.org/).
- Execute as verificações de qualidade antes de enviar alterações.

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).