"""
conftest.py — Arquivo lido automaticamente pelo pytest antes dos testes.

Os scripts começam com número (03_filtrar_rmc.py), e "import 03_filtrar_rmc" é sintaxe
inválida em Python. Por isso a fixture `script` carrega o módulo pelo caminho do arquivo.
Carregar não executa o pipeline: o main() só roda sob `if __name__ == "__main__"`.
"""

import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def carregar_script(nome):
    caminho = RAIZ / "scripts" / f"{nome}.py"
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def script():
    """Uso: def test_x(script): m = script("03_filtrar_rmc")"""
    return carregar_script
