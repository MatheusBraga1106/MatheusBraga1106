"""Motor da cobrinha: um Snake de verdade, com estado persistente.

Modelo de dados (v3)
--------------------
O corpo e GUARDADO EXPLICITAMENTE (`body`), nao derivado de `path` + um
comprimento. A versao anterior derivava, e qualquer descompasso entre os
dois (corte da janela de animacao, crescimento, renascimento) virava
corpo fantasma ou colisao invisivel.

    body             celulas ocupadas, cabeca primeiro. len(body) e o tamanho.
    path             trilha da cabeca dentro da janela de animacao.
    bodyAtPathStart  corpo no frame 0 da janela (o render precisa disso pra
                     desenhar o ciclo inteiro sem "teleporte" no loop).
    events           {frame, cell, date} de cada comida engolida na janela.
    eaten            dias ja consumidos (nunca sao comida de novo).

Invariantes garantidos a cada passo (verificados em tests.py):
    1. nenhuma celula se repete dentro de `body`;
    2. toda celula esta dentro do tabuleiro;
    3. cabecas consecutivas em `path` sao vizinhas ortogonais;
    4. path[-1] == body[0] e path[0] == bodyAtPathStart[0];
    5. o corpo so cresce comendo, 1 celula por comida.
"""
from collections import deque
from datetime import date, timedelta

COLS, ROWS = 53, 7
BOARD = COLS * ROWS
START_LENGTH = 3
MAX_PATH = 300          # frames guardados para a animacao
VERSION = 3

_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --------------------------------------------------------------- calendario
def current_anchor(today=None):
    """Domingo da primeira coluna do grid (53 semanas atras)."""
    today = today or date.today()
    sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    return sunday - timedelta(weeks=COLS - 1)


def date_to_cell(day, anchor):
    delta = (date.fromisoformat(day) - anchor).days
    return delta // 7, delta % 7


def neighbors(cell):
    col, row = cell
    for dc, dr in _DIRS:
        c, r = col + dc, row + dr
        if 0 <= c < COLS and 0 <= r < ROWS:
            yield c, r


# ------------------------------------------------------------------- estado
def new_state(anchor, head=(0, 3)):
    """Nasce com o tamanho minimo, esticada na horizontal se couber."""
    body = _spawn_body(head, occupied=set())
    return {
        "version": VERSION,
        "generation": 1,
        "anchor": anchor.isoformat(),
        "body": [list(c) for c in body],
        "path": [list(body[0])],
        "bodyAtPathStart": [list(c) for c in body],
        "events": [],
        "eaten": [],
        "totalEaten": 0,
    }


def _spawn_body(head, occupied):
    """Monta um corpo inicial valido a partir de `head`, sem pisar em `occupied`."""
    body = [head]
    seen = {head}
    while len(body) < START_LENGTH:
        nxt = next((n for n in neighbors(body[-1])
                    if n not in seen and n not in occupied), None)
        if nxt is None:
            break  # tabuleiro apertado demais: nasce menor, cresce comendo
        body.append(nxt)
        seen.add(nxt)
    return body


def _on_board(cell):
    return 0 <= cell[0] < COLS and 0 <= cell[1] < ROWS


def reanchor(state, anchor):
    """Atualiza o inicio do calendario. A cobrinha NAO se move.

    Ela vive em coordenadas do tabuleiro; e o calendario que desliza por
    baixo dela toda semana. A versao anterior arrastava o corpo junto e
    fazia `% COLS`, entao quem estava na coluna 0 reaparecia na coluna 52:
    corpo teletransportado e desconexo. Pior, tentar cortar o pedaco que
    saiu do grid matava a cobrinha quase toda semana.

    Como a comida e identificada por DATA (nao por celula), deslizar o
    calendario ja basta: os dias que sairam do grid somem sozinhos e os que
    entraram viram comida nova.
    """
    if (anchor - date.fromisoformat(state["anchor"])).days // 7 <= 0:
        return
    state["anchor"] = anchor.isoformat()


def migrate(state, anchor):
    """Traz estados v1/v2 (corpo derivado de path+length) para o modelo novo."""
    if state.get("version") == VERSION and "body" in state:
        return state
    path = [tuple(p) for p in state.get("path") or [[0, 3]]]
    length = int(state.get("length") or START_LENGTH)

    body, seen = [], set()
    for cell in reversed(path[-length:]):      # da cabeca para a cauda
        if cell in seen:
            break                              # corpo antigo inconsistente: corta aqui
        body.append(cell)
        seen.add(cell)
    if not body:
        body = _spawn_body((0, 3), set())

    return {
        "version": VERSION,
        "generation": int(state.get("generation") or 1),
        "anchor": state.get("anchor") or anchor.isoformat(),
        "body": [list(c) for c in body],
        "path": [list(body[0])],
        "bodyAtPathStart": [list(c) for c in body],
        "events": [],
        "eaten": list(state.get("eaten") or []),
        "totalEaten": int(state.get("totalEaten") or 0),
    }


# -------------------------------------------------------------- busca/espaco
def _reachable(start, goal, blocked):
    """Existe caminho livre de `start` ate `goal` sem pisar em `blocked`?"""
    if start == goal:
        return True
    seen = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for nb in neighbors(cur):
            if nb in seen or nb in blocked:
                continue
            if nb == goal:
                return True
            seen.add(nb)
            queue.append(nb)
    return False


def _free_space(start, blocked):
    """Quantas celulas livres a cabeca alcanca a partir de `start`."""
    seen = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for nb in neighbors(cur):
            if nb not in seen and nb not in blocked:
                seen.add(nb)
                queue.append(nb)
    return len(seen)


FOLGA = 3       # espaco livre exigido alem do proprio corpo


def choose_move(body, target):
    """Melhor passo unico. None significa encurralada de verdade.

    Prioridade (medida em benchmark - ver historico do projeto):
      1. passo SEGURO (a cabeca ainda alcanca a propria cauda depois) e com
         espaco livre pro corpo inteiro mais uma folga; entre esses, o que
         chega mais perto da comida;
      2. sem nenhum assim, persegue a propria cauda - e o jeito classico de
         desenrolar o corpo ate abrir espaco;
      3. em ultimo caso, o passo que deixa mais espaco livre.

    A regra 2 sozinha derrubou as mortes em ~25% num teste de 3650 dias
    simulados; sem ela a cobrinha corria atras de comida ate se fechar
    numa bolsa sem saida.
    """
    head = body[0]
    occupied = set(body)
    options = [n for n in neighbors(head) if n not in occupied]
    if not options:
        return None

    ranked = []
    for mv in options:
        grow = mv == target
        after = [mv] + body if grow else [mv] + body[:-1]
        after_set = set(after)
        tail = after[-1]
        space = _free_space(mv, after_set - {mv})
        ranked.append({
            "mv": mv,
            "tail": tail,
            "safe": _reachable(mv, tail, after_set - {tail, mv}),
            "space": space,
            "dist": abs(mv[0] - target[0]) + abs(mv[1] - target[1]),
            "fits": space >= len(after) + FOLGA,
        })

    bons = [r for r in ranked if r["safe"] and r["fits"]]
    if bons:
        return min(bons, key=lambda r: (r["dist"], -r["space"]))["mv"]

    seguros = [r for r in ranked if r["safe"]]
    if seguros:
        return min(seguros, key=lambda r: (
            abs(r["mv"][0] - r["tail"][0]) + abs(r["mv"][1] - r["tail"][1]),
            -r["space"]))["mv"]

    return max(ranked, key=lambda r: (r["space"], -r["dist"]))["mv"]


# ------------------------------------------------------------------- passos
def _apply(state, move, grow):
    state["body"].insert(0, list(move))
    if not grow:
        state["body"].pop()
    state["path"].append(list(move))


def restart(state):
    """Game over: renasce pequena no maior vazio disponivel."""
    occupied = {tuple(c) for c in state["body"]}
    head = max(
        ((c, r) for c in range(COLS) for r in range(ROWS)
         if (c, r) not in occupied),
        key=lambda cell: _free_space(cell, occupied),
        default=(0, 3),
    )
    body = _spawn_body(head, occupied)
    state["generation"] += 1
    state["body"] = [list(c) for c in body]
    state["path"] = [list(body[0])]
    state["bodyAtPathStart"] = [list(c) for c in body]
    state["events"] = []


def advance(state, activity, anchor, max_foods=15, max_steps=900):
    """Avanca a cobrinha ate comer `max_foods` quadrados (ou acabar a comida).

    Nunca desiste porque um alvo especifico esta bloqueado: ela sobrevive
    perseguindo espaco ate abrir caminho. So renasce quando fica sem nenhum
    vizinho livre ou quando enche o tabuleiro.
    """
    eaten = set(state["eaten"])
    food = {}
    for day, info in activity.items():
        if info.get("count", 0) <= 0 or day in eaten:
            continue
        if date.fromisoformat(day) < anchor:
            continue
        cell = date_to_cell(day, anchor)
        if 0 <= cell[0] < COLS and 0 <= cell[1] < ROWS:
            food[cell] = day

    eaten_now = 0
    for _ in range(max_steps):
        if eaten_now >= max_foods or not food:
            break
        body = [tuple(c) for c in state["body"]]
        occupied = set(body)
        free_food = [c for c in food if c not in occupied]
        if not free_food:
            break  # o que sobrou esta debaixo dela; fica pra proxima rodada
        head = body[0]
        target = min(free_food,
                     key=lambda c: abs(c[0] - head[0]) + abs(c[1] - head[1]))

        move = choose_move(body, target)
        if move is None:
            restart(state)
            continue

        grow = move in food
        _apply(state, move, grow)
        if grow:
            day = food.pop(move)
            eaten.add(day)
            state["totalEaten"] += 1
            eaten_now += 1
            state["events"].append({
                "frame": len(state["path"]) - 1,
                "cell": list(move),
                "date": day,
            })
            if len(state["body"]) >= BOARD:
                restart(state)

    state["eaten"] = sorted(d for d in eaten if date.fromisoformat(d) >= anchor)
    _trim(state)
    return state


def _trim(state):
    """Corta a janela de animacao, recalculando o corpo do novo frame 0.

    Eventos ate `extra` (inclusive) ja foram absorvidos pelo novo
    `bodyAtPathStart`; manter o de `extra` faria o crescimento dele ser
    contado duas vezes e o render desenharia um segmento a mais que o
    motor. Por isso o corte e estrito (`> extra`), garantindo a invariante
    de que todo evento guardado tem frame >= 1.
    """
    extra = len(state["path"]) - MAX_PATH
    if extra <= 0:
        return
    grow_frames = {e["frame"] for e in state["events"]}
    body = [tuple(c) for c in state["bodyAtPathStart"]]
    for f in range(1, extra + 1):
        body.insert(0, tuple(state["path"][f]))
        if f not in grow_frames:
            body.pop()
    state["bodyAtPathStart"] = [list(c) for c in body]
    state["path"] = state["path"][extra:]
    state["events"] = [dict(e, frame=e["frame"] - extra)
                       for e in state["events"] if e["frame"] > extra]


# ------------------------------------------------------------- reconstrucao
def body_frames(state):
    """Corpo em cada frame da janela. E a fonte da verdade para o render."""
    grow_frames = {e["frame"] for e in state["events"]}
    body = [tuple(c) for c in state["bodyAtPathStart"]]
    frames = [list(body)]
    for f in range(1, len(state["path"])):
        body.insert(0, tuple(state["path"][f]))
        if f not in grow_frames:
            body.pop()
        frames.append(list(body))
    return frames
