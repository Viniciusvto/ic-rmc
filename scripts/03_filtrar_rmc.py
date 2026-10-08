#!/usr/bin/env python3
"""
03_filtrar_rmc.py — Separa, dos pontos do Brasil inteiro, os que caem dentro da RMC.

Entradas: dados/brutos/fgv/organizacoes_*.json      (a coleta mais recente)
          dados/brutos/ibge/rmc_municipios.geojson
Saídas  : dados/intermediarios/revisar_fora_do_brasil.csv  (sem coordenada ou fora do Brasil;
                                                             coluna "motivo"; revisar à mão)
          dados/intermediarios/candidatos_caixa.csv        (recorte grosseiro)
          dados/intermediarios/rmc_pontos.csv              (recorte fino: só RMC)

Uso:
    python scripts/03_filtrar_rmc.py
"""

import json
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, shape
from shapely.ops import unary_union

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
SAIDA = RAIZ / "dados" / "intermediarios"

MARGEM_GRAUS = 0.05  # folga da caixa (~5 km)
BRASIL_LAT = (-34.0, 5.5)  # retângulo aproximado do território brasileiro
BRASIL_LON = (-74.0, -34.5)


# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------
def coleta_mais_recente():
    """Devolve o arquivo de coleta da FGV mais recente."""
    arquivos = sorted((BRUTOS / "fgv").glob("organizacoes_*.json"))
    if not arquivos:
        raise FileNotFoundError("Nenhuma coleta em dados/brutos/fgv. Rode o 01 antes.")
    return arquivos[-1]  # nome tem a data AAAA-MM-DD → ordem alfabética = cronológica


def carregar_pontos(arquivo):
    """Lê o JSON bruto da FGV e devolve uma tabela (DataFrame)."""
    corpo = json.loads(arquivo.read_text(encoding="utf-8"))
    df = pd.DataFrame(corpo["result"]["organizations"])
    # CSV não guarda lista: [2025, 2022] vira o texto "2022;2025"
    df["anos"] = df["invetoriedYears"].apply(
        lambda a: ";".join(str(x) for x in sorted(a))
    )
    return df.drop(columns="invetoriedYears")


def carregar_municipios():
    """Lê o GeoJSON do IBGE e devolve [(nome, código, contorno shapely), ...]."""
    caminho = BRUTOS / "ibge" / "rmc_municipios.geojson"
    colecao = json.loads(caminho.read_text(encoding="utf-8"))
    return [
        (f["properties"]["nome"], f["properties"]["codigo_ibge"], shape(f["geometry"]))
        for f in colecao["features"]
    ]


def localizar(lat, lon, municipios):
    """Point-in-polygon: devolve (nome, código) do município que contém o ponto."""
    ponto = Point(lon, lat)  # ATENÇÃO: shapely usa (x, y) = (longitude, latitude)
    for nome, codigo, contorno in municipios:
        if contorno.covers(ponto):  # covers = dentro OU exatamente na borda
            return nome, codigo
    return None, None


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    arquivo = coleta_mais_recente()
    df = carregar_pontos(arquivo)
    municipios = carregar_municipios()
    print(f"Coleta usada: {arquivo.name}  ({len(df)} pontos)")

    # A) Pontos sem localização utilizável → revisão humana
    #    NaN (coordenada vazia) dá False em qualquer comparação, então cai aqui também;
    #    a coluna "motivo" separa os dois casos.
    no_brasil = df.latitude.between(*BRASIL_LAT) & df.longitude.between(*BRASIL_LON)
    revisar = df[~no_brasil].copy()
    revisar["motivo"] = revisar.latitude.isna().map(
        {True: "sem coordenada", False: "coordenada fora do Brasil"}
    )
    revisar.to_csv(
        SAIDA / "revisar_fora_do_brasil.csv", index=False, encoding="utf-8-sig"
    )
    print(f"A) Para revisar à mão: {len(revisar)}")
    print(revisar.motivo.value_counts().to_string())

    # B) Recorte grosseiro: retângulo que envolve os 20 municípios + margem
    oeste, sul, leste, norte = unary_union([c for _, _, c in municipios]).bounds
    na_caixa = df.longitude.between(
        oeste - MARGEM_GRAUS, leste + MARGEM_GRAUS
    ) & df.latitude.between(sul - MARGEM_GRAUS, norte + MARGEM_GRAUS)
    caixa = df[na_caixa].copy()

    # C) Recorte fino: point-in-polygon só nos candidatos da caixa
    achados = [
        localizar(la, lo, municipios) for la, lo in zip(caixa.latitude, caixa.longitude)
    ]
    caixa[["municipio", "codigo_ibge"]] = pd.DataFrame(achados, index=caixa.index)
    caixa.to_csv(SAIDA / "candidatos_caixa.csv", index=False, encoding="utf-8-sig")

    rmc = caixa[caixa.municipio.notna()]
    rmc.to_csv(SAIDA / "rmc_pontos.csv", index=False, encoding="utf-8-sig")
    print(f"\nB) Candidatos na caixa: {len(caixa)}")
    print(f"C) Dentro da RMC: {len(rmc)}   (descartados: {len(caixa) - len(rmc)})")
    print("\nPor município:")
    print(rmc.municipio.value_counts().to_string())


if __name__ == "__main__":
    main()
