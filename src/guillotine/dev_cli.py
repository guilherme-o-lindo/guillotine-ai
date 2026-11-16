"""Comandos de desenvolvimento do Guillotine (não usados pela CLI do agente)."""

import shutil
import subprocess
import time
from pathlib import Path

import typer

app = typer.Typer(
    help="Ferramentas de desenvolvimento do Guillotine.", no_args_is_help=True
)
qa_app = typer.Typer(help="Verificações de qualidade.", invoke_without_command=True)
app.add_typer(qa_app, name="qa")


def project_root() -> Path:
    """Encontra a raiz do checkout atual, independentemente do cwd."""
    candidates = (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents)
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "guillotine"
        ).is_dir():
            return candidate
    raise RuntimeError("Não foi possível localizar a raiz do Guillotine.")


def run_check(label: str, command: list[str]) -> bool:
    """Executa um verificador sem shell; não interrompe a sequência por falha."""
    typer.echo(f"\n=== {label} ===")
    executable = shutil.which(command[0])
    if executable is None:
        typer.secho(
            f"[FAIL] {label}: comando '{command[0]}' não encontrado",
            fg=typer.colors.RED,
        )
        return False
    try:
        result = subprocess.run(
            [executable, *command[1:]], cwd=project_root(), check=False
        )
    except OSError as exc:
        typer.secho(f"[FAIL] {label}: {exc}", fg=typer.colors.RED)
        return False
    passed = result.returncode == 0
    typer.secho(
        f"[{'PASS' if passed else 'FAIL'}] {label}",
        fg=typer.colors.GREEN if passed else typer.colors.RED,
    )
    return passed


def lint_checks() -> list[tuple[str, list[str]]]:
    return [("Ruff lint", ["ruff", "check", "."])]


def format_checks() -> list[tuple[str, list[str]]]:
    return [("Ruff format", ["ruff", "format", "--check", "."])]


def type_checks() -> list[tuple[str, list[str]]]:
    return [("Pyright", ["pyright"])]


def test_checks(
    allure: bool = False, *, coverage: bool = True
) -> list[tuple[str, list[str]]]:
    """Monta a execução de testes com cobertura opcional e relatório Allure."""
    cmd = ["pytest"]
    if coverage:
        cmd.extend(["--cov", "--cov-report=term-missing"])
    if allure:
        cmd.extend(["--alluredir=allure-results", "--clean-alluredir"])
    return [("Pytest + Coverage" if coverage else "Pytest", cmd)]


def security_checks() -> list[tuple[str, list[str]]]:
    # -ll evita falhar no aviso B404 de severidade baixa, sem suprimir seu diagnóstico.
    return [
        ("Bandit", ["bandit", "-r", "src/guillotine", "-ll"]),
        ("pip-audit", ["pip-audit"]),
    ]


def execute_checks(checks: list[tuple[str, list[str]]]) -> None:
    start = time.perf_counter()
    results = [(name, run_check(name, cmd)) for name, cmd in checks]
    typer.echo("\n=== QA SUMMARY ===")
    for name, passed in results:
        typer.echo(f"[{'PASS' if passed else 'FAIL'}] {name}")
    typer.echo(f"Duration: {time.perf_counter() - start:.2f}s")
    if not all(passed for _, passed in results):
        raise typer.Exit(code=1)


@qa_app.callback(invoke_without_command=True)
def qa(
    ctx: typer.Context,
    allure: bool = typer.Option(
        False, "--allure", help="Gera resultados Allure na execução completa."
    ),
) -> None:
    """Roda lint, formatação, tipos, testes, segurança e auditoria."""
    if ctx.invoked_subcommand is None:
        execute_checks(
            lint_checks()
            + format_checks()
            + type_checks()
            + test_checks(allure=allure)
            + security_checks()
        )


@qa_app.command("quick")
def quick(
    allure: bool = typer.Option(
        False, "--allure", help="Gera resultados Allure nos testes rápidos."
    ),
) -> None:
    """Roda Ruff, Pyright e Pytest, sem cobertura ou auditoria de segurança."""
    execute_checks(
        lint_checks()
        + format_checks()
        + type_checks()
        + test_checks(allure=allure, coverage=False)
    )


@qa_app.command("lint")
def lint() -> None:
    """Verifica o lint com Ruff."""
    execute_checks(lint_checks())


@qa_app.command("format")
def format_check() -> None:
    """Confere a formatação sem modificar arquivos."""
    execute_checks(format_checks())


@qa_app.command("types")
def types() -> None:
    """Executa Pyright."""
    execute_checks(type_checks())


@qa_app.command("test")
def test(
    allure: bool = typer.Option(
        False, "--allure", help="Gera arquivos allure-results/."
    ),
) -> None:
    """Executa Pytest com cobertura de código."""
    execute_checks(test_checks(allure=allure))


@qa_app.command("security")
def security() -> None:
    """Executa Bandit e pip-audit."""
    execute_checks(security_checks())


if __name__ == "__main__":
    app()
