"""Testes de integridade dos dados versionados: regras que a base final sempre deve cumprir.

Rodam sobre dados/tratados/ e dados/manual/ — se uma coleta nova ou uma edição manual
quebrar alguma regra, o teste avisa antes de o relatório sair errado.
"""

import pandas as pd
import pytest

from conftest import RAIZ, carregar_script

TRATADOS = RAIZ / "dados" / "tratados" / "rmc_inventarios.csv"
SETORES = RAIZ / "dados" / "manual" / "setores.csv"
INCLUSOES = RAIZ / "dados" / "manual" / "inclusoes_rmc.csv"
RMC = set(carregar_script("02_baixar_municipios").RMC)


@pytest.fixture(scope="module")
def base():
    return pd.read_csv(TRATADOS, dtype={"anos": str}).fillna({"observacao": ""})


def test_municipios_sao_da_rmc(base):
    assert set(base.municipio) <= RMC


def test_sem_organizacao_repetida(base):
    repetidas = base[base.duplicated(["organizacao", "tipo", "municipio"], keep=False)]
    assert repetidas.empty, list(repetidas.organizacao)


def test_anos_validos_e_coerentes(base):
    for _, linha in base.iterrows():
        anos = [int(a) for a in linha.anos.split(";")]
        assert all(2000 <= a <= 2100 for a in anos), linha.organizacao
        assert (min(anos), max(anos), len(anos)) == (
            linha.primeiro_ano,
            linha.ultimo_ano,
            linha.qtd_anos,
        )


def test_toda_organizacao_tem_setor(base):
    setores = pd.read_csv(SETORES, dtype=str).fillna("")
    com_setor = set(setores[setores.setor.str.strip() != ""].organizacao)
    assert set(base.organizacao) <= com_setor, set(base.organizacao) - com_setor


def test_industrial_so_aceita_valores_conhecidos():
    setores = pd.read_csv(SETORES, dtype=str)
    assert set(setores.industrial) <= {"True", "False"}


def test_cada_inclusao_manual_aparece_como_inferida(base):
    inclusoes = pd.read_csv(INCLUSOES)
    inferidas = base[base.observacao.str.startswith("inferido")]
    assert len(inferidas) == len(inclusoes)
    assert set(inferidas.organizacao) == set(inclusoes.organizationName)
