"""Avanca a cobrinha e regenera o SVG. Use --demo para testar sem token."""
import argparse
import json
import os
import random
from datetime import date, timedelta

import engine
import github_data
import render


def demo_activity(anchor):
    random.seed(7)
    days = {}
    for i in range(engine.COLS * engine.ROWS):
        day = anchor + timedelta(days=i)
        if day > date.today():
            break
        if random.random() < 0.45:
            days[day.isoformat()] = {
                "count": random.randint(1, 12),
                "repos": {f"repo{j}" for j in range(random.randint(1, 3))},
            }
        else:
            days[day.isoformat()] = {"count": 0, "repos": set()}
    return days


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="MatheusBraga1106")
    ap.add_argument("--state", default="snake-state.json")
    ap.add_argument("--out", default="snake.svg")
    ap.add_argument("--color", default="#8b5cf6")
    ap.add_argument("--frame-ms", type=int, default=140)
    ap.add_argument("--backfill", type=int, default=30,
                    help="dias de historico consumidos na primeira rodada")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    anchor = engine.current_anchor()
    if os.path.exists(args.state):
        with open(args.state, encoding="utf-8") as fh:
            state = json.load(fh)
        engine.reanchor(state, anchor)
    else:
        state = engine.new_state(anchor, args.backfill)

    if args.demo:
        activity = demo_activity(anchor)
    else:
        token = os.environ.get("GH_TOKEN")
        if not token:
            raise SystemExit("defina GH_TOKEN (token classico com escopo repo)")
        activity = github_data.daily_activity(
            github_data.fetch(args.user, token))

    engine.advance(state, activity, anchor)
    svg = render.render(state, activity, anchor,
                        snake_color=args.color, frame_ms=args.frame_ms)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    with open(args.state, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)

    print(f"tamanho={state['length']} comidos={state['totalEaten']} "
          f"geracao={state['generation']} frames={len(state['path'])}")


if __name__ == "__main__":
    main()
