"""Suite de testes da cobrinha.

Valida os dois lados do problema:

  * o MOTOR  - invariantes do jogo a cada passo;
  * o RENDER - o SVG e lido de volta e a animacao e reconstruida com a
    semantica real do CSS (inclusive o `mod` da duracao, que era a origem
    do corpo teleportado). E o unico jeito de provar que o que chega no
    navegador esta certo.

Rode:  py tests.py           (tudo)
       py tests.py rapido    (so o essencial, ~10s)
"""
import random
import re
import sys
from datetime import date, timedelta

import engine
import render

PITCH, PAD = render.PITCH, render.PAD


class Falha(AssertionError):
    pass


def _ok(cond, msg):
    if not cond:
        raise Falha(msg)


# ------------------------------------------------------------------ motor
def checar_estado(state, ctx=""):
    body = [tuple(c) for c in state["body"]]
    _ok(body, f"{ctx}: corpo vazio")
    _ok(len(set(body)) == len(body),
        f"{ctx}: corpo com celula repetida -> {body}")
    for c, r in body:
        _ok(0 <= c < engine.COLS and 0 <= r < engine.ROWS,
            f"{ctx}: celula fora do tabuleiro {(c, r)}")
    for a, b in zip(body, body[1:]):
        _ok(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1,
            f"{ctx}: corpo desconexo entre {a} e {b}")

    path = [tuple(c) for c in state["path"]]
    _ok(path[-1] == body[0], f"{ctx}: path[-1] != cabeca")
    _ok(path[0] == tuple(state["bodyAtPathStart"][0]),
        f"{ctx}: path[0] != cabeca do bodyAtPathStart")
    for a, b in zip(path, path[1:]):
        _ok(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1,
            f"{ctx}: salto na trilha entre {a} e {b}")
    _ok(len(path) <= engine.MAX_PATH + 1,
        f"{ctx}: trilha maior que a janela ({len(path)})")

    for ev in state["events"]:
        # frame 0 significaria um crescimento ja absorvido pelo
        # bodyAtPathStart, contado duas vezes pelo render
        _ok(ev["frame"] >= 1, f"{ctx}: evento no frame 0")
        _ok(ev["frame"] < len(path), f"{ctx}: evento fora da janela")

    for f in engine.body_frames(state):
        _ok(len(set(f)) == len(f), f"{ctx}: corpo reconstruido se sobrepoe")
    _ok(engine.body_frames(state)[-1] == body,
        f"{ctx}: reconstrucao do ultimo frame != corpo real")

    # o render precisa concordar com o motor sobre quantos segmentos existem
    quadros, prefixo = render.animation_path(state)
    nascimentos = render.segment_births(state, quadros, prefixo)
    _ok(len(nascimentos) == len(body),
        f"{ctx}: render desenharia {len(nascimentos)} segmentos, "
        f"corpo tem {len(body)}")


# ----------------------------------------------------------------- render
def ler_svg(svg):
    """Extrai da string do SVG tudo que descreve a animacao."""
    kf = re.search(r"@keyframes p\{(.*?)\}(?=@|\.)", svg, re.S)
    _ok(kf, "SVG sem @keyframes p")
    quadros = []
    for pct, x, y in re.findall(
            r"([\d.]+)%\{transform:translate\((-?[\d.]+)px,(-?[\d.]+)px\)\}",
            kf.group(1)):
        col = round((float(x) - PAD) / PITCH)
        row = round((float(y) - PAD) / PITCH)
        quadros.append((float(pct), (col, row)))

    total = float(re.search(r"animation-duration:([\d.]+)s", svg).group(1))

    nascimentos = {}
    for k, _a, b in re.findall(
            r"@keyframes b(\d+)\{0%,([\d.]+)%\{opacity:0\}([\d.]+)%,"
            r"100%\{opacity:1\}\}", svg):
        nascimentos[int(k)] = float(b)

    atrasos = {}
    for k, nomes, d in re.findall(
            r"\.s(\d+)\{animation-name:([^;]+);animation-delay:(-?[\d.]+)s",
            svg):
        atrasos[int(k)] = float(d)
        _ok(nomes.split(",")[0] == "p",
            f"segmento {k} nao usa a trilha `p`: {nomes}")
    return quadros, total, nascimentos, atrasos


def checar_svg(svg, state, ctx=""):
    quadros, total, nascimentos, atrasos = ler_svg(svg)
    n = len(quadros)
    _ok(n >= 2, f"{ctx}: animacao com menos de 2 frames")
    passo = total / (n - 1)
    celulas = [c for _, c in quadros]
    estatico = len(set(celulas)) == 1

    if not estatico:
        for a, b in zip(celulas, celulas[1:]):
            _ok(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1,
                f"{ctx}: trilha da animacao salta de {a} para {b}")

    segs = sorted(atrasos)
    _ok(segs == list(range(len(segs))), f"{ctx}: segmentos com indice furado")

    # nasce_frame vem do percentual; converte de volta pra indice de frame
    nasce = {k: int(round(p * (n - 1) / 100.0)) for k, p in nascimentos.items()}
    for k in segs:
        nasce.setdefault(k, 0)
        # INVARIANTE ANTI-TELEPORTE: o segmento k nao pode aparecer antes do
        # frame k, senao o `mod` do CSS o joga pro fim da trilha.
        _ok(nasce[k] >= k,
            f"{ctx}: segmento {k} nasce no frame {nasce[k]} (< {k}) -> "
            f"vai dar a volta pelo fim do ciclo")
        esperado_atraso = k * passo - total
        _ok(abs(atrasos[k] - esperado_atraso) < 1e-3,
            f"{ctx}: segmento {k} com atraso {atrasos[k]:.3f}s, "
            f"esperado {esperado_atraso:.3f}s")

    esperado = engine.body_frames(state)
    prefixo = n - len(state["path"])

    for F in range(n):
        # com nasce[k] >= k, todo segmento visivel tem F >= k: sem wrap.
        corpo = [celulas[F - k] for k in segs if F >= nasce[k]]

        _ok(len(set(corpo)) == len(corpo),
            f"{ctx}: frame {F} desenha duas partes na mesma celula -> {corpo}")
        if not estatico:
            for a, b in zip(corpo, corpo[1:]):
                _ok(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1,
                    f"{ctx}: frame {F} com corpo desconexo entre {a} e {b}")
        for c, r in corpo:
            _ok(0 <= c < engine.COLS and 0 <= r < engine.ROWS,
                f"{ctx}: frame {F} desenha fora do tabuleiro")

        if F >= prefixo:                      # aqui ja e o corpo de verdade
            _ok(corpo == esperado[F - prefixo],
                f"{ctx}: frame {F} nao bate com o corpo do motor\n"
                f"  svg={corpo}\n  motor={esperado[F - prefixo]}")
    return n, len(segs), 0


# ------------------------------------------------------------- simulacao
def gerar_atividade(inicio, dias, densidade, seed):
    rnd = random.Random(seed)
    ativ = {}
    for i in range(dias):
        d = inicio + timedelta(days=i)
        ativ[d.isoformat()] = {
            "count": rnd.randint(1, 15) if rnd.random() < densidade else 0,
            "repos": set(),
        }
    return ativ


def simular(dias, densidade, seed, checar_cada=0, render_cada=0, max_foods=15):
    """Emula `dias` de calendario real, um `advance` por dia."""
    hoje0 = date(2026, 1, 4)
    ativ = gerar_atividade(engine.current_anchor(hoje0) - timedelta(days=400),
                           dias + 400, densidade, seed)
    anchor = engine.current_anchor(hoje0)
    state = engine.new_state(anchor)

    stats = {"svgs": 0, "maior": 0, "geracoes": 0, "frames_svg": 0}
    for d in range(dias):
        hoje = hoje0 + timedelta(days=d)
        anchor = engine.current_anchor(hoje)
        engine.reanchor(state, anchor)
        visivel = {k: v for k, v in ativ.items()
                   if anchor <= date.fromisoformat(k) <= hoje}
        engine.advance(state, visivel, anchor, max_foods=max_foods)

        stats["maior"] = max(stats["maior"], len(state["body"]))
        if checar_cada and d % checar_cada == 0:
            checar_estado(state, f"seed{seed} dia{d}")
        if render_cada and d % render_cada == 0:
            svg = render.render(state, visivel, anchor)
            nf, ns, _ = checar_svg(svg, state, f"seed{seed} dia{d}")
            stats["svgs"] += 1
            stats["frames_svg"] = max(stats["frames_svg"], nf)
    stats["geracoes"] = state["generation"]
    stats["final"] = len(state["body"])
    stats["comidos"] = state["totalEaten"]
    return state, stats


# --------------------------------------------------------------- casos de erro
ANCHOR = engine.current_anchor(date(2026, 1, 4))


def _dia_da_celula(alvo, anchor):
    for i in range(371):
        d = anchor + timedelta(days=i)
        if engine.date_to_cell(d.isoformat(), anchor) == alvo:
            return d.isoformat()
    return None


def caso_atividade_vazia():
    st = engine.new_state(ANCHOR)
    engine.advance(st, {}, ANCHOR)
    checar_estado(st, "vazia")
    checar_svg(render.render(st, {}, ANCHOR), st, "vazia")


def caso_tudo_zero():
    ativ = {(ANCHOR + timedelta(days=i)).isoformat():
            {"count": 0, "repos": set()} for i in range(371)}
    st = engine.new_state(ANCHOR)
    engine.advance(st, ativ, ANCHOR)
    _ok(st["totalEaten"] == 0, "comeu sem comida")
    checar_svg(render.render(st, ativ, ANCHOR), st, "zero")


def caso_comida_fora_da_janela():
    ativ = {(ANCHOR - timedelta(days=5)).isoformat():
            {"count": 9, "repos": set()}}
    st = engine.new_state(ANCHOR)
    engine.advance(st, ativ, ANCHOR)
    _ok(st["totalEaten"] == 0, "comeu comida anterior ao anchor")


def caso_comida_sob_o_corpo():
    st = engine.new_state(ANCHOR)
    cauda = tuple(st["body"][-1])
    ativ = {_dia_da_celula(cauda, ANCHOR): {"count": 5, "repos": set()}}
    antes = len(st["body"])
    engine.advance(st, ativ, ANCHOR, max_steps=50)
    checar_estado(st, "sob o corpo")
    _ok(len(st["body"]) >= antes, "encolheu")


def caso_tabuleiro_lotado():
    st = engine.new_state(ANCHOR)
    serpentina = []
    for col in range(engine.COLS):
        linhas = (range(engine.ROWS) if col % 2 == 0
                  else reversed(range(engine.ROWS)))
        serpentina += [(col, r) for r in linhas]
    corpo = serpentina[:engine.BOARD - 1][::-1]
    st["body"] = [list(c) for c in corpo]
    st["path"] = [list(corpo[0])]
    st["bodyAtPathStart"] = [list(c) for c in corpo]
    st["events"] = []
    livre = ({(c, r) for c in range(engine.COLS) for r in range(engine.ROWS)}
             - set(corpo))
    ativ = {_dia_da_celula(next(iter(livre)), ANCHOR):
            {"count": 3, "repos": set()}}
    engine.advance(st, ativ, ANCHOR, max_steps=20)
    checar_estado(st, "lotado")
    _ok(st["generation"] >= 2, "nao renasceu ao encher o tabuleiro")


def caso_migracao_v2_quebrado():
    velho = {
        "version": 2, "generation": 4, "anchor": ANCHOR.isoformat(),
        "length": 8,
        "path": [[0, 0], [1, 0], [2, 0], [2, 1], [1, 1], [0, 1],
                 [0, 0], [1, 0]],            # trilha que volta em si mesma
        "events": [], "eaten": ["2026-01-01"], "totalEaten": 21,
    }
    novo = engine.migrate(velho, ANCHOR)
    checar_estado(novo, "migracao")
    _ok(novo["totalEaten"] == 21, "perdeu o placar na migracao")
    _ok(novo["generation"] == 4, "perdeu a geracao na migracao")


def caso_corte_da_janela():
    st = engine.new_state(ANCHOR)
    ativ = gerar_atividade(ANCHOR, 371, 0.9, 99)
    for _ in range(60):
        engine.advance(st, ativ, ANCHOR, max_foods=8)
        checar_estado(st, "corte")
    _ok(len(st["path"]) <= engine.MAX_PATH + 1, "janela nao foi cortada")
    checar_svg(render.render(st, ativ, ANCHOR), st, "corte")


def caso_evento_na_borda_do_corte():
    """Comida engolida exatamente no frame em que a janela e cortada.

    Esse crescimento ja entra no bodyAtPathStart; se o evento tambem for
    mantido, o render conta duas vezes e desenha um segmento fantasma.
    """
    serpentina = []
    for col in range(engine.COLS):
        linhas = (range(engine.ROWS) if col % 2 == 0
                  else reversed(range(engine.ROWS)))
        serpentina += [(col, r) for r in linhas]
    trilha = serpentina[:engine.MAX_PATH + 1]

    st = engine.new_state(ANCHOR)
    st["path"] = [list(c) for c in trilha]
    st["bodyAtPathStart"] = [list(trilha[0])]
    st["events"] = [
        {"frame": 1, "cell": list(trilha[1]), "date": "2026-01-01"},
        {"frame": 2, "cell": list(trilha[2]), "date": "2026-01-02"},
    ]
    st["body"] = [list(c) for c in reversed(trilha[-3:])]

    engine._trim(st)
    checar_estado(st, "borda do corte")
    _ok(len(st["body"]) == 3, f"corpo virou {len(st['body'])}, esperado 3")
    checar_svg(render.render(st, {}, ANCHOR), st, "borda do corte")


def caso_reanchor():
    st = engine.new_state(ANCHOR)
    ativ = gerar_atividade(ANCHOR, 371, 0.6, 5)
    engine.advance(st, ativ, ANCHOR, max_foods=20)
    for semanas in range(1, 30):
        engine.reanchor(st, ANCHOR + timedelta(weeks=semanas))
        checar_estado(st, f"reanchor+{semanas}")


def caso_uma_celula():
    st = engine.new_state(ANCHOR)
    st["body"] = [[10, 3]]
    st["path"] = [[10, 3]]
    st["bodyAtPathStart"] = [[10, 3]]
    checar_svg(render.render(st, {}, ANCHOR), st, "1 celula")


def casos_de_erro():
    return [
        ("atividade vazia", caso_atividade_vazia),
        ("todos os dias com zero commits", caso_tudo_zero),
        ("comida anterior ao grid e ignorada", caso_comida_fora_da_janela),
        ("comida embaixo do corpo nao vira alvo", caso_comida_sob_o_corpo),
        ("tabuleiro lotado renasce", caso_tabuleiro_lotado),
        ("migracao de estado v2 quebrado", caso_migracao_v2_quebrado),
        ("corte da janela preserva o corpo", caso_corte_da_janela),
        ("comida exatamente na borda do corte", caso_evento_na_borda_do_corte),
        ("reanchor desliza o grid", caso_reanchor),
        ("cobrinha de 1 celula ainda renderiza", caso_uma_celula),
    ]


# ------------------------------------------------------------------- runner
def main():
    rapido = len(sys.argv) > 1 and sys.argv[1] == "rapido"
    falhas = 0

    print("== casos de erro ==")
    for nome, fn in casos_de_erro():
        try:
            fn()
            print(f"  ok   {nome}")
        except Falha as e:
            falhas += 1
            print(f"  FALHA {nome}: {e}")

    print("\n== emulando commits (motor + svg validados) ==")
    cenarios = [(180, 0.8, 1), (180, 0.35, 2)] if rapido else [
        (365, 0.9, 1),    # um ano quase todo dia commitando
        (365, 0.6, 2),
        (365, 0.25, 3),   # poucos commits
        (730, 0.75, 4),   # dois anos
        (1095, 0.5, 5),   # tres anos
    ]
    for dias, dens, seed in cenarios:
        try:
            st, s = simular(dias, dens, seed, checar_cada=1,
                            render_cada=15 if not rapido else 30)
            print(f"  ok   {dias:4d} dias dens={dens:.2f} -> "
                  f"tamanho={s['final']:3d} pico={s['maior']:3d} "
                  f"comidos={s['comidos']:4d} geracoes={s['geracoes']:2d} "
                  f"svgs_validados={s['svgs']:3d} frames={s['frames_svg']}")
        except Falha as e:
            falhas += 1
            print(f"  FALHA {dias} dias seed{seed}: {e}")

    if not rapido:
        print("\n== estresse: backlog gigante de uma vez ==")
        for max_foods in (15, 60, 200):
            try:
                st, s = simular(90, 0.95, 7, checar_cada=1, render_cada=10,
                                max_foods=max_foods)
                print(f"  ok   max_foods={max_foods:3d} -> tamanho={s['final']:3d} "
                      f"pico={s['maior']:3d} geracoes={s['geracoes']:2d}")
            except Falha as e:
                falhas += 1
                print(f"  FALHA max_foods={max_foods}: {e}")

    print()
    if falhas:
        print(f"{falhas} FALHA(S)")
        return 1
    print("tudo passou")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
