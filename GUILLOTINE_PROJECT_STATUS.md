<div align="center">

<a href="https://github.com/guilherme-o-lindo/guillotine-ai">
  <img src="assets/banner.png" alt="Guillotine — assistente pessoal de IA" width="100%">
</a>

# Guillotine 🇫🇷

**Estado do Projeto e Plano de Evolução**

Documento de continuidade técnica: entregas, decisões arquiteturais, qualidade, riscos conhecidos e próximos passos.

<p>
  <a href="LICENSE"><img src="https://img.shields.io/static/v1?label=License&message=MIT&color=16A34A&style=flat-square" alt="Licença MIT"></a>
  <img src="https://img.shields.io/static/v1?label=Released&message=v0.2.0&color=7C3AED&style=flat-square" alt="Última versão publicada: v0.2.0">
  <img src="https://img.shields.io/static/v1?label=Next&message=v0.3.0%20ready&color=9333EA&style=flat-square" alt="Próxima versão: v0.3.0 pronta para release">
  <img src="https://img.shields.io/static/v1?label=Python&message=3.12%2B&color=3776AB&style=flat-square&logo=python&logoColor=white" alt="Python 3.12 ou superior">
  <img src="https://img.shields.io/static/v1?label=QA&message=417%20passed&color=16A34A&style=flat-square" alt="QA: 417 testes aprovados">
</p>

[README](README.md) · [Resumo](#1-resumo-executivo) · [Implementação](#2-estado-da-implementação) · [QA](#3-validação-e-qualidade) · [Release](#4-fechamento-da-v030) · [Riscos](#5-limitações-e-pontos-de-atenção) · [Roadmap](#6-roadmap) · [Histórico](#9-registro-de-progresso)

</div>

> **Snapshot — 15–16/11/2026:** `v0.2.0` é a última tag de release confirmada. O código da `v0.3.0` já está concluído e validado, e o semantic-release `10.7.0` calculou `0.3.0` na branch `main`. Ainda não há confirmação da tag `v0.3.0` nem do GitHub Release. **Não confundir versão pronta para release com versão publicada.**

## 1. Resumo executivo

O **Guillotine** é um agente pessoal de IA em Python com interface CLI, integração com APIs de modelos compatíveis com OpenAI, conversas persistidas em SQLite e fluxo de execução estruturado por LangGraph/PydanticAI. O projeto adota arquitetura modular e evolução incremental.

A `v0.1.0` entregou o MVP. A `v0.2.0` aprimorou confiabilidade, configuração, lifecycle, testes e persistência. A **`v0.3.0` implementou o sistema funcional de ferramentas**, incluindo integração MCP, permissões, aprovações, auditoria, acesso controlado à web e leitura limitada de arquivos locais. O escopo de funcionalidades entrou em *release freeze*.

| Indicador | Estado verificado |
|:--|:--|
| Última versão publicada/tag confirmada | `v0.2.0` |
| Versão em preparação | `v0.3.0` |
| Branch de desenvolvimento | `develop` |
| Branch de release | `main` |
| Último merge local informado | `a083f64` — `develop` → `main` |
| Próxima versão calculada | `0.3.0` (`semantic-release version --print`) |
| Pipeline de QA | 6 verificações aprovadas |
| Testes e cobertura | 417 aprovados, 1 ignorado; 89,48% |
| Build | Wheel e sdist construídos com a versão declarada `0.2.0` |
| Pendência principal | Publicar e confirmar a tag/release `v0.3.0` |

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

O teste ignorado depende da criação de um symlink indisponível no ambiente Windows utilizado. Os testes específicos de *junctions* do Windows passaram. O `pip-audit` não auditou o pacote local `guillotine (0.2.0)` no PyPI, pois ele não está publicado ali.

Artefatos produzidos **antes** do bump: `guillotine-0.2.0.tar.gz` e `guillotine-0.2.0-py3-none-any.whl`. Isso não demonstra um build de pacotes já versionados como `0.3.0`.

```powershell
uv run guillotine-dev qa
uv build
```

### 3.2. Abrangência dos testes

- **Unitários:** configuração, agente, CLI, permissões, execução de ferramentas, schemas, arquivos, extrator HTML e transporte Safe Fetch.
- **Integração:** persistência de permissões, fluxo de conversas, auditoria e lifecycle MCP, incluindo conexões stdio reais.
- **Propriedades:** configuração e condições de validação onde aplicável.
- **Testes reais de aceitação realizados no desenvolvimento:** Git MCP em modo leitura, buscas DuckDuckGo, Safe Fetch para sites públicos e operações locais de arquivos, inclusive rejeição de traversal.

**Critério para o release:** corrigir somente problemas realmente bloqueantes, sem iniciar uma nova rodada de implementação de funcionalidades.

## 4. Fechamento da `v0.3.0`

### 4.1. Situação do Git e do versionamento

- Última tag confirmada: `v0.2.0`; a tag `v0.3.0` ainda não foi confirmada.
- Commits da fase de ferramentas incluem `e87c396`, `5b3d315` e `f3e30d7`; configuração de release no commit `30684fe`.
- Merge local para `main`: `a083f64`.
- Semantic Release instalado: `10.7.0`.
- O comando somente de leitura `uv run semantic-release version --print` calculou `0.3.0` na `main`.
- A configuração de release foi ajustada para o formato de branches do Semantic Release 10; `main` é a branch de publicação.
- O Commitizen é destinado à validação de mensagens de commit; o Semantic Release controla o bump de versão e tags.
- O workflow confirmado é `.github/workflows/qa.yml`. **Não há workflow de publicação confirmado.**

### 4.2. Checklist restante

- [x] Concluir a implementação de ferramentas MCP e locais.
- [x] Testar escopos, permissões, aprovações, auditoria e tratamento de erros.
- [x] Executar QA completo: 417 aprovados, 1 ignorado; 89,48% de cobertura.
- [x] Construir wheel e sdist com a versão atualmente declarada (`0.2.0`).
- [x] Integrar `develop` em `main` localmente.
- [x] Confirmar que o Semantic Release calcula `0.3.0`.
- [x] Atualizar README e documento de status para o escopo implementado (estes arquivos).
- [ ] Confirmar push atualizado de `main` para `origin/main` e verificações CI no remoto.
- [ ] Revisar documentação final e config de changelog/credenciais de publicação.
- [ ] Executar bump de release pelo fluxo escolhido, com controle de commit/tag/push.
- [ ] Verificar versão declarada `0.3.0`, lockfile e artefatos reconstruídos após o bump.
- [ ] Confirmar tag remota `v0.3.0` e, se desejado, GitHub Release formal.

> O aviso **`Token value is missing!`** apareceu na consulta de versão. O cálculo local funcionou, mas a publicação automática em GitHub pode exigir autenticação. Não inferir que push/tag/release ocorreram sem confirmação.

### 4.3. Fluxo de publicação adotado

| Papel | Ferramenta |
|:--|:--|
| Padronização de commits | Commitizen + Conventional Commits |
| Cálculo e aplicação de versões | Python Semantic Release |
| Lockfile e build | uv |
| Desenvolvimento e integração | `develop` |
| Branch estável/publicação | `main` |
| QA remoto existente | GitHub Actions `qa.yml` |

Não executar `cz bump` em paralelo ao Semantic Release. Evitar comandos de versão com efeitos de escrita, push ou publicação antes de validar autenticação e o estado Git. Para consulta segura: `uv run semantic-release version --print`.

## 5. Limitações e pontos de atenção

| Área | Estado e decisão |
|:--|:--|
| **Git MCP** | Suporte de escrita fora do escopo da `v0.3.0`; somente ações READ selecionadas |
| **Arquivos locais** | Exigem `GUILLOTINE_FILE_ROOT`, raiz confiável e caminhos relativos; limites de tamanho/quantidade; verificações contra traversal, symlinks e junctions |
| **TOCTOU** | Verificação de caminho e abertura de arquivo não constituem isolamento robusto contra trocas concorrentes maliciosas; documentar, não prometer sandbox completo |
| **Safe Fetch** | Proteções contra SSRF e validação de redirecionamento/TLS; manter limites e avaliações de segurança ao ampliar o recurso |
| **MCP externo** | Ferramentas/servidores externos devem ser tratados como fontes não confiáveis; respeitar aprovações e escopos |
| **Lifecycle Windows** | `WinError 10054` intermitente de transporte Proactor foi observado em alguns encerramentos excepcionais; sem causa definitiva identificada |
| **Configuração** | Conferir `.env.example` contra variáveis usadas; revisar presença e necessidade de `GH_TOKEN`; não expor segredos em logs |
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
| `v0.3.0` | Ferramentas, MCP, web, arquivos, permissões e auditoria | **Implementada e validada; release pendente** |
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
| 15–16/11/2026 | QA final: **417 aprovados, 1 ignorado**, cobertura **89,48%**; `uv build` aprovado em `0.2.0` |
| 16/11/2026 | README e status alinhados para a preparação do release `v0.3.0` |

---

<div align="center">

*Guillotine — desenvolvimento incremental, extensibilidade e controle sobre a execução.*

[Voltar ao README](README.md)

</div>
