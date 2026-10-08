#!/usr/bin/env python3
"""
04_limpar.py — Limpa os pontos da RMC, aplica as inclusões manuais e gera o CSV final.

Entradas: dados/intermediarios/rmc_pontos.csv
          dados/intermediarios/revisar_fora_do_brasil.csv
          dados/manual/inclusoes_rmc.csv            (decisões humanas; criado vazio na 1ª vez)
          dados/brutos/ibge/rmc_municipios.geojson
Saída   : dados/tratados/rmc_inventarios.csv
"""

import json
from pathlib import Path

import pandas as pd
from shapely.geometry import shape

RAIZ = Path(__file__).resolve().parent.parent
INTER = RAIZ / "dados" / "intermediarios"
MANUAL = RAIZ / "dados" / "manual" / "inclusoes_rmc.csv"
GEOJSON = RAIZ / "dados" / "brutos" / "ibge" / "rmc_municipios.geojson"
SAIDA = RAIZ / "dados" / "tratados" / "rmc_inventarios.csv"

COLUNAS = ["organizationName", "organizationTypeName", "anos", "latitude", "longitude",
           "municipio", "codigo_ibge", "observacao"]


def limpar_texto(s):
    """Remove espaços nas pontas e espaços duplos no meio."""
    return " ".join(str(s).split())


def carregar_municipios():
    colecao = json.loads(GEOJSON.read_text(encoding="utf-8"))
    return {f["properties"]["nome"]: (f["properties"]["codigo_ibge"], shape(f["geometry"]))
            for f in colecao["features"]}


def inclusoes_manuais(municipios):
    """Lê as decisões manuais e completa tipo/anos a partir da lista de revisão."""
    if not MANUAL.exists():
        MANUAL.parent.mkdir(parents=True, exist_ok=True)
        MANUAL.write_text("organizationName,municipio,justificativa\n", encoding="utf-8")
        print(f"Criado modelo vazio: {MANUAL.relative_to(RAIZ)}")
        return pd.DataFrame(columns=COLUNAS)

    manual = pd.read_csv(MANUAL)
    if manual.empty:
        return pd.DataFrame(columns=COLUNAS)

    invalidos = set(manual.municipio) - set(municipios)
    if invalidos:
        raise ValueError(f"Município fora da RMC ou com grafia errada no arquivo manual: {invalidos}")

    fora = pd.read_csv(INTER / "revisar_fora_do_brasil.csv", dtype={"anos": str})
    fora["chave"] = fora.organizationName.map(limpar_texto)
    manual["chave"] = manual.organizationName.map(limpar_texto)
    fora = fora.drop(columns=["organizationName", "latitude", "longitude"])  # coordenada errada sai
    junto = manual.merge(fora, on="chave", how="left")

    nao_achados = junto[junto.organizationTypeName.isna()]
    if not nao_achados.empty:
        raise ValueError(f"Nomes do arquivo manual que não estão na lista de revisão: "
                         f"{list(nao_achados.organizationName)}")

    # Coordenada substituta: um ponto garantidamente dentro do município
    interno = {n: c.representative_point() for n, (_, c) in municipios.items()}
    junto["latitude"] = junto.municipio.map(lambda m: interno[m].y)
    junto["longitude"] = junto.municipio.map(lambda m: interno[m].x)
    junto["codigo_ibge"] = junto.municipio.map(lambda m: municipios[m][0])
    junto["observacao"] = "inferido: " + junto.justificativa.fillna("coordenada original fora do Brasil")
    return junto[COLUNAS]


def main():
    municipios = carregar_municipios()

    rmc = pd.read_csv(INTER / "rmc_pontos.csv", dtype={"anos": str})
    rmc["observacao"] = ""
    manual = inclusoes_manuais(municipios)
    print(f"Pontos pelo filtro geográfico: {len(rmc)}")
    print(f"Inclusões manuais:            {len(manual)}")

    base = pd.concat([rmc[COLUNAS], manual], ignore_index=True)

    # Limpeza
    base["organizationName"] = base.organizationName.map(limpar_texto)
    antes = len(base)
    base = base.drop_duplicates(subset=["organizationName", "organizationTypeName",
                                        "latitude", "longitude"])
    print(f"Duplicatas removidas:         {antes - len(base)}")

    # Colunas derivadas dos anos
    anos = base.anos.str.split(";").apply(lambda l: [int(a) for a in l])
    base["qtd_anos"] = anos.str.len()
    base["primeiro_ano"] = anos.apply(min)
    base["ultimo_ano"] = anos.apply(max)
    base["codigo_ibge"] = base.codigo_ibge.astype("Int64")

    base = (base.rename(columns={"organizationName": "organizacao",
                                 "organizationTypeName": "tipo"})
                .sort_values(["municipio", "organizacao"]))
    ordem = ["organizacao", "tipo", "municipio", "codigo_ibge", "anos", "qtd_anos",
             "primeiro_ano", "ultimo_ano", "latitude", "longitude", "observacao"]

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    base[ordem].to_csv(SAIDA, index=False, encoding="utf-8-sig")
    print(f"\nTotal final: {len(base)}  →  {SAIDA.relative_to(RAIZ)}")
    print(base.groupby("tipo").size().to_string())


if __name__ == "__main__":
    main()
