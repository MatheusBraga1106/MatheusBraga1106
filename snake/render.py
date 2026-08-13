"""Gera o SVG animado a partir do estado da cobrinha."""
from datetime import date

from engine import BOARD, COLS, ROWS, date_to_cell

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


def render(state, activity, anchor, snake_color="#8b5cf6", frame_ms=140):
    path = state["path"]
    if len(path) < 2:
        path = path * 2
    n = len(path)
    total = n * frame_ms / 1000
    frame_dur = total / n

    grows = {e["frame"]: e["grow"] for e in state["events"]}
    lengths, cur = [], state["lengthAtPathStart"]
    for f in range(n):
        cur = min(cur + grows.get(f, 0), BOARD)
        lengths.append(cur)
    max_len = lengths[-1]

    already_eaten = set(state.get("eaten", ()))
    cells = {}
    for day, a in activity.items():
        if date.fromisoformat(day) < anchor or a["count"] <= 0:
            continue
        if day in already_eaten:
            continue  # comida ha muito tempo: nem desenha, sem precisar de animacao
        col, row = date_to_cell(day, anchor)
        if 0 <= col < COLS:
            cells[(col, row)] = _level(a["count"])
    eaten = {tuple(e["cell"]): e["frame"] for e in state["events"]}

    w = PAD * 2 + COLS * PITCH - GAP
    h = PAD * 2 + ROWS * PITCH - GAP

    css = [
        ":root{%s;--snake:%s}" % (
            ";".join(f"--l{i}:{c}" for i, c in enumerate(LIGHT)), snake_color),
        "@media(prefers-color-scheme:dark){:root{%s}}" % (
            ";".join(f"--l{i}:{c}" for i, c in enumerate(DARK))),
        ".bg{fill:var(--l0)}",
        ".s{fill:var(--snake)}",
    ]
    for i in range(1, 5):
        css.append(f".l{i}{{fill:var(--l{i})}}")

    steps = []
    for f, (col, row) in enumerate(path):
        x, y = _xy(col, row)
        steps.append(f"{f * 100 / (n - 1):.4f}%{{transform:translate({x}px,{y}px)}}")
    css.append("@keyframes p{%s}" % "".join(steps))

    for f in sorted(set(eaten.values())):
        pct = f * 100 / (n - 1)
        css.append(
            "@keyframes e%d{0%%,%.4f%%{opacity:1}%.4f%%,100%%{opacity:0}}"
            % (f, max(pct - 0.01, 0), pct))
        css.append(f".e{f}{{animation:e{f} {total:.2f}s linear infinite}}")

    for k in range(max_len):
        birth = next((f for f in range(n) if lengths[f] > k), None)
        if birth is None:
            continue
        delay = k * frame_dur - total
        anims = [f"p {total:.2f}s linear infinite"]
        delays = [f"{delay:.3f}s"]
        if birth > 0:
            pct = birth * 100 / (n - 1)
            css.append(
                "@keyframes b%d{0%%,%.4f%%{opacity:0}%.4f%%,100%%{opacity:1}}"
                % (k, max(pct - 0.01, 0), pct))
            anims.append(f"b{k} {total:.2f}s linear infinite")
            delays.append("0s")
        css.append(".s%d{animation:%s;animation-delay:%s}"
                   % (k, ",".join(anims), ",".join(delays)))

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
    for (col, row), lv in sorted(cells.items()):
        x, y = _xy(col, row)
        cls = f"l{lv}"
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
