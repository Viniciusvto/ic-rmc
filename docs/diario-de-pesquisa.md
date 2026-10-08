# Diário de pesquisa — IC RMC

## 2026-09-28
- Estrutura do projeto e repositório Git criados.
- Base tratada: 36 organizações, 11/20 municípios, 14 descontinuadas.
- Critério de "ativo": último ano-base >= 2024 (dois ciclos do RPE).
- Critério de "industrial": 8 setores listados em SETORES_INDUSTRIAIS
  no script 01_tratar.py.

## 2026-10-08
- Nova metodologia: coleta direta da API do mapa do RPE (2.340 pontos, Brasil) e
  recorte por point-in-polygon sobre as malhas do IBGE.
  70 candidatos na caixa envolvente → 34 dentro da RMC.
- Revisão manual: 35 pontos sem localização utilizável = 32 sem coordenada + 3 com
  coordenada fora do Brasil. Busca por nomes de municípios → 1 inclusão
  (LSL Transportes Paulínia).
- Comparação com o painel de setembro (36 registros): 34 casam por nome, com campos
  idênticos. Faltavam 2:
  - "BDO ... - Campinas": está na coleta como "BDO ... - CAM" (nome truncado), já dentro
    da RMC pelas coordenadas; só o setor precisou ser preenchido à mão.
  - "LSL Transportes - Campinas": está como "LSL Transportes CAM", sem coordenada.
    A busca por nomes de municípios não o pegou por causa da sigla. Incluído como
    inferido (Campinas), com justificativa em dados/manual/inclusoes_rmc.csv.
- Total final: 36 (34 + 2 inferidos) — Matriz 20, Unidade 10, Controlada 6.
  13 industriais, 8 deles ainda publicando (mesmos números de setembro).
- Lição: na revisão manual, procurar também siglas (ex.: CAM) além dos nomes dos municípios.
- Setores: dados/manual/setores.csv, herdado do painel de setembro (util_setores_antigos.py).
- Painel de setembro preservado em referencias/painel_antigo_2026-09.html (commit 9642646).
