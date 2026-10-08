#!/usr/bin/env python3
"""
02_baixar_municipios.py — Baixa do IBGE os contornos dos 20 municípios da RMC.

Fonte   : API de Localidades e API de Malhas do IBGE
Saída   : dados/brutos/ibge/municipios_sp.json      (lista oficial de municípios de SP)
          dados/brutos/ibge/rmc_municipios.geojson  (contornos dos 20 municípios da RMC)

Uso:
    python scripts/02_baixar_municipios.py
"""

import json
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
PASTA_SAIDA = RAIZ / "dados" / "brutos" / "ibge"

IBGE = "https://servicodados.ibge.gov.br/api"
UF_SP = 35  # código IBGE do estado de São Paulo

# Região Metropolitana de Campinas — LC Estadual 870/2000 (+ Morungaba, 2014)
RMC = [
    "Americana",
    "Artur Nogueira",
    "Campinas",
    "Cosmópolis",
    "Engenheiro Coelho",
    "Holambra",
    "Hortolândia",
    "Indaiatuba",
    "Itatiba",
    "Jaguariúna",
    "Monte Mor",
    "Morungaba",
    "Nova Odessa",
    "Paulínia",
    "Pedreira",
    "Santa Bárbara d'Oeste",
    "Santo Antônio de Posse",
    "Sumaré",
    "Valinhos",
    "Vinhedo",
]


# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------
def listar_municipios_sp():
    """Devolve a lista oficial de municípios de SP (id + nome + regiões)."""
    r = requests.get(f"{IBGE}/v1/localidades/estados/{UF_SP}/municipios", timeout=60)
    r.raise_for_status()
    return r.json()


def codigos_da_rmc(municipios_sp):
    """Cruza os nomes da RMC com a lista do IBGE e devolve {nome: código}."""
    codigos = {m["nome"]: m["id"] for m in municipios_sp if m["nome"] in RMC}
    faltando = set(RMC) - set(codigos)
    if faltando:
        raise RuntimeError(f"Nomes não encontrados no IBGE (grafia?): {faltando}")
    return codigos


def baixar_contorno(codigo):
    """Baixa o contorno (GeoJSON) de um município pelo código IBGE."""
    r = requests.get(
        f"{IBGE}/v3/malhas/municipios/{codigo}",
        params={"formato": "application/vnd.geo+json"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["features"][0]  # a resposta traz 1 "feature" por município


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    # 1. Lista oficial de SP → guarda como veio
    municipios_sp = listar_municipios_sp()
    (PASTA_SAIDA / "municipios_sp.json").write_text(
        json.dumps(municipios_sp, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"Municípios de SP no IBGE: {len(municipios_sp)}")

    # 2. Códigos dos 20 da RMC
    codigos = codigos_da_rmc(municipios_sp)
    print(f"Municípios da RMC encontrados: {len(codigos)}/20")

    # 3. Contorno de cada um
    features = []
    for nome, codigo in sorted(codigos.items()):
        feature = baixar_contorno(codigo)
        feature["properties"] = {"nome": nome, "codigo_ibge": codigo}
        features.append(feature)
        print(f"  ok  {codigo}  {nome}  ({feature['geometry']['type']})")
        time.sleep(0.3)  # pausa curta: educação com o servidor

    # 4. Junta tudo num único arquivo GeoJSON
    colecao = {"type": "FeatureCollection", "features": features}
    saida = PASTA_SAIDA / "rmc_municipios.geojson"
    saida.write_text(json.dumps(colecao, ensure_ascii=False), encoding="utf-8")
    print(f"Salvo em: {saida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
