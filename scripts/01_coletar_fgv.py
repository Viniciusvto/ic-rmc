#!/usr/bin/env python3
"""
01_coletar_fgv.py — Baixa todos os pontos do mapa do Registro Público de Emissões (FGV).

Entrada : API da FGV (endpoint SearchOrganizationsGeolocalization)
Saída   : dados/brutos/fgv/organizacoes_AAAA-MM-DD.json  (resposta original, sem alteração)

Uso:
    python scripts/01_coletar_fgv.py
"""

import json
from collections import Counter
from datetime import date
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent          # .../ic-rmc
PASTA_SAIDA = RAIZ / "dados" / "brutos" / "fgv"

URL = ("https://registropublicodeemissoesapi.fgv.br/api/services/app/"
       "EstatisticaPublica/SearchOrganizationsGeolocalization")
CABECALHOS = {"User-Agent": "Mozilla/5.0 (pesquisa de IC - FATEC Campinas)"}
CAMPOS_ESPERADOS = {"latitude", "longitude", "organizationName",
                    "organizationTypeName", "invetoriedYears"}


# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------
def baixar():
    """Faz o POST sem filtros e devolve o corpo da resposta (dicionário)."""
    resposta = requests.post(URL, json={}, headers=CABECALHOS, timeout=60)
    resposta.raise_for_status()                 # erro HTTP (404, 500...) para aqui
    corpo = resposta.json()
    if not corpo.get("success"):
        raise RuntimeError(f"A API respondeu sem sucesso: {corpo.get('error')}")
    return corpo


def conferir(pontos):
    """Verificações mínimas: veio algo? os campos são os esperados?"""
    if not pontos:
        raise RuntimeError("A API devolveu uma lista vazia.")
    faltando = CAMPOS_ESPERADOS - set(pontos[0])
    if faltando:
        raise RuntimeError(f"Campos ausentes na resposta: {faltando}")

    print(f"Pontos recebidos: {len(pontos)}")
    for tipo, qtd in Counter(p["organizationTypeName"] for p in pontos).most_common():
        print(f"  {tipo:<12} {qtd}")


def salvar(corpo):
    """Grava a resposta original com a data da coleta no nome do arquivo."""
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    arquivo = PASTA_SAIDA / f"organizacoes_{date.today().isoformat()}.json"
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(corpo, f, ensure_ascii=False, indent=1)
    print(f"Salvo em: {arquivo.relative_to(RAIZ)}")


def main():
    corpo = baixar()
    conferir(corpo["result"]["organizations"])
    salvar(corpo)


if __name__ == "__main__":
    main()
