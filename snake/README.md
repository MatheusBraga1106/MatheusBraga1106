# Cobrinha do perfil

Snake jogado de verdade em cima do grid de contribuições, com **estado
persistente**: a cobrinha não recomeça do zero a cada execução — ela guarda
onde parou e quanto cresceu em `snake-state.json`.

Diferente do `Platane/snk` (que só reproduz o ano inteiro com tamanho fixo),
aqui cada dia com atividade vira uma comida no tabuleiro e some quando ela
passa por cima.

## Regras

- **Cresce 1 quadrado** por dia com atividade que ela consegue comer.
- **Não atravessa o próprio corpo** e não volta 180°: cada passo sai de uma
  busca em largura (BFS) que trata o corpo como parede.
- **Só come se for seguro**: antes de avançar ela confere se ainda vai
  conseguir alcançar o próprio rabo. Se não der, entra em modo sobrevivência
  e persegue o rabo até abrir espaço.
- **Game over** quando fica sem saída ou quando enche o tabuleiro — aí renasce
  pequena e o contador de geração sobe.
- Ela persegue a comida alcançável **mais próxima**, não a ordem do
  calendário: seguir a data engessa o trajeto e faz o corpo cair justamente em
  cima dos dias seguintes.

## Uso

```bash
export GH_TOKEN=...          # token classico, escopo repo
python3 main.py --user MatheusBraga1106
```

Sem token, para experimentar com dados falsos:

```bash
python3 main.py --demo
```

Opções: `--color` (cor da cobrinha), `--frame-ms` (velocidade),
`--backfill` (quantos dias de histórico ela come na primeira rodada),
`--out`, `--state`.

## Testes

```bash
python3 test_rules.py
```

Simula centenas de dias e valida, frame a frame, que nenhum passo teleporta,
sai do tabuleiro ou sobrepõe o próprio corpo.

## Arquivos

| Arquivo | Papel |
|---|---|
| `engine.py` | Regras do jogo, pathfinding e estado persistente |
| `render.py` | Monta o SVG animado (CSS puro, sem JS) |
| `github_data.py` | Busca a atividade diária via GraphQL |
| `main.py` | Junta tudo pela linha de comando |
| `run.sh` | O que a VPS executa todo dia |

O SVG usa só animação CSS com `prefers-color-scheme`, então funciona dentro de
um `<img>` no README e acompanha o tema claro/escuro de quem está olhando.
