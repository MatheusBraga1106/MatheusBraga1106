"""Gera o SVG animado a partir do estado da cobrinha.

Como a animacao funciona (e por que a versao anterior quebrava)
---------------------------------------------------------------
Todos os segmentos compartilham UM keyframe (`p`, a trilha da cabeca) e se
diferenciam so pelo `animation-delay`: o segmento k anda k frames atrasado.
Isso mantem o SVG pequeno, mas o CSS faz `mod` na duracao - entao, no
comeco de cada volta, os segmentos de indice maior que o frame atual
"davam a volta" e apareciam la no FIM da trilha, do outro lado do
tabuleiro: corpo teleportado, desconexo e com celulas repetidas durante os
primeiros `len(corpo)` frames de cada ciclo. Como essa janela quebrada tem
o tamanho da cobrinha, o defeito PIORAVA conforme ela crescia.

Duas correcoes:

1. A trilha animada comeca com o proprio corpo ao contrario (da cauda ate a
   cabeca). Assim o ciclo abre com a cabeca saindo de onde a cauda esta e
   percorrendo o proprio corpo - continuo, sem salto.
2. Cada segmento so fica visivel a partir do frame em que ele realmente
   existe (`max(k, frame em que nasceu)`), o que elimina de vez a faixa
   teleportada do `mod`.

Tambem corrige a duracao: com N keyframes o ciclo dura (N-1)*frame_ms, e
nao N*frame_ms - senao cada passo fica levemente mais longo que o atraso
entre segmentos e o corpo vai saindo do alinhamento com o grid.
"""
from datetime import date

from engine import COLS, ROWS, date_to_cell

CELL, GAP, PAD = 11, 3, 10
PITCH = CELL + GAP

LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
DARK = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def _level(count):
    for i, limit in enumerate((1, 3, 6, 10)):
        if count < limit:
            return i
    return 4


def _xy(col, row):
    return PAD + col * PITCH, PAD + row * PITCH


def animation_path(state):
    """Trilha da animacao: corpo ao contrario + trilha da cabeca.

    Devolve (frames, prefixo). O prefixo e quantos frames vieram do corpo,
    ou seja, o frame `prefixo` corresponde ao frame 0 do `path`.
    """
    start_body = [tuple(c) for c in state["bodyAtPathStart"]]
    path = [tuple(c) for c in state["path"]]
    prefix = list(reversed(start_body[1:]))     # da cauda ate encostar na cabeca
    return prefix + path, len(prefix)


def segment_births(state, frames, prefix):
    """Frame em que cada segmento passa a existir.

    Combina as duas regras: o segmento k so aparece depois de k frames (pra
    nao dar a volta pelo fim do ciclo) e depois que a cobrinha cresceu o
    suficiente pra ter esse segmento.
    """
    grow_at = sorted(e["frame"] + prefix for e in state["events"])
    base = len(state["bodyAtPathStart"])

    births, length = [], 0
    for f in range(len(frames)):
        logical = base + sum(1 for g in grow_at if g <= f)
        visible = min(f + 1, logical)
        while length < visible:
            births.append(f)
            length += 1
    return births


def render(state, activity, anchor, snake_color="#8b5cf6", frame_ms=140):
    frames, prefix = animation_path(state)
    if len(frames) < 2:
        frames = frames * 2
        prefix = 0
    n = len(frames)
    total = (n - 1) * frame_ms / 1000.0      # 1 passo = exatamente frame_ms
    step = frame_ms / 1000.0

    births = segment_births(state, frames, prefix)
    max_len = len(births)

    ja_comido = set(state.get("eaten", ()))
    cells = {}
    for day, a in activity.items():
        if date.fromisoformat(day) < anchor or a.get("count", 0) <= 0:
            continue
        col, row = date_to_cell(day, anchor)
        if 0 <= col < COLS and 0 <= row < ROWS:
            cells[(col, row)] = (_level(a["count"]), day in ja_comido)
    eaten = {tuple(e["cell"]): e["frame"] + prefix for e in state["events"]}

    w = PAD * 2 + COLS * PITCH - GAP
    h = PAD * 2 + ROWS * PITCH - GAP

    def pct(frame):
        return frame * 100.0 / (n - 1)

    # duracao/ritmo ficam uma vez so em `.s`; cada segmento so diz QUAIS
    # animacoes usa e com que atraso (economiza ~40 bytes por segmento, o
    # que pesa quando a cobrinha passa de 200)
    css = [
        ":root{%s;--snake:%s}" % (
            ";".join(f"--l{i}:{c}" for i, c in enumerate(LIGHT)), snake_color),
        "@media(prefers-color-scheme:dark){:root{%s}}" % (
            ";".join(f"--l{i}:{c}" for i, c in enumerate(DARK))),
        ".bg{fill:var(--l0)}",
        ".eaten{opacity:.35}",   # ja comido: fica visivel (historico real), so mais apagado
        ".s{fill:var(--snake);animation-duration:%.2fs;"
        "animation-timing-function:linear;animation-iteration-count:infinite}"
        % total,
    ]
    css += [f".l{i}{{fill:var(--l{i})}}" for i in range(1, 5)]

    steps = []
    for f, (col, row) in enumerate(frames):
        x, y = _xy(col, row)
        steps.append(f"{pct(f):.4f}%{{transform:translate({x}px,{y}px)}}")
    css.append("@keyframes p{%s}" % "".join(steps))

    for f in sorted(set(eaten.values())):
        p = pct(f)
        css.append("@keyframes e%d{0%%,%.4f%%{opacity:1}%.4f%%,100%%{opacity:0}}"
                   % (f, max(p - 0.01, 0), p))
        css.append(f".e{f}{{animation:e{f} {total:.2f}s linear infinite}}")

    for k, birth in enumerate(births):
        nomes, delays = ["p"], [f"{k * step - total:.3f}s"]
        if birth > 0:
            p = pct(birth)
            css.append(
                "@keyframes b%d{0%%,%.4f%%{opacity:0}%.4f%%,100%%{opacity:1}}"
                % (k, max(p - 0.01, 0), p))
            nomes.append(f"b{k}")
            delays.append("0s")
        css.append(".s%d{animation-name:%s;animation-delay:%s}"
                   % (k, ",".join(nomes), ",".join(delays)))

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}">',
        "<style>%s</style>" % "".join(css),
    ]
    for col in range(COLS):
        for row in range(ROWS):
            x, y = _xy(col, row)
            out.append(f'<rect class="bg" x="{x}" y="{y}" width="{CELL}" '
                       f'height="{CELL}" rx="2"/>')
    for (col, row), (lv, comido) in sorted(cells.items()):
        x, y = _xy(col, row)
        cls = f"l{lv}"
        if comido:
            cls += " eaten"
        if (col, row) in eaten:
            cls += f" e{eaten[(col, row)]}"
        out.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" '
                   f'height="{CELL}" rx="2"/>')
    for k in range(max_len - 1, -1, -1):
        fade = max(0.45, 1 - 0.55 * k / max(max_len - 1, 1))
        out.append(f'<rect class="s s{k}" x="-1" y="-1" width="{CELL + 2}" '
                   f'height="{CELL + 2}" rx="3" fill-opacity="{fade:.2f}"/>')
    out.append("</svg>")
    return "".join(out)
