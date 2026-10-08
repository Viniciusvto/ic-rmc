#!/usr/bin/env bash
# Roda o pipeline completo, em ordem. Para no primeiro erro.
set -euo pipefail

cd "$(dirname "$0")/.."            # vai para a raiz do projeto, de onde quer que seja chamado

for script in scripts/0*.py; do
    echo "════ $script"
    python "$script"
    echo
done
echo "Pipeline concluído."
