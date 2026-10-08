#!/usr/bin/env python3
"""
util_setores_antigos.py — USO ÚNICO. Cria dados/manual/setores.csv reaproveitando a
classificação de setores do painel de setembro (referencias/painel_antigo_2026-09.html).

Não começa com número de propósito: o rodar_tudo.sh só executa scripts/0*.py.
"""

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ANTIGO = RAIZ / "referencias" / "painel_antigo_2026-09.html"
ATUAL = RAIZ / "dados" / "tratados" / "rmc_inventarios.csv"
DESTINO = RAIZ / "dados" / "manual" / "setores.csv"


def chave(texto):
    """Normaliza nomes para comparar: sem acento, minúsculo, só letras e números.
    'LSL Transportes - Paulínia' e 'LSL Transportes Paulínia' viram a mesma chave."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def main():
    if DESTINO.exists():
        raise SystemExit(f"{DESTINO.relative_to(RAIZ)} já existe — não vou sobrescrever decisões manuais.")

    html = ANTIGO.read_text(encoding="utf-8")
    trecho = re.search(r"const DADOS = (\[.*?\]);", html, re.S)
    if not trecho:
        raise SystemExit("Não encontrei 'const DADOS = [...]' no painel antigo.")
    antigos = {chave(d["org"]): (d["setor"], d["industrial"]) for d in json.loads(trecho.group(1))}

    atual = pd.read_csv(ATUAL)
    linhas, sem_par = [], []
    for org in atual.organizacao:
        setor, industrial = antigos.get(chave(org), ("", ""))
        if not setor:
            sem_par.append(org)
        linhas.append({"organizacao": org, "setor": setor, "industrial": industrial})

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(linhas).to_csv(DESTINO, index=False, encoding="utf-8")
    print(f"Criado: {DESTINO.relative_to(RAIZ)}")
    print(f"Classificadas automaticamente: {len(linhas) - len(sem_par)}/{len(linhas)}")
    if sem_par:
        print("Preencha à mão (setor e industrial True/False):")
        for org in sem_par:
            print(f"  - {org}")


if __name__ == "__main__":
    main()
