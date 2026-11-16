<div align="center">

<a href="https://github.com/guilherme-o-lindo/guillotine-ai">
  <img src="assets/banner.png" alt="Guillotine — assistente pessoal de IA" width="100%">
</a>

# Guillotine 🇫🇷

**Seu assistente pessoal de IA, do seu jeito.**

Agente modular em Python com conversas persistentes, ferramentas locais, integração MCP e execução controlada por permissões.

<p>
  <a href="LICENSE"><img src="https://img.shields.io/static/v1?label=License&message=MIT&color=16A34A&style=flat-square" alt="Licença MIT"></a>
  <a href="https://github.com/guilherme-o-lindo/guillotine-ai/releases/tag/v0.3.0"><img src="https://img.shields.io/static/v1?label=Released&message=v0.3.0&color=7C3AED&style=flat-square" alt="Versão publicada: v0.3.0"></a>
  <img src="https://img.shields.io/static/v1?label=Next&message=v0.4.0%20planned&color=9333EA&style=flat-square" alt="Próxima versão planejada: v0.4.0">
  <img src="https://img.shields.io/static/v1?label=Python&message=3.12%2B&color=3776AB&style=flat-square&logo=python&logoColor=white" alt="Python 3.12 ou superior">
  <img src="https://img.shields.io/static/v1?label=QA&message=417%20passed&color=16A34A&style=flat-square" alt="QA: 417 testes aprovados">
</p>

[Visão geral](#visão-geral) · [Funcionalidades](#funcionalidades) · [Instalação](#instalação) · [CLI](#cli) · [Arquitetura](#arquitetura) · [Qualidade](#qualidade-e-testes) · [Roadmap](#roadmap) · [Status técnico](GUILLOTINE_PROJECT_STATUS.md)

</div>

> **Estado do projeto — 16/11/2026:** **`v0.3.0` publicada.** O Python Semantic Release gerou o commit `fd2f36f`, atualizou o changelog, criou a tag `v0.3.0` (confirmada no remoto) e produziu wheel/sdist `0.3.0`. O QA final registrou **417 testes aprovados, 1 ignorado e 89,48% de cobertura**. Próxima versão planejada: `v0.4.0`.

## Visão geral

O **Guillotine** é um assistente pessoal de inteligência artificial desenvolvido em Python. Seu objetivo é reunir interação com modelos, gerenciamento de conversas, memória e ferramentas em uma aplicação extensível, mantendo controle explícito sobre as operações executadas.

A trajetória do projeto é incremental: `v0.1.0` estabeleceu o MVP, `v0.2.0` melhorou a confiabilidade e `v0.3.0` entregou ferramentas locais e MCP com permissões, aprovações e auditoria. A interface principal atual é uma CLI; API e voz continuam no roadmap.

## Funcionalidades

| Área | Implementação disponível na `v0.3.0` |
|:--|:--|
| **Agente e modelos** | PydanticAI, execução assíncrona e APIs compatíveis com OpenAI; configuração de modelo, endpoint, chave e timeout |
| **Orquestração** | LangGraph e checkpoints SQLite |
| **Conversas** | Criar, listar, abrir e excluir conversas; recuperar histórico e persistir mensagens em SQLite |
| **Ferramentas** | Catálogo de ferramentas, registry, executor, bridge com PydanticAI e validação de argumentos via JSON Schema |
| **MCP** | Conexão e gerenciamento de servidores MCP, incluindo transportes stdio e Streamable HTTP |
| **Integrações MCP testadas** | Git com operações selecionadas de **leitura** e DuckDuckGo para buscas e expansão de links |
| **Web local** | Safe Fetch com verificações de SSRF, limites de resposta, validação de TLS e tratamento de redirecionamentos; extração de conteúdo HTML/XHTML |
| **Arquivos locais** | Listagem, leitura de arquivos UTF-8 e pesquisa limitada à raiz configurada pelo usuário |
| **Controle de execução** | Escopos de recursos, permissões, solicitações de aprovação, registro de auditoria e tratamento de falhas |
| **Qualidade** | Ruff, Pyright strict, Pytest com cobertura, Bandit, pip-audit e GitHub Actions (`qa.yml`) |

### Limites importantes

- **Git MCP:** as operações selecionadas atualmente são somente de leitura. Escritas, commits, merges e outras alterações de repositório por ferramentas do agente ficam para uma evolução posterior.
- **Arquivos locais:** acesso opt-in por `GUILLOTINE_FILE_ROOT`, relativo à raiz permitida, com limites de tamanho/quantidade e rejeição de caminhos fora do escopo, symlinks e junctions nas verificações implementadas. **Não constitui sandbox resistente a ataques de troca de arquivos entre checagem e abertura (TOCTOU)**; utilize diretórios confiáveis.
- **Safe Fetch:** não é um navegador irrestrito. Aplica verificações de endereços e redirecionamentos para reduzir riscos de SSRF, além de limites de conteúdo.
- **MCP:** servidores externos devem ser tratados como integrações com seus próprios riscos; permissões e escopos continuam sendo aplicados pelo Guillotine.
- **Interface:** o redesenho completo da experiência de terminal, API, voz e memória inteligente ainda não fazem parte da entrega atual.

## Início rápido

Pré-requisitos: **Python 3.12+**, [uv](https://docs.astral.sh/uv/) e Git.

```powershell
# Clonar e entrar na pasta
git clone https://github.com/guilherme-o-lindo/guillotine-ai.git
cd guillotine-ai

# Instalar dependências
uv sync

# Criar arquivo local de ambiente
Copy-Item .env.example .env

# Após configurar o .env, iniciar o assistente
uv run --env-file .env guillotine
```

Em Unix/macOS, substitua `Copy-Item` por `cp .env.example .env`. A opção `--env-file .env` carrega explicitamente as variáveis de ambiente; o `uv run` sem essa opção não carrega automaticamente esse arquivo por padrão.

### Configuração básica

Exemplo de variáveis para um endpoint compatível com OpenAI:

```dotenv
GUILLOTINE_MODEL=seu-modelo
GUILLOTINE_BASE_URL=http://localhost:20128/v1
GUILLOTINE_API_KEY=sua-chave
GUILLOTINE_TIMEOUT=60

# Opcional: autorizar ferramentas locais de arquivos
# GUILLOTINE_FILE_ROOT=C:\\Users\\User\\Documents
```

O endereço `localhost:20128` ilustra o uso com um endpoint local, como o 9Router; ajuste para o seu provedor. Sem `GUILLOTINE_FILE_ROOT`, as ferramentas locais de arquivos não devem receber uma raiz autorizada. A configuração de servidores MCP é separada dessas variáveis; consulte os comandos de ajuda da instalação para os recursos disponíveis.

> **Segurança:** nunca versione `.env`, credenciais, tokens ou arquivos privados. A variável `GH_TOKEN` existente no exemplo original não é requisito comprovado para a inicialização básica do Guillotine.

## CLI

A CLI atual permite conversar com o agente e gerenciar sessões:

| Comando | Finalidade |
|:--|:--|
| `/nova` | Iniciar conversa |
| `/conversas` | Listar conversas |
| `/abrir ID` | Retomar conversa pelo identificador |
| `/historico` | Ver mensagens da conversa atual |
| `/excluir` | Excluir conversa atual |
| `/ajuda` | Consultar comandos, inclusive integrações disponíveis |
| `/sair` | Encerrar a aplicação |

Mensagens sem comando são encaminhadas ao agente. A CLI também incorpora integração MCP e pedidos de aprovação; os nomes e argumentos dos subcomandos devem ser consultados na ajuda da versão instalada, evitando instruções desatualizadas.

## Arquitetura

A estrutura de ferramentas implementada na `v0.3.0` está organizada por responsabilidades:

```text
src/guillotine/
├── core/
│   ├── agent.py
│   ├── lifecycle.py
│   ├── mcp_configuration.py
│   ├── permissions.py
│   ├── permission_store.py
│   ├── approvals.py
│   └── tool_audit.py
├── interfaces/
│   ├── cli.py
│   ├── mcp_commands.py
│   └── approval_prompt.py
├── memory/
│   ├── manager.py
│   ├── repositories/
│   └── storage/
├── models/
│   ├── provider.py
│   ├── router.py
│   └── errors.py
├── services/
│   └── conversations.py
├── tools/
│   ├── bridges/pydantic_ai.py
│   ├── core/
│   │   ├── contracts.py
│   │   ├── registry.py
│   │   └── executor.py
│   ├── local/
│   │   ├── safe_fetch.py
│   │   ├── web_fetch.py
│   │   ├── html_extract.py
│   │   ├── html_response.py
│   │   ├── file_reader.py
│   │   └── file_tools.py
│   └── mcp/
│       ├── client.py
│       └── manager.py
└── main.py
```

*Árvore resumida dos componentes relevantes; não pretende listar todos os arquivos do pacote.*

| Camada | Papel |
|:--|:--|
| `core/` | Agente, lifecycle, configuração, permissões, aprovações e auditoria |
| `interfaces/` | CLI e interação humana com comandos e aprovações |
| `memory/` | Conversas, mensagens, repositórios e persistência |
| `models/` | Provedor e tratamento de falhas de modelos |
| `services/` | Coordenação de casos de uso |
| `tools/core/` | Contratos, registro e execução controlada |
| `tools/bridges/` | Adaptação das ferramentas para o agente |
| `tools/local/` | Integrações web e arquivos locais |
| `tools/mcp/` | Clientes e gerenciamento de servidores MCP |

Tecnologias principais: Python, uv, PydanticAI, LangGraph, SQLite/aiosqlite, SDK MCP, JSON Schema, HTTPX/httpx2, truststore, Pytest, Ruff, Pyright, Bandit e pip-audit. A presença de uma dependência não implica utilização em todos os fluxos.

## Qualidade e testes

**Última validação informada: 15–16/11/2026, Windows / Python 3.12.16.**

| Verificação | Resultado |
|:--|:--|
| Ruff lint | Aprovado |
| Ruff format | 102 arquivos já formatados |
| Pyright strict | 0 erros / 0 avisos |
| Pytest | **417 aprovados**, 1 ignorado (symlink indisponível no ambiente) |
| Cobertura total | **89,48%**, acima do mínimo de 85% |
| Bandit | Sem problemas de severidade média ou alta; 5 achados de baixa severidade |
| pip-audit | Nenhuma vulnerabilidade conhecida nas dependências auditáveis; pacote local `guillotine` não auditado no PyPI |
| `uv build` | Wheel e sdist `0.3.0` gerados com sucesso durante o release |

```powershell
# Pipeline de QA disponível no projeto
uv run guillotine-dev qa

# Comandos individuais
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
uv build
```

Para instalar os hooks de commit:

```powershell
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

O **Commitizen** valida mensagens Conventional Commits. O **python-semantic-release** calcula e aplica versões; não execute `cz bump` paralelamente ao fluxo de release. O hook do Pyright utiliza `uv run --no-sync pyright` para não alterar o lockfile durante commits.

### Release

A **`v0.3.0` foi publicada** a partir da branch `main`, com changelog e tag gerados pelo Python Semantic Release. Artefatos gerados: `guillotine-0.3.0.tar.gz` e `guillotine-0.3.0-py3-none-any.whl`. Para futuras versões, após QA e com um token GitHub configurado no `.env`, o fluxo é:

```powershell
# Consultar a próxima versão sem modificar o repositório
uv run --env-file .env --no-sync semantic-release version --print

# Efetuar o release e publicar os artefatos (comandos com efeitos remotos)
uv run --env-file .env --no-sync semantic-release version
uv run --env-file .env --no-sync semantic-release publish
```

Esses comandos devem ser executados somente na branch de publicação e com a árvore de trabalho limpa. O `.env` e o token não devem ser versionados. Consulte o [registro técnico da v0.3.0](GUILLOTINE_PROJECT_STATUS.md#4-release-da-v030--concluído) para o histórico do release.

## Roadmap

| Versão | Tema | Situação |
|:--|:--|:--|
| `v0.1.0` | MVP: agente, conversas, CLI e SQLite | Concluída e publicada |
| `v0.2.0` | Confiabilidade, testes e ciclo de vida | Concluída e publicada |
| `v0.3.0` | Registry, executor, MCP, permissões, ferramentas web e arquivos locais | **Concluída e publicada** |
| `v0.4.0` | Memória inteligente e recuperação contextual | Planejada |
| `v0.5.0` | Evolução da CLI e interfaces | Planejada |
| `v0.6.0` | Autonomia e execução em etapas | Planejada |
| `v0.7.0` | Segurança e observabilidade avançadas | Planejada; controles básicos já existem |
| `v1.0.0` | Consolidação e estabilidade | Planejada |

O roadmap é orientativo e pode mudar. Detalhes das decisões e pendências estão no [documento de status técnico](GUILLOTINE_PROJECT_STATUS.md).

## Contribuições

Contribuições são bem-vindas via [Issues](https://github.com/guilherme-o-lindo/guillotine-ai/issues) e Pull Requests. Utilize Conventional Commits e execute o QA relevante antes de enviar mudanças.

## Licença

Distribuído sob a [licença MIT](LICENSE).
