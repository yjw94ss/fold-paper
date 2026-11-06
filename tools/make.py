# -*- coding: utf-8 -*-
import random, json
from gen_levels import build, solve, show

random.seed(20261106)

PLAN = [
    # (w, h, holes, 目标 par 下限, 目标 par 上限, 密封折线数)
    (3, 3, 2, 1, 1, 0),
    (4, 4, 2, 2, 2, 0),
    (4, 4, 3, 3, 3, 0),
    (5, 4, 3, 4, 4, 0),
    (5, 5, 3, 5, 5, 0),
    (5, 5, 4, 6, 6, 0),
    (6, 5, 4, 7, 7, 0),
    (6, 6, 4, 8, 8, 0),
    (6, 6, 5, 9, 9, 1),
    (7, 6, 4, 10, 10, 0),
    (7, 7, 5, 11, 11, 1),
    (7, 7, 6, 12, 12, 0),
    (8, 7, 5, 13, 13, 1),
    (8, 8, 6, 14, 15, 0),
    (8, 8, 6, 16, 18, 1),
]

out = []
for idx, (w, h, nh, lo, hi, nseal) in enumerate(PLAN, 1):
    found = None
    for _ in range(4000):
        cells = [(x, y) for y in range(h) for x in range(w)]
        holes = random.sample(cells, nh)
        # 让孔尽量分散一些，视觉上更好看
        st = build(w, h, holes)
        n, path = solve(st)
        if n is None or not (lo <= n <= hi):
            continue
        sealed = []
        if nseal:
            # 随机封一条折线，仍须可解且 par 不降
            for _try in range(30):
                side = random.choice('LRUD')
                k = random.randint(0, (w if side in 'LR' else h) - 1)
                s2 = {(0, 0, w, h, side)}
                n2, p2 = solve(st, frozenset(s2))
                if n2 is not None and n2 >= n:
                    sealed = [[side, k]]
                    n, path = n2, p2
                    break
        found = (w, h, holes, sealed, n, path)
        break
    if not found:
        print('!! no level for plan', idx, (w, h, nh, lo, hi))
        continue
    w, h, holes, sealed, n, path = found
    out.append({'w': w, 'h': h, 'holes': [list(p) for p in sorted(holes)],
                'seal': sealed, 'par': n, 'path': ''.join(path)})
    print('L%d %dx%d par=%d holes=%d seal=%s path=%s' % (idx, w, h, n, len(holes), sealed, ''.join(path)))
    print(show(w, h, holes))
    print()

print(json.dumps(out, ensure_ascii=False))
open('tools/levels.json', 'w').write(json.dumps(out, ensure_ascii=False, indent=0))
