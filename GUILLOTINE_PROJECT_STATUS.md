<div align="center">

<a href="https://github.com/guilherme-o-lindo/guillotine-ai">
  <img src="assets/banner.png" alt="Guillotine — assistente pessoal de IA" width="100%">
</a>

# Guillotine 🇫🇷

**Estado do Projeto e Plano de Evolução**

Documento de continuidade técnica: entregas, decisões arquiteturais, qualidade, riscos conhecidos e próximos passos.

<p>
  <a href="LICENSE"><img src="https://img.shields.io/static/v1?label=License&message=MIT&color=16A34A&style=flat-square" alt="Licença MIT"></a>
  <a href="https://github.com/guilherme-o-lindo/guillotine-ai/releases/tag/v0.3.0"><img src="https://img.shields.io/static/v1?label=Released&message=v0.3.0&color=7C3AED&style=flat-square" alt="Versão publicada: v0.3.0"></a>
  <img src="https://img.shields.io/static/v1?label=Next&message=v0.4.0%20planned&color=9333EA&style=flat-square" alt="Próxima versão planejada: v0.4.0">
  <img src="https://img.shields.io/static/v1?label=Python&message=3.12%2B&color=3776AB&style=flat-square&logo=python&logoColor=white" alt="Python 3.12 ou superior">
  <img src="https://img.shields.io/static/v1?label=QA&message=417%20passed&color=16A34A&style=flat-square" alt="QA: 417 testes aprovados">
</p>

[README](README.md) · [Resumo](#1-resumo-executivo) · [Implementação](#2-estado-da-implementação) · [QA](#3-validação-e-qualidade) · [Release](#4-release-da-v030--concluído) · [Riscos](#5-limitações-e-pontos-de-atenção) · [Roadmap](#6-roadmap) · [Histórico](#9-registro-de-progresso)

</div>

> **Snapshot — 16/11/2026:** a **`v0.3.0` foi lançada** por meio do Python Semantic Release `10.7.0`. O commit de release `fd2f36f` (`chore(release): 0.3.0`) está em `main` e `origin/main`; a tag `v0.3.0` foi confirmada localmente e no remoto. O build gerou wheel e sdist `0.3.0`, e o comando de publicação foi executado com sucesso. A próxima versão planejada é a `v0.4.0`.

## 1. Resumo executivo

O **Guillotine** é um agente pessoal de IA em Python com interface CLI, integração com APIs de modelos compatíveis com OpenAI, conversas persistidas em SQLite e fluxo de execução estruturado por LangGraph/PydanticAI. O projeto adota arquitetura modular e evolução incremental.

A `v0.1.0` entregou o MVP. A `v0.2.0` aprimorou confiabilidade, configuração, lifecycle, testes e persistência. A **`v0.3.0` implementou o sistema funcional de ferramentas**, incluindo integração MCP, permissões, aprovações, auditoria, acesso controlado à web e leitura limitada de arquivos locais. O conjunto de funcionalidades foi encerrado e publicado na versão `v0.3.0`.

| Indicador | Estado verificado |
|:--|:--|
| Última versão publicada | **`v0.3.0`** |
| Próxima versão planejada | `v0.4.0` — memória inteligente |
| Branch de desenvolvimento | `develop` |
| Branch de release | `main` |
| Commit de release | `fd2f36f` — `chore(release): 0.3.0` |
| Tag Git | `v0.3.0` confirmada localmente e em `origin` |
| Pipeline de QA | 6 verificações aprovadas |
| Testes e cobertura | 417 aprovados, 1 ignorado; 89,48% |
| Build de release | `guillotine-0.3.0.tar.gz` e `guillotine-0.3.0-py3-none-any.whl` |
| Estado do release | **Concluído e publicado** |

## 2. Estado da implementação

### 2.1. Base estabelecida até a `v0.2.0`

- Agente assíncrono com PydanticAI e provedor compatível com OpenAI.
- Configuração de modelo, endpoint, credenciais e timeout por variáveis de ambiente.
- Integração com lifecycle do 9Router local, quando usado como endpoint.
- Conversas, histórico de mensagens e persistência em SQLite/aiosqlite.
- Grafo e checkpoints SQLite com LangGraph.
- CLI de conversação e gerenciamento de sessões.
- Tratamento de falhas conhecidas do provedor, testes automatizados e hooks de desenvolvimento.

### 2.2. Entregas concluídas para a `v0.3.0`

| Entrega | Estado | Observações |
|:--|:--|:--|
| Contratos, registry e executor de ferramentas | Implementado | Catálogo e invocação controlados por contratos |
| Bridge PydanticAI | Implementado | Exposição de ferramentas, schema e validação de argumentos JSON Schema |
| MCP client/manager | Implementado | Conexões stdio e Streamable HTTP; encerramento ordenado |
| Configuração MCP | Implementado | Seleção de ferramentas e recursos |
| Git MCP | Integrado e testado | Ferramentas selecionadas de **leitura**; escrita não suportada nesta versão |
| DuckDuckGo MCP | Integrado e testado | Busca e expansão de links |
| Permissões e aprovações | Implementado e testado | Controle por ferramenta/operação e escopos de recursos |
| Auditoria de ferramentas | Implementado e testado | Registro de execuções e recusas, com testes de integração |
| Safe Fetch | Implementado e testado | Validação de IPs/redirects, TLS e limites de resposta |
| Extração web estruturada | Implementado e testado | HTML/XHTML: título, descrição, conteúdo e links |
| Arquivos locais | Implementado e testado | Listar diretórios, ler arquivos UTF-8 e pesquisar arquivos sob raiz autorizada |
| Tratamento de falhas | Implementado e testado | Erros esperados de ferramentas retornam ao agente sem encerrar a sessão |

### 2.3. Arquitetura relevante

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
├── models/
├── services/
├── tools/
│   ├── bridges/pydantic_ai.py
│   ├── core/{contracts,registry,executor}.py
│   ├── local/
│   │   ├── safe_fetch.py
│   │   ├── web_fetch.py
│   │   ├── html_extract.py
│   │   ├── html_response.py
│   │   ├── file_reader.py
│   │   └── file_tools.py
│   └── mcp/{client,manager}.py
└── main.py
```

*Representação resumida dos componentes conhecidos, não um inventário integral do repositório.*

| Camada | Responsabilidade |
|:--|:--|
| `core/` | Agente, configuração, ciclo de vida, permissões, aprovações e auditoria |
| `interfaces/` | Interação humana, comandos e prompts de aprovação |
| `memory/` | Repositórios e persistência de conversas/mensagens |
| `models/` | Conexão com provedores e tratamento de erros |
| `services/` | Casos de uso e coordenação |
| `tools/core/` | Contratos, registro e executor |
| `tools/bridges/` | Integração entre ferramentas e agente |
| `tools/local/` | Fetch/extrator web e acesso restrito a arquivos |
| `tools/mcp/` | Conexões e gerenciamento MCP |

**Decisão de arquitetura:** preservar a separação por responsabilidade e só introduzir novas abstrações quando um caso de uso justificar.

## 3. Validação e qualidade

### 3.1. Resultado final da suíte

Último relatório compartilhado, executado em Windows com Python `3.12.16`:

| Verificação | Resultado |
|:--|:--|
| Ruff lint | Aprovado |
| Ruff format | 102 arquivos já formatados |
| Pyright strict | 0 erros, 0 avisos |
| Pytest | **417 passed, 1 skipped**, de 418 coletados |
| Cobertura | **89,48%**, acima do limite de 85% |
| Bandit | Sem achados médios/altos; 5 de baixa severidade |
| pip-audit | Sem vulnerabilidades conhecidas nas dependências auditáveis |
| `uv build` | Wheel + sdist gerados com sucesso |

O teste ignorado depende da criação de um symlink indisponível no ambiente Windows utilizado. Os testes específicos de *junctions* do Windows passaram. Na execução do QA anterior ao bump, o `pip-audit` não auditou o pacote local `guillotine (0.2.0)` no PyPI, pois não estava publicado ali. Isso não representa uma vulnerabilidade identificada.

O QA completo foi realizado antes do bump, com a versão `0.2.0` declarada. Durante o release, o Semantic Release executou `uv build` com sucesso e produziu **`guillotine-0.3.0.tar.gz`** e **`guillotine-0.3.0-py3-none-any.whl`**.

```powershell
uv run guillotine-dev qa
uv build
```

### 3.2. Abrangência dos testes

- **Unitários:** configuração, agente, CLI, permissões, execução de ferramentas, schemas, arquivos, extrator HTML e transporte Safe Fetch.
- **Integração:** persistência de permissões, fluxo de conversas, auditoria e lifecycle MCP, incluindo conexões stdio reais.
- **Propriedades:** configuração e condições de validação onde aplicável.
- **Testes reais de aceitação realizados no desenvolvimento:** Git MCP em modo leitura, buscas DuckDuckGo, Safe Fetch para sites públicos e operações locais de arquivos, inclusive rejeição de traversal.

**Critério adotado no fechamento:** somente problemas bloqueantes foram tratados durante o release; funcionalidades novas ficam para versões posteriores.

## 4. Release da `v0.3.0` — concluído

### 4.1. Versionamento, Git e publicação

- **Versão:** `0.3.0`, calculada e aplicada pelo Python Semantic Release `10.7.0` a partir dos commits convencionais.
- **Commit oficial:** `fd2f36f` — `chore(release): 0.3.0`, em `main` e `origin/main`.
- **Tag oficial:** `v0.3.0`, confirmada no repositório local e no remoto.
- **Changelog:** atualizado automaticamente no processo de release.
- **Build:** `uv build` concluiu a construção de `guillotine-0.3.0.tar.gz` e `guillotine-0.3.0-py3-none-any.whl`.
- **Publicação:** `semantic-release publish` foi executado com sucesso utilizando as variáveis de ambiente do `.env`; a publicação integral da versão foi confirmada no acompanhamento.
- **Histórico relevante:** implementação em `e87c396`, `5b3d315` e `f3e30d7`; configuração do Semantic Release em `30684fe`; merge `a083f64`; documentação em `c1a7aeb`.
- **Workflow:** `.github/workflows/qa.yml` é o workflow de QA identificado. O release `v0.3.0` foi realizado pelo fluxo local do Semantic Release; não se pressupõe a existência de um workflow `release.yml`.

[Release v0.3.0 no GitHub](https://github.com/guilherme-o-lindo/guillotine-ai/releases/tag/v0.3.0)

### 4.2. Checklist final

- [x] Implementar ferramentas MCP e ferramentas locais de web e arquivos.
- [x] Validar escopos, permissões, aprovações, auditoria e tratamento de erros.
- [x] Executar QA: **417 testes aprovados, 1 ignorado, 89,48% de cobertura**.
- [x] Integrar `develop` em `main`.
- [x] Atualizar README e documento de acompanhamento.
- [x] Atualizar versão para `0.3.0` e gerar o changelog com Semantic Release.
- [x] Construir wheel e sdist versionados como `0.3.0`.
- [x] Criar e enviar o commit `fd2f36f` e a tag `v0.3.0`.
- [x] Executar a publicação final da versão.

### 4.3. Fluxo de release adotado

| Papel | Ferramenta |
|:--|:--|
| Padronização e validação de commits | Commitizen + Conventional Commits |
| Cálculo de versão, changelog, commit e tag | Python Semantic Release |
| Ambiente, lockfile e build | uv |
| Desenvolvimento e integração | `develop` |
| Branch estável/publicação | `main` |
| QA remoto | GitHub Actions `qa.yml` |

O release foi executado com as variáveis locais do `.env` e sem sincronização automática do ambiente durante o comando:

```powershell
uv run --env-file .env --no-sync semantic-release version
uv run --env-file .env --no-sync semantic-release publish
```

O hook de Pyright do Pre-commit foi ajustado para `uv run --no-sync pyright`, impedindo que uma sincronização do `uv.lock` interrompa os commits de versão. **Não executar `cz bump` em paralelo ao Semantic Release.** Para consultar uma versão futura sem aplicar mudanças, utilizar `uv run --env-file .env --no-sync semantic-release version --print`.

## 5. Limitações e pontos de atenção

| Área | Estado e decisão |
|:--|:--|
| **Git MCP** | Suporte de escrita fora do escopo da `v0.3.0`; somente ações READ selecionadas |
| **Arquivos locais** | Exigem `GUILLOTINE_FILE_ROOT`, raiz confiável e caminhos relativos; limites de tamanho/quantidade; verificações contra traversal, symlinks e junctions |
| **TOCTOU** | Verificação de caminho e abertura de arquivo não constituem isolamento robusto contra trocas concorrentes maliciosas; documentar, não prometer sandbox completo |
| **Safe Fetch** | Proteções contra SSRF e validação de redirecionamento/TLS; manter limites e avaliações de segurança ao ampliar o recurso |
| **MCP externo** | Ferramentas/servidores externos devem ser tratados como fontes não confiáveis; respeitar aprovações e escopos |
| **Lifecycle Windows** | `WinError 10054` intermitente de transporte Proactor foi observado em alguns encerramentos excepcionais; sem causa definitiva identificada |
| **Configuração** | Conferir `.env.example` contra variáveis usadas; o token GitHub é necessário para a publicação autenticada, não para o uso básico do agente; não expor segredos em logs |
| **Memória** | Conhecimento/preferências e recuperação contextual ainda não integram uma memória inteligente completa |
| **LangGraph** | Concorrência simultânea na mesma conversa não possui serialização específica confirmada; evitar complexidade sem consumidor concreto |
| **Dependências** | Reavaliar caso a caso módulos não usados diretamente (ex.: observabilidade e infraestrutura adicional) |
| **CLI/API/voz** | Experiência avançada de terminal, API e voz ainda planejadas |

**Nota:** a segurança aplicada reduz riscos nas condições previstas, mas não implica resistência completa a processos locais maliciosos ou a servidores MCP não confiáveis.

## 6. Roadmap

| Versão | Entrega principal | Estado |
|:--|:--|:--|
| `v0.1.0` | MVP: agente, conversas, CLI e persistência | Concluída/publicada |
| `v0.2.0` | QA, configuração, lifecycle e confiabilidade | Concluída/publicada |
| `v0.3.0` | Ferramentas, MCP, web, arquivos, permissões e auditoria | **Concluída e publicada** |
| `v0.4.0` | Memória inteligente, preferências e recuperação contextual | Planejada |
| `v0.5.0` | Evolução da CLI e interfaces (API/voz conforme priorização) | Planejada |
| `v0.6.0` | Autonomia controlada, planos e execução em etapas | Planejada |
| `v0.7.0` | Endurecimento de segurança e observabilidade avançada | Planejada; controles básicos já implementados |
| `v1.0.0` | Estabilidade e consolidação | Planejada |

O roadmap não implica que um recurso existente deva ser reimplementado em outra versão. Exemplo: **permissões e auditoria já estão na `v0.3.0`**; uma fase futura de segurança trataria aprofundamento/observabilidade.

## 7. Registro histórico da `v0.2.0`

A `v0.2.0` consolidou a base do MVP antes da introdução das ferramentas:

- Testes automatizados com banco SQLite isolado, mocks de provedor, serviços, grafo, CLI e tratamento de erros.
- Revisão da configuração do modelo, timeout e lifecycle de clientes.
- Verificações de atomicidade das trocas de mensagens, exclusão associada a mensagens/checkpoints e tratamento de falhas na exclusão.
- Hooks Pre-commit, Ruff, Pyright, Conventional Commits e processo de build.
- **Marco histórico:** 86 testes aprovados em 10/11/2026; a suíte cresceu para 418 casos coletados no fechamento da `v0.3.0`.
- Tag Git `v0.2.0` registrada; confirmação da página formal de GitHub Release não consta dos registros disponíveis.

Esse resultado histórico não deve ser confundido com os indicadores atuais da suíte.

## 8. Processo e princípios de desenvolvimento

1. **Analisar** o código real e delimitar o problema.
2. **Projetar** responsabilidades sem abstrações preventivas.
3. **Implementar** a menor alteração coerente.
4. **Validar** com testes relevantes, Ruff, Pyright e verificações de segurança conforme o risco.
5. **Revisar** segurança, regressões e compatibilidade.
6. **Registrar** alterações por Conventional Commits.
7. **Publicar** versões após QA, documentação e validação de tag/artefatos.

| Princípio | Aplicação |
|:--|:--|
| Simplicidade | Preferir soluções explícitas à complexidade antecipada |
| Modularidade | Responsabilidades delimitadas entre camadas |
| Testabilidade | Testar sem exigir serviços externos em cada execução |
| Controle de recursos | Fechar clientes e conexões de forma ordenada |
| Permissões antes de ações | Validar escopo, efeitos e consentimento |
| Falhas previsíveis | Tornar erros conhecidos visíveis ao agente/usuário |
| Segurança por padrão | Reduzir superfície de acesso e proteger credenciais |
| Evolução incremental | Congelar funcionalidades ao preparar um release |

## 9. Registro de progresso

| Data | Marco |
|:--|:--|
| 10/11/2026 | `v0.2.0`: revisão de confiabilidade, 86 testes aprovados e release tag confirmado |
| 11–15/11/2026 | Integração MCP, Safe Fetch, extração HTML, permissões, auditoria e ferramentas locais de arquivos |
| 15/11/2026 | Commit `f3e30d7` consolida extração web e arquivos locais; configuração Semantic Release 10 em `30684fe` |
| 15/11/2026 | Merge local `a083f64` integra `develop` em `main`; cálculo de próxima versão retorna `0.3.0` |
| 15–16/11/2026 | QA final: **417 aprovados, 1 ignorado**, cobertura **89,48%** |
| 16/11/2026 | README e status alinhados à `v0.3.0`; commit de documentação `c1a7aeb` |
| 16/11/2026 | **Release `v0.3.0` concluído:** commit `fd2f36f`, tag remota confirmada, changelog atualizado, wheel/sdist `0.3.0` gerados e publicação executada |

---

<div align="center">

*Guillotine — desenvolvimento incremental, extensibilidade e controle sobre a execução.*

[Voltar ao README](README.md)

</div>
