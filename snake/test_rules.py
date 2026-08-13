"""Valida as regras do jogo simulando varios meses de atividade."""
import random
from datetime import timedelta

import engine


def simulate(seed, days=400, density=0.55):
    random.seed(seed)
    anchor = engine.current_anchor()
    state = engine.new_state(anchor)
    activity = {}
    for i in range(days):
        day = anchor + timedelta(days=i)
        activity[day.isoformat()] = {
            "count": random.randint(1, 12) if random.random() < density else 0,
            "repos": set(),
        }
    frames_checked = 0
    for i, day in enumerate(sorted(activity)):
        visible = {d: activity[d] for d in sorted(activity)[:i + 1]}
        engine.advance(state, visible, anchor)
        frames_checked += check(state)
    return state, frames_checked


def check(state):
    """Valida o path inteiro (pode ter sido resetado no meio da rodada)."""
    path = [tuple(p) for p in state["path"]]
    grows = {e["frame"]: e["grow"] for e in state["events"]}
    lengths, cur = [], state["lengthAtPathStart"]
    for f in range(len(path)):
        cur += grows.get(f, 0)
        lengths.append(cur)
    for f in range(1, len(path)):
        head, prev = path[f], path[f - 1]
        dist = abs(head[0] - prev[0]) + abs(head[1] - prev[1])
        assert dist == 1, f"passo invalido {prev}->{head} (dist {dist})"
        assert 0 <= head[0] < engine.COLS and 0 <= head[1] < engine.ROWS, \
            f"saiu do tabuleiro: {head}"
        length = min(lengths[f], f + 1)
        body = path[f - length + 1:f + 1]
        assert len(set(body)) == len(body), \
            f"corpo se sobrepos no frame {f} (tam {length}): {body}"
    return len(path)


if __name__ == "__main__":
    total = 0
    for seed in range(15):
        state, checked = simulate(seed)
        total += checked
        print(f"seed {seed:2d}: tamanho={state['length']:3d} "
              f"comidos={state['totalEaten']:3d} "
              f"geracoes={state['generation']} frames_ok={checked}")
    print(f"\nOK: {total} frames validados, nenhuma colisao.")
