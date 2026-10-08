#!/usr/bin/env bash
# Roda o pipeline completo, em ordem, e abre o relatório e o mapa no navegador. Para no primeiro erro.
#
# Uso:
#   ./scripts/rodar_tudo.sh              # roda tudo e abre os HTMLs (no WSL)
#   ./scripts/rodar_tudo.sh --sem-abrir  # só roda
set -euo pipefail

cd "$(dirname "$0")/.."            # vai para a raiz do projeto, de onde quer que seja chamado

# Usa o Python do .venv, se existir — assim não é preciso ativar o venv antes
if [[ -x .venv/bin/python ]]; then
    PYTHON=.venv/bin/python
else
    PYTHON=python
fi

for script in scripts/0*.py; do
    echo "════ $script"
    "$PYTHON" "$script"
    echo
done
echo "Pipeline concluído."

# Abre no navegador padrão do Windows. Só no WSL (onde existe powershell.exe);
# no CI ou num Linux comum, este trecho é pulado.
if [[ "${1:-}" != "--sem-abrir" ]] && command -v powershell.exe >/dev/null; then
    for html in entregas/relatorio_rmc.html entregas/painel_rmc.html; do
        caminho_windows=$(wslpath -w "$html")       # /home/... → \\wsl.localhost\Ubuntu\home\...
        # cd /mnt/c: o PowerShell reclama se for iniciado dentro de uma pasta do Linux
        (cd /mnt/c && powershell.exe -NoProfile -Command "Start-Process '$caminho_windows'")
    done
    echo "Abrindo relatório e mapa no navegador."
fi
