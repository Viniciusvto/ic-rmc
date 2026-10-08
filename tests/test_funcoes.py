"""Testes das funções puras dos scripts: entrada conhecida → saída esperada."""

import pandas as pd
import pytest
from shapely.geometry import box


# ---------------------------------------------------------------------------
# util_setores_antigos.chave — normalização de nomes para casar bases
# ---------------------------------------------------------------------------
def test_chave_ignora_acento_caixa_e_pontuacao(script):
    chave = script("util_setores_antigos").chave
    assert chave("LSL Transportes - Paulínia") == chave("LSL Transportes Paulínia")
    assert chave("Ação & Cia. Ltda") == "acaocialtda"


# ---------------------------------------------------------------------------
# 03_filtrar_rmc.localizar — point-in-polygon
# ---------------------------------------------------------------------------
@pytest.fixture
def quadrado():
    # "município" de mentira: longitude -47 a -46, latitude -23 a -22
    return [("Teste", 123, box(-47, -23, -46, -22))]


def test_localizar_ponto_dentro(script, quadrado):
    localizar = script("03_filtrar_rmc").localizar
    assert localizar(-22.5, -46.5, quadrado) == ("Teste", 123)


def test_localizar_ponto_na_borda_conta_como_dentro(script, quadrado):
    localizar = script("03_filtrar_rmc").localizar
    assert localizar(-22.0, -46.5, quadrado) == ("Teste", 123)  # covers, não contains


def test_localizar_ponto_fora(script, quadrado):
    localizar = script("03_filtrar_rmc").localizar
    assert localizar(-21.5, -46.5, quadrado) == (None, None)


def test_localizar_nao_inverte_latitude_e_longitude(script):
    # Retângulo não quadrado: se lat/lon fossem trocadas, o ponto cairia fora
    localizar = script("03_filtrar_rmc").localizar
    retangulo = [("Teste", 1, box(-47, -10, -46, -9))]  # lon -47..-46, lat -10..-9
    assert localizar(-9.5, -46.5, retangulo) == ("Teste", 1)


# ---------------------------------------------------------------------------
# 04_limpar.limpar_texto
# ---------------------------------------------------------------------------
def test_limpar_texto_remove_espacos_extras(script):
    limpar = script("04_limpar").limpar_texto
    assert limpar("  BDO   RCS\tAuditores ") == "BDO RCS Auditores"


# ---------------------------------------------------------------------------
# 06_gerar_relatorio — registro, marcadores, preencher, carregar
# ---------------------------------------------------------------------------
def linha(**campos):
    padrao = dict(
        organizacao="Org",
        municipio="Campinas",
        tipo="Matriz",
        setor="Energia",
        anos="2023;2021;2022",
        industrial="False",
    )
    padrao.update(campos)
    return pd.Series(padrao)


def test_registro_ordena_anos_e_calcula_serie(script):
    r = script("06_gerar_relatorio").registro(linha())
    assert r["anos"] == [2021, 2022, 2023]
    assert (r["ini"], r["fim"], r["n"]) == (2021, 2023, 3)


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("True", True),
        ("true", True),
        ("sim", True),
        ("1", True),
        ("False", False),
        ("não", False),
        ("0", False),
        ("", False),
    ],
)
def test_registro_industrial(script, valor, esperado):
    r = script("06_gerar_relatorio").registro(linha(industrial=valor))
    assert r["industrial"] is esperado


def test_registro_ativo_na_fronteira_do_ano(script):
    m = script("06_gerar_relatorio")
    assert m.registro(linha(anos=f"{m.ANO_ATIVO}"))["ativo"] is True
    assert m.registro(linha(anos=f"{m.ANO_ATIVO - 1}"))["ativo"] is False


def test_marcadores_contam_e_escapam_fechamento_de_tag(script):
    m = script("06_gerar_relatorio")
    dados = [
        {"org": "A </script>", "industrial": True, "ativo": True},
        {"org": "B", "industrial": True, "ativo": False},
        {"org": "C", "industrial": False, "ativo": True},
    ]
    v = m.marcadores(dados, n_inferidos=1)
    assert (v["__N_TOTAL__"], v["__N_IND__"], v["__N_IND_ATIVAS__"]) == ("3", "2", "1")
    assert "</script>" not in v["__DADOS__"]
    assert "(1 inferido pelo nome)" in v["__META__"]
    assert "(2 inferidos pelo nome)" in m.marcadores(dados, n_inferidos=2)["__META__"]


def test_preencher_falha_se_marcador_nao_existe(script):
    preencher = script("06_gerar_relatorio").preencher
    assert preencher("<p>__A__</p>", {"__A__": "1"}) == "<p>1</p>"
    with pytest.raises(ValueError, match="__B__"):
        preencher("<p>__A__</p>", {"__A__": "1", "__B__": "2"})


def test_carregar_falha_se_organizacao_sem_setor(script, tmp_path, monkeypatch):
    m = script("06_gerar_relatorio")
    base = tmp_path / "base.csv"
    setores = tmp_path / "setores.csv"
    base.write_text("organizacao,anos,observacao\nA,2024,\nB,2024,\n", encoding="utf-8")
    setores.write_text("organizacao,setor,industrial\nA,Energia,False\n", encoding="utf-8")
    monkeypatch.setattr(m, "CSV", base)  # aponta o script para os arquivos de teste
    monkeypatch.setattr(m, "SETORES", setores)
    monkeypatch.setattr(m, "RAIZ", tmp_path)
    with pytest.raises(ValueError, match="B"):
        m.carregar()
