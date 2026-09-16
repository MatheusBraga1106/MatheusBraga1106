# Cobrinha do perfil

Snake jogado de verdade em cima do grid de contribuições, com **estado
persistente**: a cobrinha não recomeça do zero a cada execução — ela guarda
onde parou e quanto cresceu em `snake-state.json`.

Diferente do `Platane/snk` (que só reproduz o ano inteiro com tamanho fixo),
aqui cada dia com atividade vira uma comida no tabuleiro e some quando ela
passa por cima.

## Regras

- **Cresce 1 quadrado** por dia com atividade que ela consegue comer.
- **Não atravessa o próprio corpo**: cada passo trata o corpo como parede.
- **Só anda se for seguro**: antes de avançar ela confere se ainda vai
  conseguir alcançar o próprio rabo e se sobra espaço livre pro corpo inteiro
  (mais uma folga). Se não der, persegue o próprio rabo até abrir espaço.
- **Game over** só quando fica sem nenhum vizinho livre ou quando enche o
  tabuleiro — aí renasce pequena e o contador de geração sobe.
- Ela persegue a comida alcançável **mais próxima**, não a ordem do
  calendário: seguir a data engessa o trajeto e faz o corpo cair justamente em
  cima dos dias seguintes.
- O calendário **desliza por baixo dela** toda semana; a cobrinha vive em
  coordenadas do tabuleiro e não se move quando isso acontece.

## Como o estado é guardado

O corpo é gravado **explicitamente** (`body`), não derivado de `path` + um
comprimento. Derivar era frágil: qualquer descompasso entre os dois (corte da
janela, crescimento, renascimento) virava corpo fantasma ou colisão invisível.

| Campo | Papel |
|---|---|
| `body` | células ocupadas, cabeça primeiro — `len(body)` é o tamanho |
| `path` | trilha da cabeça dentro da janela de animação (até 300 frames) |
| `bodyAtPathStart` | corpo no frame 0 da janela |
| `events` | `{frame, cell, date}` de cada comida engolida na janela |
| `eaten` | dias já consumidos (nunca viram comida de novo) |

Estados antigos (v1/v2) são migrados automaticamente, preservando placar e
geração.

## Como a animação funciona

Todos os segmentos compartilham **um** keyframe (`p`, a trilha da cabeça) e se
diferenciam só pelo `animation-delay`: o segmento `k` anda `k` frames
atrasado. Isso mantém o SVG pequeno, mas tem uma armadilha — o CSS faz `mod`
na duração, então no começo de cada volta os segmentos de índice maior que o
frame atual davam a volta e apareciam no **fim** da trilha, do outro lado do
tabuleiro. Como essa janela quebrada tem o tamanho da cobrinha, o defeito
piorava conforme ela crescia.

Duas correções:

1. A trilha animada começa com o próprio corpo ao contrário, então o ciclo
   abre com a cabeça saindo de onde a cauda está e percorrendo o próprio
   corpo — contínuo, sem salto.
2. Cada segmento só fica visível a partir de `max(k, frame em que nasceu)`,
   o que elimina de vez a faixa teleportada.

## Uso

```bash
export GH_TOKEN=...          # token classico, escopo repo
py main.py --user MatheusBraga1106
```

Sem token, para experimentar com dados falsos:

```bash
py main.py --demo
```

Opções: `--color` (cor da cobrinha), `--frame-ms` (velocidade), `--max-foods`
(quantos quadrados ela come por execução), `--out`, `--state`.

## Testes

```bash
py tests.py            # tudo (~45s)
py tests.py rapido     # só o essencial (~10s)
```

A suíte valida os dois lados:

- **motor** — invariantes do jogo a cada passo (corpo sem sobreposição, dentro
  do tabuleiro, conexo, cabeça sempre em célula vizinha);
- **render** — o SVG é **lido de volta** e a animação é reconstruída com a
  semântica real do CSS (inclusive o `mod` da duração), conferindo frame a
  frame que o corpo desenhado bate exatamente com o corpo do motor.

Além dos casos de erro (atividade vazia, comida sob o corpo, tabuleiro lotado,
migração de estado quebrado, borda do corte da janela, deslize do calendário),
ela emula até **3 anos de commits** em várias densidades.

## Arquivos

| Arquivo | Papel |
|---|---|
| `engine.py` | Regras do jogo, pathfinding e estado persistente |
| `render.py` | Monta o SVG animado (CSS puro, sem JS) |
| `github_data.py` | Busca a atividade diária via GraphQL |
| `main.py` | Junta tudo pela linha de comando |
| `tests.py` | Suíte de testes (motor + SVG) |
| `run.sh` | O que a VPS executa todo dia |

O SVG usa só animação CSS com `prefers-color-scheme`, então funciona dentro de
um `<img>` no README e acompanha o tema claro/escuro de quem está olhando.
