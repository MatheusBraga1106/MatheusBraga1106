"""Estado persistente da cobrinha: posicao, tamanho e caminho percorrido.

O corpo sao as ultimas `length` posicoes visitadas pela cabeca. A simulacao
anda um passo por vez: a cada passo ela persegue a comida alcancavel mais
proxima; se nenhuma comida tiver caminho livre agora, ela entra em modo
sobrevivencia (persegue o proprio rabo) ate abrir espaço - nunca desiste s6
por causa de um alvo especifico estar temporariamente bloqueado. So reseta
quando literalmente nao sobra nenhum movimento seguro (encurralada de
verdade) ou quando enche o tabuleiro inteiro.
"""
from collections import deque
from datetime import date, timedelta

COLS, ROWS = 53, 7
BOARD = COLS * ROWS
START_LENGTH = 3
MAX_PATH = 400  # frames guardados para a animacao


def current_anchor(today=None):
    today = today or date.today()
    sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    return sunday - timedelta(weeks=COLS - 1)


def date_to_cell(day, anchor):
    delta = (date.fromisoformat(day) - anchor).days
    return delta // 7, delta % 7


def new_state(anchor):
    """Nasce pequena e vazia: nada e excluido de vez, so limitamos quanto ela
    come por rodada (veja `max_foods` em advance). Um backlog grande e comido
    aos poucos, dia apos dia, ate zerar - nunca fica comida orfa no tabuleiro.
    """
    head = [0, 3]
    return {
        "version": 2,
        "generation": 1,
        "anchor": anchor.isoformat(),
        "length": START_LENGTH,
        "lengthAtPathStart": START_LENGTH,
        "head": head,
        "path": [list(head)],
        "events": [],
        "eaten": [],
        "totalEaten": 0,
    }


def reanchor(state, anchor):
    """O grid anda pra frente com o tempo; reposiciona o corpo ja guardado."""
    shift = (anchor - date.fromisoformat(state["anchor"])).days // 7
    if shift <= 0:
        return
    for p in state["path"]:
        p[0] = (p[0] - shift) % COLS
    for e in state["events"]:
        e["cell"][0] = (e["cell"][0] - shift) % COLS
    state["head"][0] = (state["head"][0] - shift) % COLS
    state["anchor"] = anchor.isoformat()


def _neighbors(cell):
    col, row = cell
    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c, r = col + dc, row + dr
        if 0 <= c < COLS and 0 <= r < ROWS:
            yield c, r


def _body(path, length):
    """Celulas ocupadas pelo corpo, cabeca inclusa."""
    seg = path[-length:] if length <= len(path) else path
    return {tuple(c) for c in seg}


def _bfs(start, goal, blocked):
    """Menor caminho evitando `blocked`, ou None."""
    if start == goal:
        return []
    prev = {start: None}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur == goal:
            break
        for nb in _neighbors(cur):
            if nb in prev or nb in blocked:
                continue
            prev[nb] = cur
            queue.append(nb)
    if goal not in prev:
        return None
    route, node = [], goal
    while node != start:
        route.append(node)
        node = prev[node]
    return route[::-1]


def _safe(path, length, move, grow):
    """Depois desse passo a cabeca ainda alcanca a propria cauda?"""
    new_path = [tuple(p) for p in path] + [move]
    new_len = length + (1 if grow else 0)
    if new_len <= 3:
        return True
    body = _body(new_path, new_len)
    tail = new_path[-new_len] if new_len <= len(new_path) else new_path[0]
    return _bfs(move, tail, body - {tail}) is not None


def _choose_move(path, length, target):
    """Um unico passo: persegue `target` se der um caminho seguro ate ele,
    senao persegue a propria cauda pra sobreviver. None so quando nao sobra
    nenhuma celula vizinha livre (fim de jogo de verdade).
    """
    head = tuple(path[-1])
    blocked = _body(path, length)
    options = [n for n in _neighbors(head) if n not in blocked]
    if not options:
        return None, False
    route = _bfs(head, target, blocked - {target})
    if route and _safe(path, length, route[0], grow=route[0] == target):
        return route[0], route[0] == target
    tail = tuple(path[-length]) if length <= len(path) else tuple(path[0])
    safe_opts = [n for n in options if _safe(path, length, n, grow=False)]
    pool = safe_opts or options
    best = min(pool, key=lambda n: abs(n[0] - tail[0]) + abs(n[1] - tail[1]))
    return best, False


def _restart(state):
    """Game over de verdade: renasce pequena numa celula livre."""
    body = _body(state["path"], state["length"])
    head = next(((c, r) for c in range(COLS) for r in range(ROWS)
                 if (c, r) not in body), (0, 3))
    state["generation"] += 1
    state["length"] = START_LENGTH
    state["lengthAtPathStart"] = START_LENGTH
    state["head"] = list(head)
    state["path"] = [list(head)]
    state["events"] = []


def advance(state, activity, anchor, max_foods=15, max_steps=600):
    """Anda passo a passo perseguindo a comida mais proxima alcancavel.

    Nunca desiste so porque um alvo especifico esta bloqueado no momento -
    ela sobrevive perseguindo a propria cauda ate abrir espaço. Reseta
    apenas quando fica sem nenhum movimento seguro (encurralada de verdade)
    ou quando enche o tabuleiro inteiro.
    """
    eaten = set(state["eaten"])
    food = {}
    for day, info in activity.items():
        if info["count"] <= 0 or day in eaten:
            continue
        if date.fromisoformat(day) < anchor:
            continue
        cell = date_to_cell(day, anchor)
        if 0 <= cell[0] < COLS:
            food[cell] = day

    eaten_this_round = 0
    for _ in range(max_steps):
        if eaten_this_round >= max_foods or not food:
            break
        head = tuple(state["path"][-1])
        body = _body(state["path"], state["length"])
        reachable_food = [c for c in food if c not in body]
        if not reachable_food:
            break  # toda comida restante esta sob o proprio corpo agora
        target = min(reachable_food,
                    key=lambda c: abs(c[0] - head[0]) + abs(c[1] - head[1]))

        move, grew = _choose_move(state["path"], state["length"], target)
        if move is None:
            _restart(state)  # sem saida de verdade: reseta e continua a rodada
            continue

        state["path"].append(list(move))
        if grew:
            day = food.pop(move)
            eaten.add(day)
            state["length"] += 1
            state["totalEaten"] += 1
            eaten_this_round += 1
            state["events"].append({
                "frame": len(state["path"]) - 1,
                "grow": 1,
                "date": day,
                "cell": list(move),
            })
            if state["length"] >= BOARD:
                _restart(state)  # encheu o tabuleiro inteiro

    state["eaten"] = sorted(d for d in eaten if date.fromisoformat(d) >= anchor)
    state["head"] = list(state["path"][-1])
    _trim(state)
    return state


def _trim(state):
    extra = len(state["path"]) - MAX_PATH
    if extra <= 0:
        return
    state["lengthAtPathStart"] += sum(
        e["grow"] for e in state["events"] if e["frame"] < extra
    )
    state["path"] = state["path"][extra:]
    state["events"] = [
        dict(e, frame=e["frame"] - extra)
        for e in state["events"] if e["frame"] >= extra
    ]
