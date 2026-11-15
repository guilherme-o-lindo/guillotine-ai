"""Registra entrypoint dev, preservando o pyproject existente."""

import re
import tomllib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "pyproject.toml"
original = path.read_text(encoding="utf-8")
config = tomllib.loads(original)
entrypoints = config.get("project", {}).get("scripts", {})
expected = "guillotine.dev_cli:app"

if "guillotine-dev" in entrypoints:
    if entrypoints["guillotine-dev"] != expected:
        raise SystemExit(
            "'guillotine-dev' já existe com outro destino; ajuste manualmente."
        )
    print("Entry point já configurado; nenhuma alteração necessária.")
else:
    match = re.search(r"(?m)^\[project\.scripts\]\s*$", original)
    if not match:
        raise SystemExit("Seção [project.scripts] não encontrada; ajuste manualmente.")
    position = match.end()
    updated = (
        original[:position] + f'\nguillotine-dev = "{expected}"' + original[position:]
    )
    tomllib.loads(updated)
    path.write_text(updated, encoding="utf-8")
    print("Registrado: guillotine-dev = 'guillotine.dev_cli:app'")
