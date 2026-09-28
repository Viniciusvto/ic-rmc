#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_analisar.py — Números da base tratada

Entrada : dados/tratados/rmc_inventarios_analise.csv
Saída   : relatório no terminal (e --md grava em Markdown)

Este script só LÊ. Ele não altera nada. Rodar duas vezes dá o mesmo
resultado — é o que torna os números do relatório reproduzíveis: qualquer
pessoa roda e confere.

Uso:
    python 02_analisar.py
    python 02_analisar.py --md resultados.md
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

RMC_20 = [
    "Americana", "Artur Nogueira", "Campinas", "Cosmópolis",
    "Engenheiro Coelho", "Holambra", "Hortolândia", "Indaiatuba",
    "Itatiba", "Jaguariúna", "Monte Mor", "Morungaba",
    "Nova Odessa", "Paulínia", "Pedreira", "Santa Bárbara d'Oeste",
    "Santo Antônio de Posse", "Sumaré", "Valinhos", "Vinhedo",
]


def carregar(caminho):
    """Lê o CSV tratado e devolve os registros com os tipos certos.

    Todo CSV é texto. O número 16 gravado em disco volta como a string "16",
    e "16" < "9" é verdadeiro em ordem alfabética. Converter os campos
    numéricos e booleanos na entrada evita esse erro silencioso mais adiante.
    """
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        registros = list(csv.DictReader(f, delimiter=";"))

    for r in registros:
        r["ini"] = int(r["ini"])
        r["fim"] = int(r["fim"])
        r["n"] = int(r["n"])
        # "True"/"False" vêm como texto; bool("False") seria True, então
        # a comparação explícita é obrigatória aqui.
        r["continua"] = r["continua"] == "True"
        r["industrial"] = r["industrial"] == "True"
        r["ativo"] = r["ativo"] == "True"
        r["lista_anos"] = [int(a) for a in r["anos"].split(";")]

    return registros


def analisar(reg):
    """Monta o relatório inteiro como lista de linhas de texto."""
    L = []
    def p(texto=""):
        L.append(texto)

    total = len(reg)

    # --- panorama -----------------------------------------------------------
    p("# Inventários de GEE na RMC — leitura do catálogo")
    p()
    p(f"- Registros: **{total}**")
    p(f"- Municípios com ao menos um registro: **{len({r['municipio'] for r in reg})} de 20**")
    p(f"- Tipo: " + ", ".join(f"{v} {k}" for k, v in Counter(r["tipo"] for r in reg).most_common()))
    p()

    # --- cobertura municipal ------------------------------------------------
    # Counter conta as ocorrências; o .get(m, 0) garante que municípios sem
    # nenhum registro apareçam como zero em vez de sumirem da tabela. Esse
    # zero é resultado, não ausência de dado.
    contagem = Counter(r["municipio"] for r in reg)
    p("## Cobertura por município")
    p()
    p("| Município | Registros |")
    p("|---|---:|")
    for m in sorted(RMC_20, key=lambda x: (-contagem.get(x, 0), x)):
        p(f"| {m} | {contagem.get(m, 0)} |")
    zerados = [m for m in RMC_20 if contagem.get(m, 0) == 0]
    p()
    p(f"Sem nenhum registro ({len(zerados)}): {', '.join(zerados)}.")
    p()

    # --- continuidade de publicação -----------------------------------------
    ativos = [r for r in reg if r["ativo"]]
    parados = [r for r in reg if not r["ativo"]]
    p("## Continuidade")
    p()
    p(f"- Ainda publicando: **{len(ativos)}**")
    p(f"- Descontinuados: **{len(parados)}** ({len(parados) / total:.0%})")
    p()
    p("| Organização | Município | Parou em |")
    p("|---|---|---:|")
    for r in sorted(parados, key=lambda x: x["fim"]):
        p(f"| {r['org']} | {r['municipio']} | {r['fim']} |")
    p()

    # --- profundidade da série ----------------------------------------------
    faixas = Counter()
    for r in reg:
        n = r["n"]
        faixas["1 ano" if n == 1 else
               "2 a 4 anos" if n < 5 else
               "5 a 9 anos" if n < 10 else
               "10 anos ou mais"] += 1
    p("## Profundidade da série")
    p()
    p("| Faixa | Registros |")
    p("|---|---:|")
    for faixa in ["1 ano", "2 a 4 anos", "5 a 9 anos", "10 anos ou mais"]:
        p(f"| {faixa} | {faixas[faixa]} |")
    p()

    # A amostra que realmente sustenta análise temporal: série longa E viva.
    # Separar as duas condições é o ponto — uma série de 6 anos que terminou
    # em 2015 não serve para falar do que as empresas fazem hoje.
    nucleo = sorted((r for r in reg if r["n"] >= 5 and r["ativo"]),
                    key=lambda x: -x["n"])
    p(f"Com 5 anos ou mais: **{sum(1 for r in reg if r['n'] >= 5)}**. "
      f"Dessas, ainda publicando: **{len(nucleo)}**.")
    p()
    p("| Organização | Anos | Série | Setor |")
    p("|---|---:|---|---|")
    for r in nucleo:
        p(f"| {r['org']} | {r['n']} | {r['ini']}–{r['fim']} | {r['setor']} |")
    p()

    # --- séries com lacuna ---------------------------------------------------
    lacunas = [r for r in reg if not r["continua"]]
    p(f"Séries com ano faltando no meio: **{len(lacunas)}**"
      + ("." if not lacunas else ": " + ", ".join(r["org"] for r in lacunas) + "."))
    p()

    # --- perfil setorial -----------------------------------------------------
    industriais = [r for r in reg if r["industrial"]]
    p("## Perfil setorial")
    p()
    p(f"- Indústria de transformação: **{len(industriais)}** "
      f"(ativos: {sum(1 for r in industriais if r['ativo'])})")
    p(f"- Serviços, logística e infraestrutura: **{total - len(industriais)}**")
    p()
    p("| Setor | Registros | Indústria |")
    p("|---|---:|---|")
    setores = Counter(r["setor"] for r in reg)
    eh_ind = {r["setor"]: r["industrial"] for r in reg}
    for s, v in sorted(setores.items(), key=lambda kv: (-kv[1], kv[0])):
        p(f"| {s} | {v} | {'sim' if eh_ind[s] else 'não'} |")
    p()

    # --- evolução temporal ---------------------------------------------------
    # Um registro "cobre" um ano se aquele ano está na sua lista. Um mesmo
    # registro entra em vários anos — por isso a soma da coluna é maior que 36.
    por_ano = Counter()
    for r in reg:
        for ano in r["lista_anos"]:
            por_ano[ano] += 1
    p("## Organizações publicando, por ano-base")
    p()
    p("| Ano | Registros | |")
    p("|---:|---:|---|")
    for ano in range(min(por_ano), max(por_ano) + 1):
        q = por_ano.get(ano, 0)
        p(f"| {ano} | {q} | {'█' * q} |")
    p()

    return L


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", default="dados/tratados/rmc_inventarios_analise.csv")
    parser.add_argument("--md", help="grava o relatório em um arquivo Markdown")
    args = parser.parse_args()

    if not Path(args.entrada).exists():
        raise SystemExit(f"ERRO: não encontrei {args.entrada}. Rode 01_tratar.py antes.")

    linhas = analisar(carregar(args.entrada))
    texto = "\n".join(linhas)
    print(texto)

    if args.md:
        Path(args.md).write_text(texto, encoding="utf-8")
        print(f"\n[gravado em {args.md}]")


if __name__ == "__main__":
    main()
