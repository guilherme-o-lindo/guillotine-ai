# Guillotine

Assistente de inteligência artificial modular desenvolvido em Python, projetado para centralizar e simplificar o uso de modelos de IA, ferramentas e diferentes interfaces de interação.

## Arquitetura

O projeto utiliza uma arquitetura modular, separando as responsabilidades em componentes independentes. Essa organização facilita a manutenção, a evolução e a adição de novas funcionalidades sem acoplar todo o sistema.

```text
guillotine/
├── src/
│   └── guillotine/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       │
│       ├── core/
│       │   ├── agent.py
│       │   ├── context.py
│       │   ├── prompts.py
│       │   └── permissions.py
│       │
│       ├── models/
│       │   ├── router.py
│       │   └── providers.py
│       │
│       ├── tools/
│       │   ├── registry.py
│       │   ├── executor.py
│       │   ├── internal/
│       │   └── mcp/
│       │
│       ├── memory/
│       │   ├── manager.py
│       │   ├── types.py
│       │   ├── repositories/
│       │   └── storage/
│       │
│       └── interfaces/
│           ├── cli/
│           ├── voice/
│           └── api/
│
├── data/
│   └── guillotine.db
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── CHANGELOG.md
├── pyproject.toml
├── uv.lock
└── README.md
```

## Componentes

### Core

Contém a lógica central do agente e coordena seu funcionamento.

- **agent.py:** responsável pelo ciclo de execução do agente e pela coordenação das interações.
- **context.py:** gerencia o contexto utilizado durante as conversas.
- **prompts.py:** centraliza os prompts e as instruções do agente.
- **permissions.py:** controla as permissões de acesso e execução de ferramentas.

### Models

Gerencia a comunicação com os modelos de inteligência artificial.

- **router.py:** seleciona e encaminha as requisições para os modelos disponíveis.
- **providers.py:** concentra as integrações com os diferentes provedores de IA.

Essa separação permite utilizar diferentes modelos e provedores sem depender de uma implementação específica.

### Tools

Gerencia as ferramentas que o agente pode utilizar.

- **registry.py:** registra e disponibiliza as ferramentas existentes.
- **executor.py:** controla a execução das ferramentas.

As ferramentas são divididas em duas categorias:

**Internal:** ferramentas nativas do Guillotine, como operações com arquivos, pesquisas, gerenciamento de sessões e informações do sistema.

**MCP:** integrações com servidores externos através do Model Context Protocol, permitindo ampliar as capacidades do agente sem implementar cada integração diretamente.

### Memory

Responsável pelo armazenamento e gerenciamento de informações persistentes.

- **manager.py:** coordena as operações de memória.
- **types.py:** define estruturas e tipos utilizados pelo sistema.
- **repositories/:** concentra as operações de consulta e persistência de cada conjunto de informações.
- **storage/:** gerencia a conexão com o banco de dados, os modelos e as migrações.

Inicialmente, o projeto utiliza SQLite, com possibilidade de utilizar outros bancos de dados futuramente.

### Interfaces

Contém as diferentes formas de interação com o agente.

- **cli/:** interface de linha de comando.
- **voice/:** recursos de interação por voz.
- **api/:** disponibiliza o agente através de uma API.

As interfaces utilizam a mesma lógica central, evitando duplicação de funcionalidades.

### Configuração e inicialização

- **main.py:** ponto de entrada principal da aplicação.
- **config.py:** centraliza as configurações utilizadas pelo sistema.
- **__init__.py:** identifica o pacote Python e pode disponibilizar funcionalidades de inicialização.

## Dados e configurações

### data/

Armazena os dados persistentes gerados durante a execução do sistema.

Inicialmente, contém o banco de dados SQLite:

```text
data/
└── guillotine.db
```

Essa pasta fica fora de `src/` porque os dados de execução não fazem parte do código-fonte da aplicação.

### .env

Armazena configurações locais e informações sensíveis, como chaves de API e endereços de serviços.

### .env.example

Disponibiliza um modelo das variáveis de ambiente necessárias para executar o projeto, sem expor informações sensíveis.

### pyproject.toml

Centraliza os metadados do projeto, dependências, configurações de ferramentas e informações de empacotamento.

### uv.lock

Registra as versões exatas das dependências resolvidas pelo `uv`, contribuindo para a reprodução do ambiente de desenvolvimento.

## Desenvolvimento e qualidade

- **test/:** reúne os testes automatizados do projeto.
- **.gitignore:** define arquivos e diretórios que não devem ser versionados.
- **.pre-commit-config.yaml:** configura verificações automáticas antes dos commits.
- **CHANGELOG.md:** registra as alterações relevantes entre versões.
- **.python-version:** define a versão do Python utilizada no projeto.

## Tecnologias

| Categoria | Tecnologia |
|---|---|
| Linguagem | Python |
| Gerenciamento de projeto | uv |
| Banco de dados inicial | SQLite |
| Configuração e validação | Pydantic |
| Testes | Pytest |
| Qualidade de código | Ruff |
| Versionamento | Git e GitHub |
| Commits | Commitizen |
| Versionamento de releases | Python Semantic Release |

---

**Guillotine** — uma arquitetura modular para um assistente de IA extensível, independente de provedores e interfaces.