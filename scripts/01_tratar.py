#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_tratar.py — Tratamento da base de organizações da RMC com inventário de GEE

Entrada : dados/brutos/levantamento_rmc.csv   (o levantamento como foi extraído)
Saída   : dados/tratados/rmc_inventarios_analise.csv

Este script NUNCA altera o arquivo de entrada. Ele lê, transforma e escreve
em outro lugar. Se o resultado sair errado, você corrige o script e roda de
novo — o dado de origem continua intacto.

Uso:
    python 01_tratar.py
    python 01_tratar.py --entrada outro_arquivo.csv --saida saida.csv
"""

import argparse
import csv
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. PARÂMETROS DE CLASSIFICAÇÃO
#
# Tudo que envolve julgamento humano fica aqui em cima, visível e auditável.
# Quando alguém perguntar "por que a Symrise conta como indústria?", a
# resposta está nesta lista, e não escondida no meio do código.
# ---------------------------------------------------------------------------

SETORES_INDUSTRIAIS = {
    "Automotivo - Montadora",
    "Automotivo - Autopeças",
    "Eletroeletrônicos",
    "Química - Aromas e Fragrâncias",
    "Farmacêutico - Saúde Animal",
    "Alimentos e Ingredientes",
    "Bens de Capital",
    "Higiene Pessoal e Cosméticos",
}

# Um registro é considerado "ativo" quando publicou este ano-base ou depois.
# 2024 é o corte porque o ciclo mais recente do RPE (publicado em junho/2026)
# tem 2025 como ano-base — quem parou antes de 2024 saiu de pelo menos dois
# ciclos seguidos.
ANO_CORTE_ATIVO = 2024

# Os 20 municípios da Região Metropolitana de Campinas.
# Serve para validar o recorte: se aparecer um município fora desta lista,
# o script avisa em vez de aceitar em silêncio.
RMC_20 = [
    "Americana", "Artur Nogueira", "Campinas", "Cosmópolis",
    "Engenheiro Coelho", "Holambra", "Hortolândia", "Indaiatuba",
    "Itatiba", "Jaguariúna", "Monte Mor", "Morungaba",
    "Nova Odessa", "Paulínia", "Pedreira", "Santa Bárbara d'Oeste",
    "Santo Antônio de Posse", "Sumaré", "Valinhos", "Vinhedo",
]


# ---------------------------------------------------------------------------
# 2. LEITURA
# ---------------------------------------------------------------------------

def abrir_csv(caminho):
    """Lê um CSV tentando as codificações mais comuns no Brasil.

    Por que isso existe: um CSV salvo pelo Excel em português costuma vir em
    cp1252 (a codificação antiga do Windows), enquanto qualquer coisa exportada
    de sistema web vem em UTF-8. Se você abrir um com a codificação do outro,
    "Paulínia" vira "Paulï¿½nia" — ou o Python levanta UnicodeDecodeError.

    Tentar em ordem resolve o problema de uma vez, em vez de você descobrir na
    marra toda vez que trocar de arquivo.
    """
    for codificacao in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(caminho, encoding=codificacao, newline="") as f:
                linhas = list(csv.DictReader(f, delimiter=";"))
            print(f"  lido em {codificacao}: {len(linhas)} linhas")
            return linhas
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"ERRO: não consegui decodificar {caminho}")


# ---------------------------------------------------------------------------
# 3. TRANSFORMAÇÃO
# ---------------------------------------------------------------------------

def expandir_anos(texto):
    """Converte o campo de anos em uma lista de inteiros.

    O campo vem em dois formatos misturados na mesma coluna:
        "2024"                      -> [2024]
        "2023,2024,2025"            -> [2023, 2024, 2025]
        "2011-2025"                 -> [2011, 2012, ..., 2025]
        "2015,2017-2019"            -> [2015, 2017, 2018, 2019]

    Foi exatamente aqui que o int() quebrou na primeira tentativa: o código
    tratava tudo como lista separada por vírgula e engasgava no "2011-2025".

    Usar set() no meio do caminho elimina duplicata (se o mesmo ano aparecer
    escrito de duas formas) e sorted() devolve em ordem crescente.
    """
    anos = set()
    for pedaco in str(texto).split(","):
        pedaco = pedaco.strip()
        if not pedaco:
            continue
        if "-" in pedaco:
            inicio, fim = pedaco.split("-")
            anos.update(range(int(inicio), int(fim) + 1))
        else:
            anos.add(int(pedaco))
    return sorted(anos)


def tratar(linhas):
    """Recebe as linhas cruas e devolve os registros com os campos derivados."""
    registros = []
    avisos = []

    for posicao, linha in enumerate(linhas, start=1):
        # .get() com valor padrão evita KeyError se a coluna não existir;
        # .strip() tira espaço sobrando, que é invisível e quebra comparação.
        organizacao = (linha.get("organizacao") or "").strip()
        municipio = (linha.get("municipio") or "").strip()
        setor = (linha.get("setor") or "Não identificado").strip()

        if not organizacao:
            avisos.append(f"linha {posicao}: sem nome de organização — pulada")
            continue

        anos = expandir_anos(linha.get("anos_inventariados", ""))
        if not anos:
            avisos.append(f"linha {posicao}: {organizacao} sem anos — pulada")
            continue

        if municipio not in RMC_20:
            avisos.append(f"linha {posicao}: '{municipio}' não é município da RMC")

        primeiro, ultimo = min(anos), max(anos)

        registros.append({
            # id estável: nome de empresa muda de grafia entre fontes, id não.
            # É por ele que a planilha de codificação manual se liga a esta base.
            "id": f"RMC{posicao:03d}",
            "org": organizacao,
            "municipio": municipio,
            "tipo": (linha.get("tipo_registro") or "").strip(),
            "setor": setor,
            "anos": ";".join(str(a) for a in anos),
            "ini": primeiro,
            "fim": ultimo,
            "n": len(anos),
            # Série contínua? len(anos) == intervalo significa que não falta
            # nenhum ano no meio. "2017-2021" tem 5 anos e 5 de intervalo: ok.
            # "2015,2020" tem 2 anos e 6 de intervalo: tem buraco.
            "continua": len(anos) == (ultimo - primeiro + 1),
            "industrial": setor in SETORES_INDUSTRIAIS,
            "ativo": ultimo >= ANO_CORTE_ATIVO,
            "obs": (linha.get("observacao") or "").strip(),
        })

    return registros, avisos


# ---------------------------------------------------------------------------
# 4. ESCRITA
# ---------------------------------------------------------------------------

COLUNAS = ["id", "org", "municipio", "tipo", "setor", "anos",
           "ini", "fim", "n", "continua", "industrial", "ativo", "obs"]


def salvar(registros, caminho):
    """Grava o CSV tratado.

    utf-8-sig põe um marcador invisível (BOM) no começo do arquivo que faz o
    Excel abrir os acentos corretamente. Sem ele, "Paulínia" aparece torto na
    planilha — e você vai achar que o script está errado quando é só o Excel
    adivinhando a codificação.

    O separador é ; porque é o que o Excel em português espera. Como o campo
    de anos usa ; internamente, aqui ele já foi convertido para lista unida
    por ; ... o que colidiria. Por isso os anos saem unidos por ';' dentro de
    aspas — o módulo csv cuida do escape sozinho.
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
        escritor.writeheader()
        escritor.writerows(registros)


# ---------------------------------------------------------------------------
# 5. EXECUÇÃO
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", default="dados/brutos/levantamento_rmc.csv")
    parser.add_argument("--saida", default="dados/tratados/rmc_inventarios_analise.csv")
    args = parser.parse_args()

    if not Path(args.entrada).exists():
        raise SystemExit(f"ERRO: não encontrei {args.entrada}")

    print(f"Lendo {args.entrada}")
    linhas = abrir_csv(args.entrada)

    print("Tratando")
    registros, avisos = tratar(linhas)

    if avisos:
        print(f"\n  {len(avisos)} aviso(s):", file=sys.stderr)
        for aviso in avisos:
            print(f"    ! {aviso}", file=sys.stderr)

    salvar(registros, args.saida)
    print(f"\nGravado {args.saida}: {len(registros)} registros")


if __name__ == "__main__":
    main()
