# Inventários de GEE na Região Metropolitana de Campinas

Levantamento das organizações da **Região Metropolitana de Campinas (RMC)** que publicaram
inventários de emissões de gases de efeito estufa no **Registro Público de Emissões (FGV / Programa
Brasileiro GHG Protocol)**.

Projeto de Iniciação Científica — FATEC Campinas, com apoio da FAPESP.
Autor: Vinicius Teixeira de Oliveira · Orientador: <nome>

## Resultado

Coleta de 08/10/2026:

| Etapa | Quantidade |
|---|---|
| Pontos no mapa do Registro Público de Emissões (Brasil) | 2.340 |
| Candidatos no retângulo envolvente da RMC | 70 |
| Dentro da RMC pelo recorte *point-in-polygon* | 34 |
| Pontos sem localização utilizável (revisados manualmente) | 35 = 32 sem coordenada + 3 fora do Brasil |
| Incluídos pela revisão manual (município inferido pelo nome) | 2 — LSL Transportes Paulínia, LSL Transportes CAM |
| **Total final** | **36** (Matriz 20 · Unidade 10 · Controlada 6) |

O painel de setembro/2026 (metodologia anterior) também tinha 36 registros; ele está preservado em
`referencias/painel_antigo_2026-09.html`.

Mapa interativo: `entregas/painel_rmc.html`
Relatório com gráficos: `entregas/relatorio_rmc.html`
Tabela final: `dados/tratados/rmc_inventarios.csv`

## Como rodar

Requisitos: Python 3 e acesso à internet.

```bash
git clone <url-do-repositorio>
cd ic-rmc
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/rodar_tudo.sh
```

Para abrir no WSL: `cd entregas && explorer.exe .` e dar dois cliques no arquivo
(`explorer.exe` não aceita caminho com `/`).

O `01` não sobrescreve uma coleta já feita no mesmo dia, e o `02` não baixa de novo os contornos do
IBGE se eles já existem (use `python scripts/02_baixar_municipios.py --atualizar` para forçar).

## Desenvolvimento

```bash
pip install -r requirements-dev.txt   # pipeline + pytest + ruff
pytest                                # testes das funções e da integridade dos dados
ruff check scripts tests              # erros e estilo
ruff format scripts tests             # formata o código
```

A cada push, o GitHub Actions (`.github/workflows/ci.yml`) roda o ruff, os testes e o pipeline
03–06 a partir dos dados brutos versionados, e falha se a tabela final ou o relatório não saírem
idênticos aos do repositório.

## Como funciona

| Script | O que faz | Saída |
|---|---|---|
| `01_coletar_fgv.py` | Baixa todos os pontos do mapa da FGV (endpoint `SearchOrganizationsGeolocalization`) | `dados/brutos/fgv/organizacoes_AAAA-MM-DD.json` |
| `02_baixar_municipios.py` | Baixa do IBGE os contornos dos 20 municípios da RMC | `dados/brutos/ibge/rmc_municipios.geojson` |
| `03_filtrar_rmc.py` | Recorte grosseiro (retângulo) + recorte fino (*point-in-polygon*) | `dados/intermediarios/` |
| `04_limpar.py` | Padroniza nomes, remove duplicatas, aplica inclusões manuais | `dados/tratados/rmc_inventarios.csv` |
| `05_gerar_painel.py` | Gera o mapa interativo | `entregas/painel_rmc.html` |
| `06_gerar_relatorio.py` | Preenche o template com os dados e os setores | `entregas/relatorio_rmc.html` |

`util_setores_antigos.py` (uso único, sem número de propósito para o `rodar_tudo.sh` não executá-lo)
criou `dados/manual/setores.csv` a partir da classificação do painel de setembro.
O relatório usa o template `scripts/templates/relatorio_rmc.html`; os comentários `<!-- REVISAR -->`
nele marcam notas com afirmações factuais a conferir a cada nova coleta.

**Por que via API e não pela interface:** o mapa da FGV só filtra por estado. A API que alimenta o
mapa devolve todos os pontos com latitude e longitude, o que permite um recorte municipal exato.

**Revisão manual:** pontos sem coordenada ou com coordenada fora do Brasil (erro de cadastro na
fonte) são listados em `dados/intermediarios/revisar_fora_do_brasil.csv`, com a coluna `motivo`.
As decisões humanas ficam em `dados/manual/`:

| Arquivo | Conteúdo |
|---|---|
| `inclusoes_rmc.csv` | Organizações reconhecidas como da RMC, com município e justificativa; saem como "inferido" |
| `setores.csv` | Setor e indicador `industrial` (True/False) de cada organização; o `06` falha se faltar alguma |

## Estrutura

```
dados/brutos/          dados como vieram da fonte (não editar)
dados/intermediarios/  etapas do meio (refeitas a cada execução)
dados/manual/          decisões humanas (nunca sobrescritas por scripts)
dados/tratados/        tabela final
scripts/               pipeline, em ordem numérica
scripts/templates/     HTML do relatório com marcadores (__DADOS__, __META__…)
entregas/              mapa, relatório e materiais finais
docs/                  diário de pesquisa (versionado) e anotações (fora do Git)
referencias/           materiais de terceiros
```

## Fontes

- **Registro Público de Emissões — FGV / Programa Brasileiro GHG Protocol:**
  https://registropublicodeemissoes.fgv.br
- **IBGE — APIs de Localidades e Malhas Territoriais:** https://servicodados.ibge.gov.br
- **Composição da RMC:** Lei Complementar Estadual nº 870/2000 (19 municípios), com inclusão de
  Morungaba em 2014.

## Limitações

- O levantamento cobre apenas organizações que publicaram no Registro Público de Emissões, que é
  voluntário. Não representa todas as emissoras da região.
- A localização vem do cadastro de endereço da própria organização. Erros de cadastro podem colocar
  um ponto no município errado ou fora do país.
- Uma organização é contada pelo ponto cadastrado, que pode ser a matriz, uma unidade ou uma
  controlada. A mesma empresa pode aparecer mais de uma vez.
- A API da FGV não é documentada publicamente e pode mudar sem aviso.
