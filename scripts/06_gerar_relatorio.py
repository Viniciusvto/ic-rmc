#!/usr/bin/env python3
"""
06_gerar_relatorio.py — Gera o relatório com os gráficos (linha do tempo, municípios, anos, setores).

Entradas: dados/tratados/rmc_inventarios.csv
          dados/manual/setores.csv                (decisão humana: setor e industrial)
          scripts/templates/relatorio_rmc.html    (HTML com marcadores __DADOS__, __META__...)
          dados/brutos/fgv/organizacoes_*.json    (só a data da coleta mais recente)
Saída   : entregas/relatorio_rmc.html

Uso:
    python scripts/06_gerar_relatorio.py
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "tratados" / "rmc_inventarios.csv"
SETORES = RAIZ / "dados" / "manual" / "setores.csv"
TEMPLATE = RAIZ / "scripts" / "templates" / "relatorio_rmc.html"
SAIDA = RAIZ / "entregas" / "relatorio_rmc.html"

ANO_ATIVO = 2024  # publicou ano-base 2024 ou depois → "publicando" (mesma regra do painel de setembro)
VERDADEIRO = {"true", "sim", "1"}


# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------
def carregar():
    """Junta a base tratada com a classificação setorial manual."""
    base = pd.read_csv(CSV, dtype={"anos": str}).fillna({"observacao": ""})
    setores = pd.read_csv(SETORES, dtype=str).fillna("")
    junto = base.merge(setores, on="organizacao", how="left").fillna({"setor": ""})

    sem_setor = junto[junto.setor.str.strip() == ""]
    if not sem_setor.empty:
        raise ValueError(f"Organizações sem setor em {SETORES.relative_to(RAIZ)}: "
                         f"{list(sem_setor.organizacao)}")
    return junto


def registro(linha):
    """Converte uma linha da tabela no formato que o JavaScript do relatório espera."""
    anos = sorted(int(a) for a in linha.anos.split(";"))
    return {
        "org": linha.organizacao,
        "municipio": linha.municipio,
        "tipo": linha.tipo,
        "setor": linha.setor,
        "anos": anos,
        "ini": anos[0],
        "fim": anos[-1],
        "n": len(anos),
        "industrial": str(linha.industrial).strip().lower() in VERDADEIRO,
        "ativo": anos[-1] >= ANO_ATIVO,
    }


def data_da_coleta():
    """Data (dd/mm/aaaa) do arquivo bruto da FGV mais recente."""
    arquivos = sorted((RAIZ / "dados" / "brutos" / "fgv").glob("organizacoes_*.json"))
    if not arquivos:
        raise FileNotFoundError("Nenhuma coleta em dados/brutos/fgv. Rode o 01 antes.")
    return date.fromisoformat(arquivos[-1].stem.split("_")[-1]).strftime("%d/%m/%Y")


def marcadores(dados, n_inferidos):
    """Calcula o texto de cada marcador do template."""
    n_total = len(dados)
    inferidos = "1 inferido" if n_inferidos == 1 else f"{n_inferidos} inferidos"
    meta = (f"Coleta da API do mapa do RPE em {data_da_coleta()} · recorte por "
            f"<i>point-in-polygon</i> sobre as malhas municipais do IBGE · "
            f"{n_total} registros ({inferidos} pelo nome)")
    return {
        # "</" escapado para um nome com "</script>" não fechar o <script> do HTML
        "__DADOS__": json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"),
        "__META__": meta,
        "__N_TOTAL__": str(n_total),
        "__N_IND__": str(sum(d["industrial"] for d in dados)),
        "__N_IND_ATIVAS__": str(sum(d["industrial"] and d["ativo"] for d in dados)),
    }


def preencher(template, valores):
    """Substitui os marcadores; falha se algum não existir no template."""
    faltando = [m for m in valores if m not in template]
    if faltando:
        raise ValueError(f"Marcadores ausentes no template: {faltando}")
    for marcador, valor in valores.items():
        template = template.replace(marcador, valor)
    return template


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
def main():
    base = carregar()
    dados = [registro(l) for l in base.itertuples()]
    valores = marcadores(dados, n_inferidos=int((base.observacao != "").sum()))

    html = preencher(TEMPLATE.read_text(encoding="utf-8"), valores)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(html, encoding="utf-8")

    print(f"Relatório gerado: {SAIDA.relative_to(RAIZ)}")
    for marcador in ("__N_TOTAL__", "__N_IND__", "__N_IND_ATIVAS__", "__META__"):
        print(f"  {marcador:<18} {valores[marcador]}")


if __name__ == "__main__":
    main()
