# Guillotine 🇫🇷

<h1 align="center">
  <a href="https://github.com/guilherme-o-lindo/guillotine-ai">
    <img
      align="center"
      src="assets/banner.png"
      alt="Guillotine — Seu assistente de IA, do seu jeito."
      width="100%"
    />
  </a>
</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>&#32;
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
  Um assistente de inteligência artificial modular, extensível e independente de provedores.
</p>

## 🌐 Idiomas

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇧🇷_Português-6E40C9?style=for-the-badge" alt="Português"></a>&#32;
  <a href=""><img src="https://img.shields.io/badge/🇺🇸_English-8B5CF6?style=for-the-badge" alt="English — em breve"></a>
</p>

## ⚡ Quick-start

O Guillotine tem como objetivo reunir diferentes modelos, ferramentas e serviços de inteligência artificial em um único assistente personalizável.

```bash
# Clone o repositório
git clone https://github.com/guilherme-o-lindo/guillotine-ai.git

# Entre na pasta
cd guillotine

# Instale as dependências
uv sync

# Execute o assistente
uv run guillotine
```

Consulte a seção de [instalação](#-instalação) para obter mais informações sobre a configuração do ambiente.

## 🧠 Sobre o projeto

**Guillotine** é um assistente de inteligência artificial desenvolvido em Python, com o objetivo de simplificar a interação com diferentes modelos e serviços de IA por meio de uma arquitetura modular e extensível.

A proposta é oferecer uma experiência unificada, permitindo utilizar diferentes provedores, ferramentas e interfaces sem depender de um único modelo ou serviço.

O projeto busca tornar a inteligência artificial mais acessível, flexível e personalizável, mantendo o controle sobre os dados, as integrações e as permissões concedidas ao agente.

Mais do que um simples cliente de IA, o Guillotine pretende funcionar como uma estrutura central capaz de coordenar modelos, ferramentas e diferentes formas de interação.

## ✨ Diferenciais

<table>
  <tbody>
    <tr>
      <td><strong>Independência de provedores</strong></td>
      <td>Uma camada unificada para trabalhar com diferentes modelos e serviços de inteligência artificial, reduzindo a dependência de fornecedores específicos.</td>
    </tr>
    <tr>
      <td><strong>Arquitetura modular</strong></td>
      <td>Componentes organizados por responsabilidade, permitindo adicionar ou modificar funcionalidades sem comprometer todo o sistema.</td>
    </tr>
    <tr>
      <td><strong>Integração com ferramentas</strong></td>
      <td>Uma estrutura para conectar o agente a ferramentas internas e serviços externos, incluindo integrações por meio do Model Context Protocol (MCP).</td>
    </tr>
    <tr>
      <td><strong>Controle de permissões</strong></td>
      <td>Execução de ações orientada por permissões e confirmação do usuário, mantendo o controle sobre o que o agente pode realizar.</td>
    </tr>
    <tr>
      <td><strong>Memória persistente</strong></td>
      <td>Uma estrutura de armazenamento para preservar informações relevantes e permitir continuidade entre diferentes sessões.</td>
    </tr>
    <tr>
      <td><strong>Múltiplas interfaces</strong></td>
      <td>Uma base preparada para diferentes formas de interação, como terminal, voz e API.</td>
    </tr>
    <tr>
      <td><strong>Flexibilidade</strong></td>
      <td>Possibilidade de adaptar o comportamento do assistente conforme a tarefa, o modelo utilizado e as ferramentas disponíveis.</td>
    </tr>
  </tbody>
</table>

## 🚀 Funcionalidades

O Guillotine está em desenvolvimento. As funcionalidades abaixo representam os objetivos do projeto e serão implementadas gradualmente.

- [ ] **Modelos e provedores**
  - [ ] Comunicação com diferentes provedores e modelos de IA.
  - [ ] Roteamento de modelos.
  - [ ] Configuração independente de provedor e modelo.

- [ ] **Agente**
  - [ ] Sistema central de gerenciamento do agente.
  - [ ] Gerenciamento de contexto e histórico de conversas.
  - [ ] Comandos e modos de operação.

- [ ] **Ferramentas**
  - [ ] Sistema de registro e execução de ferramentas internas.
  - [ ] Integração com servidores MCP.
  - [ ] Gerenciamento de permissões e confirmação de ações.

- [ ] **Memória**
  - [ ] Memória persistente com SQLite.
  - [ ] Gerenciamento de conversas e informações relevantes.

- [ ] **Interfaces**
  - [ ] Interface de linha de comando (CLI).
  - [ ] Interação por voz.
  - [ ] API para integração com outras aplicações.

## 🏗️ Arquitetura

O Guillotine busca utilizar uma arquitetura modular, separando as principais responsabilidades do agente para facilitar a manutenção, compreensão e expansão do projeto.

| Módulo       | Responsabilidade                                     |
| ------------ | ---------------------------------------------------- |
| `core`       | Lógica central, contexto e comportamento do agente.  |
| `models`     | Comunicação e roteamento entre modelos e provedores. |
| `tools`      | Registro, gerenciamento e execução de ferramentas.   |
| `memory`     | Gerenciamento de memória e persistência de dados.    |
| `interfaces` | Interfaces de interação, como CLI, voz e API.        |
| `config`     | Configurações e variáveis de ambiente.               |

A separação dos componentes busca manter o sistema organizado e evitar dependências desnecessárias entre módulos.

A arquitetura poderá evoluir conforme as necessidades do projeto, sem adotar abstrações que não tragam benefícios reais.

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

### Bibliotecas planejadas

<p align="center">
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic">
  <img src="https://img.shields.io/badge/AnyIO-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="AnyIO">
  <img src="https://img.shields.io/badge/Uvicorn-4051B5?style=for-the-badge&logo=gunicorn&logoColor=white" alt="Uvicorn">
</p>

| Tecnologia | Finalidade |
|:---|:---|
| [Pydantic](https://docs.pydantic.dev/) | Validação, serialização e estruturação de dados. |
| [AnyIO](https://anyio.readthedocs.io/) | Abstração para operações assíncronas. |
| [Uvicorn](https://www.uvicorn.org/) | Servidor ASGI para execução da futura API. |

### Desenvolvimento e qualidade de código

<p align="center">
  <img src="https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black" alt="Ruff">
  <img src="https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
  <img src="https://img.shields.io/badge/Commitizen-000000?style=for-the-badge&logo=commitlint&logoColor=white" alt="Commitizen">
  <img src="https://img.shields.io/badge/Semantic_Release-494949?style=for-the-badge&logo=semanticrelease&logoColor=white" alt="Python Semantic Release">
  <img src="https://img.shields.io/badge/Pre--commit-FAB040?style=for-the-badge&logo=pre-commit&logoColor=black" alt="Pre-commit">
</p>

| Tecnologia | Finalidade |
|:---|:---|
| [Ruff](https://docs.astral.sh/ruff/) | Análise estática, identificação de problemas e formatação de código. |
| [Pytest](https://docs.pytest.org/) | Criação e execução de testes automatizados. |
| [Commitizen](https://commitizen-tools.github.io/commitizen/) | Padronização de mensagens de commit. |
| [Python Semantic Release](https://python-semantic-release.readthedocs.io/) | Automação do versionamento e geração de releases. |
| [Pre-commit](https://pre-commit.com/) | Execução de verificações automáticas antes dos commits. |

## 📦 Instalação

### Pré-requisitos

- Python 3.12 ou superior.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- [Git](https://git-scm.com/).

### 1. Clonando o repositório

```bash
git clone https://github.com/guilherme-o-lindo/guillotine-ai.git

cd guillotine
```

### 2. Instalando as dependências

Utilize o uv para criar o ambiente virtual e instalar as dependências do projeto:

```bash
uv sync
```

### 3. Configuração

Crie um arquivo `.env` a partir do modelo disponibilizado no repositório:

```bash
cp .env.example .env
```

Configure as variáveis necessárias de acordo com o provedor e os serviços utilizados.

> Não compartilhe seu arquivo `.env` nem envie chaves de API para o repositório.

### 4. Executando

```bash
uv run guillotine
```

## 🗺️ Roadmap

O desenvolvimento será dividido em etapas, priorizando primeiro os fundamentos do agente e depois a expansão de suas capacidades.

1. **Fundamentos:** estrutura do projeto, configurações e gerenciamento do agente.
2. **Modelos:** integração com provedores e roteamento de modelos.
3. **Ferramentas:** sistema interno de ferramentas e integração MCP.
4. **Memória:** gerenciamento de conversas e persistência de informações.
5. **Interfaces:** CLI, voz e API.
6. **Expansão:** novas integrações, funcionalidades e melhorias de experiência.

## 🤝 Contribuições

O Guillotine está em desenvolvimento e contribuições são bem-vindas.

Sugestões, correções, melhorias e novas ideias podem ser compartilhadas por meio das [Issues](https://github.com/guilherme-o-lindo/guillotine-ai/issues) ou de Pull Requests.

Antes de contribuir, procure manter os padrões de organização, nomenclatura e mensagens de commit utilizados no projeto.

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).