#!/usr/bin/env bash
# Roda na VPS (cron / Dokploy Schedule). Avanca a cobrinha e publica o SVG.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/snake-runner/MatheusBraga1106}"
REPO_URL="${REPO_URL:-https://github.com/MatheusBraga1106/MatheusBraga1106.git}"
: "${GH_TOKEN:?defina GH_TOKEN (token classico com escopo repo)}"

if [ ! -d "$REPO_DIR" ]; then
  git clone "$REPO_URL" "$REPO_DIR"
fi
cd "$REPO_DIR"
git config user.name "snake-bot"
git config user.email "snake-bot@users.noreply.github.com"
git fetch origin main -q
git reset --hard origin/main -q

python3 snake/main.py \
  --user MatheusBraga1106 \
  --state snake/snake-state.json \
  --out snake.svg \
  --color "${SNAKE_COLOR:-#8b5cf6}"

git add snake.svg snake/snake-state.json
if git diff --cached --quiet; then
  echo "nada mudou hoje"
  exit 0
fi

# cache-busting: o GitHub cacheia a imagem do README pelo nome do arquivo,
# entao troca a query string a cada mudanca real pra forcar buscar de novo
sed -i -E "s#(snake\.svg)(\?v=[0-9]+)?#\1?v=$(date +%s)#" README.md
git add README.md

SUMMARY=$(python3 - <<'PY'
import json
s = json.load(open("snake/snake-state.json"))
print(f"tamanho {s['length']}, {s['totalEaten']} comidos, geracao {s['generation']}")
PY
)
git commit -q -m "cobrinha: $SUMMARY"
git push -q "https://${GH_TOKEN}@github.com/MatheusBraga1106/MatheusBraga1106.git" main
echo "publicado ($SUMMARY)"
