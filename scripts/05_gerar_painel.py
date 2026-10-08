#!/usr/bin/env python3
"""
05_gerar_painel.py — Gera o mapa interativo das organizações da RMC.

Entradas: dados/tratados/rmc_inventarios.csv
          dados/brutos/ibge/rmc_municipios.geojson
Saída   : entregas/painel_rmc.html
"""

import html
import json
from pathlib import Path

import folium
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "tratados" / "rmc_inventarios.csv"
GEOJSON = RAIZ / "dados" / "brutos" / "ibge" / "rmc_municipios.geojson"
SAIDA = RAIZ / "entregas" / "painel_rmc.html"

CORES = {"Matriz": "#1f77b4", "Unidade": "#ff7f0e", "Controlada": "#2ca02c"}
# Esri: CartoDB passou a exigir chave e o OpenStreetMap devolve 403 para arquivo aberto do disco
TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
    "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
)


def data_da_coleta():
    arquivos = sorted((RAIZ / "dados" / "brutos" / "fgv").glob("organizacoes_*.json"))
    return arquivos[-1].stem.split("_")[-1] if arquivos else "?"


def main():
    df = pd.read_csv(CSV, dtype={"anos": str}).fillna({"observacao": ""})
    colecao = json.loads(GEOJSON.read_text(encoding="utf-8"))

    # Quantas organizações em cada município → aparece no tooltip e na cor de fundo
    contagem = df.municipio.value_counts()
    for f in colecao["features"]:
        f["properties"]["qtd"] = int(contagem.get(f["properties"]["nome"], 0))

    mapa = folium.Map(tiles=None)
    folium.TileLayer(TILES, attr="Tiles © Esri", name="Mapa base (Esri)").add_to(
        mapa
    )  # name = rótulo na legenda

    contornos = folium.GeoJson(
        colecao,
        name="Municípios da RMC",
        style_function=lambda f: {
            "color": "#555",
            "weight": 1,
            "fillColor": "#3388ff",
            "fillOpacity": 0.03 + 0.04 * min(f["properties"]["qtd"], 10),
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nome", "qtd"], aliases=["Município:", "Organizações:"]
        ),
    ).add_to(mapa)

    # Uma camada por tipo → dá para ligar/desligar na legenda
    camadas = {}
    for tipo, qtd in df.tipo.value_counts().items():
        camadas[tipo] = folium.FeatureGroup(name=f"{tipo} ({qtd})").add_to(mapa)

    for _, org in df.iterrows():
        inferido = bool(org.observacao)
        texto = (
            f"<b>{html.escape(org.organizacao)}</b><br>"
            f"{org.tipo} · {html.escape(org.municipio)}<br>"
            f"Anos inventariados: {org.anos.replace(';', ', ')}"
        )
        if inferido:
            texto += f"<br><i>{html.escape(org.observacao)}</i>"

        folium.CircleMarker(
            location=[org.latitude, org.longitude],
            radius=7,
            color=CORES.get(org.tipo, "gray"),
            fill=True,
            fill_opacity=0.25 if inferido else 0.8,
            dash_array="3" if inferido else None,  # tracejado = posição aproximada
            tooltip=org.organizacao,
            popup=folium.Popup(texto, max_width=300),
        ).add_to(camadas[org.tipo])

    folium.LayerControl(collapsed=False).add_to(mapa)
    mapa.fit_bounds(contornos.get_bounds())  # enquadra a RMC automaticamente

    titulo = f"""
    <div style="position:fixed; top:12px; left:60px; z-index:9999; background:white;
                padding:8px 12px; border-radius:6px; box-shadow:0 1px 4px rgba(0,0,0,.3);
                font-family:sans-serif;">
      <b>Inventários de GEE — Região Metropolitana de Campinas</b><br>
      <small>{len(df)} organizações · Fonte: Registro Público de Emissões (FGV),
      coleta em {data_da_coleta()} · Contornos: IBGE ·
      Círculo tracejado = posição aproximada</small>
    </div>"""
    mapa.get_root().html.add_child(folium.Element(titulo))

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    mapa.save(SAIDA)
    print(f"Painel gerado: {SAIDA.relative_to(RAIZ)}  ({len(df)} organizações)")


if __name__ == "__main__":
    main()
