# -*- coding: utf-8 -*-
"""整片折叠：折痕任意，折叠部分 <= 保留部分。BFS + 父指针回溯。"""
from collections import deque
import json, random, sys

SIDES = 'LRUD'

def fold(state, side, k):
    x0, y0, w, h, holes = state
    if side == 'L':
        if 2 * k > w: return None
        c = x0 + k
        nh = [(2 * c - 1 - x, y) if x < c else (x - k, y) for (x, y) in holes]
        return (x0 + k, y0, w - k, h, tuple(sorted(set(nh))))
    if side == 'R':
        if 2 * k > w: return None
        c = x0 + w - k
        nh = [(2 * c - x, y) if x >= c else (x, y) for (x, y) in holes]
        return (x0, y0, w - k, h, tuple(sorted(set(nh))))
    if side == 'U':
        if 2 * k > h: return None
        c = y0 + k
        nh = [(x, 2 * c - 1 - y) if y < c else (x, y - k) for (x, y) in holes]
        return (x0, y0 + k, w, h - k, tuple(sorted(set(nh))))
    if side == 'D':
        if 2 * k > h: return None
        c = y0 + h - k
        nh = [(x, 2 * c - y) if y >= c else (x, y) for (x, y) in holes]
        return (x0, y0, w, h - k, tuple(sorted(set(nh))))
    return None


def solve(state, cap=200000):
    if len(state[4]) <= 1:
        return (0, [])
    parent = {state: None}
    moveof = {}
    q = deque([state])
    while q:
        st = q.popleft()
        for side in SIDES:
            size = st[2] if side in 'LR' else st[3]
            for k in range(1, size // 2 + 1):
                ns = fold(st, side, k)
                if ns is None or ns in parent:
                    continue
                parent[ns] = st
                moveof[ns] = (side, k)
                if len(ns[4]) == 1:
                    path = []
                    cur = ns
                    while parent[cur] is not None:
                        path.append(moveof[cur])
                        cur = parent[cur]
                    path.reverse()
                    return (len(path), path)
                if len(parent) > cap:
                    return (None, None)
                q.append(ns)
    return (None, None)


def build(w, h, holes):
    return (0, 0, w, h, tuple(sorted((x, y) for x, y in holes)))


def show(w, h, holes):
    g = [['.' for _ in range(w)] for _ in range(h)]
    for (x, y) in holes: g[y][x] = 'O'
    return '\n'.join(''.join(r) for r in g)


if __name__ == '__main__':
    random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 20261106)
    PLAN = [
        (3, 3, 2, 1, 1), (4, 4, 2, 2, 2), (4, 4, 3, 2, 2),
        (5, 4, 3, 3, 3), (5, 5, 3, 3, 3), (5, 5, 4, 3, 3),
        (6, 5, 4, 3, 3), (6, 6, 4, 4, 4), (6, 6, 5, 4, 4),
        (7, 6, 4, 4, 4), (7, 7, 5, 4, 4), (7, 7, 6, 5, 5),
        (7, 7, 6, 6, 6), (7, 7, 7, 6, 7), (7, 7, 7, 8, 9),
    ]
    out = []
    for idx, (w, h, nh, lo, hi) in enumerate(PLAN, 1):
        cells = [(x, y) for y in range(h) for x in range(w)]
        found = None
        for attempt in range(6000):
            holes = random.sample(cells, nh)
            n, path = solve(build(w, h, holes))
            if n is not None and lo <= n <= hi:
                found = (holes, n, path); break
        if not found:
            print('!! none', idx, (w, h, nh, lo, hi)); continue
        holes, n, path = found
        out.append({'w': w, 'h': h, 'holes': [list(p) for p in sorted(holes)],
                    'par': n, 'path': [list(p) for p in path]})
        print('L%-2d %dx%d par=%d holes=%d  %s' % (idx, w, h, n, len(holes), ' '.join(a+str(b) for a,b in path)))
        print(show(w, h, holes)); print()
        sys.stdout.flush()
    open('tools/levels2.json','w').write(json.dumps(out, ensure_ascii=False, indent=0))
    print('total', len(out), 'pars', [o['par'] for o in out])
