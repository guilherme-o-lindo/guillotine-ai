"""Testes rápidos da interface de desenvolvimento (sem executar ferramentas reais)."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from guillotine import dev_cli

runner = CliRunner()


def test_qa_runs_all_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []

    def fake_run(label: str, command: list[str]) -> bool:
        called.append(label)
        return True

    monkeypatch.setattr(dev_cli, "run_check", fake_run)
    result = runner.invoke(dev_cli.app, ["qa"])
    assert result.exit_code == 0, result.output
    assert called == [
        "Ruff lint",
        "Ruff format",
        "Pyright",
        "Pytest + Coverage",
        "Bandit",
        "pip-audit",
    ]


def test_qa_reports_failure_without_skipping_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def fake_run(label: str, command: list[str]) -> bool:
        called.append(label)
        return label != "Pyright"

    monkeypatch.setattr(dev_cli, "run_check", fake_run)
    result = runner.invoke(dev_cli.app, ["qa"])
    assert result.exit_code == 1
    assert len(called) == 6
    assert "[FAIL] Pyright" in result.output


def test_test_allure_passes_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[list[str]] = []

    def fake_run(label: str, command: list[str]) -> bool:
        commands.append(command)
        return True

    monkeypatch.setattr(dev_cli, "run_check", fake_run)
    result = runner.invoke(dev_cli.app, ["qa", "test", "--allure"])
    assert result.exit_code == 0, result.output
    assert "--alluredir=allure-results" in commands[0]
    assert "--clean-alluredir" in commands[0]


def test_quick_runs_four_checks_without_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[tuple[str, list[str]]] = []

    def fake_run(label: str, command: list[str]) -> bool:
        commands.append((label, command))
        return True

    monkeypatch.setattr(dev_cli, "run_check", fake_run)
    result = runner.invoke(dev_cli.app, ["qa", "quick"])
    assert result.exit_code == 0, result.output
    assert [label for label, _ in commands] == [
        "Ruff lint",
        "Ruff format",
        "Pyright",
        "Pytest",
    ]
    assert commands[-1][1] == ["pytest"]


def test_quick_allure_generates_results_without_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []

    def fake_run(label: str, command: list[str]) -> bool:
        commands.append(command)
        return True

    monkeypatch.setattr(dev_cli, "run_check", fake_run)
    result = runner.invoke(dev_cli.app, ["qa", "quick", "--allure"])
    assert result.exit_code == 0, result.output
    assert commands[-1] == ["pytest", "--alluredir=allure-results", "--clean-alluredir"]


def test_full_allure_keeps_coverage_and_security(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[tuple[str, list[str]]] = []

    def fake_run(label: str, command: list[str]) -> bool:
        commands.append((label, command))
        return True

    monkeypatch.setattr(dev_cli, "run_check", fake_run)
    result = runner.invoke(dev_cli.app, ["qa", "--allure"])
    assert result.exit_code == 0, result.output
    assert len(commands) == 6
    assert commands[3] == (
        "Pytest + Coverage",
        [
            "pytest",
            "--cov",
            "--cov-report=term-missing",
            "--alluredir=allure-results",
            "--clean-alluredir",
        ],
    )
    assert commands[-1][0] == "pip-audit"


def test_quick_failure_continues_and_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def fake_run(label: str, command: list[str]) -> bool:
        called.append(label)
        return label != "Ruff lint"

    monkeypatch.setattr(dev_cli, "run_check", fake_run)
    result = runner.invoke(dev_cli.app, ["qa", "quick"])
    assert result.exit_code == 1
    assert len(called) == 4
    assert "[FAIL] Ruff lint" in result.output
    assert "[PASS] Pytest" in result.output


def test_run_check_pass_and_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from subprocess import CompletedProcess

    monkeypatch.setattr(dev_cli, "project_root", lambda: tmp_path)

    def executable_found(executable: str) -> str:
        return "/usr/bin/tool"

    monkeypatch.setattr(dev_cli.shutil, "which", executable_found)
    codes = iter((0, 3))

    def fake_run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
        assert args == ["/usr/bin/tool", "--version"]
        assert kwargs["cwd"] == tmp_path
        assert kwargs["check"] is False
        return CompletedProcess(args, next(codes))

    monkeypatch.setattr(dev_cli.subprocess, "run", fake_run)
    assert dev_cli.run_check("Tool", ["tool", "--version"]) is True
    assert dev_cli.run_check("Tool", ["tool", "--version"]) is False


def test_run_check_missing_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    def executable_missing(executable: str) -> None:
        return None

    monkeypatch.setattr(dev_cli.shutil, "which", executable_missing)

    assert dev_cli.run_check("Missing tool", ["not-a-tool"]) is False


def test_run_check_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def executable_available(executable: str) -> str:
        return "tool"

    monkeypatch.setattr(dev_cli.shutil, "which", executable_available)
    monkeypatch.setattr(dev_cli, "project_root", lambda: Path.cwd())

    def raise_os_error(*args: object, **kwargs: object) -> None:
        raise OSError("execution refused")

    monkeypatch.setattr(dev_cli.subprocess, "run", raise_os_error)
    assert dev_cli.run_check("Tool", ["tool"]) is False
