# -*- coding: utf-8 -*-
"""FOLD PAPER 关卡生成器 v4

规则（前端必须一致）：
  折痕在「格与格之间」；从某侧折过来 k 格，要求 2k <= 该方向边长。
  低侧折 L/U：p<k -> k-1-p（新局部坐标），p>=k -> p-k；新边长 n-k，原点平移 k
  高侧折 R/D：p>=n-k -> 2(n-k)-1-p，其余不动；新边长 n-k

二维可分解为两条一维纸条（x 只受左右折影响、y 只受上下折影响），
故 par = par_x + par_y 精确成立。
"""
from collections import deque
import json, random, sys

LO = {'L', 'U'}
HI = {'R', 'D'}


def fold1d(n, pts, side, k):
    if k < 1 or 2 * k > n:
        return None
    if side in ('L', 'U'):
        out = [k - 1 - p if p < k else p - k for p in pts]
    else:
        c = n - k
        out = [2 * c - 1 - p if p >= c else p for p in pts]
    nn = n - k
    out = tuple(sorted(set(out)))
    assert all(0 <= p < nn for p in out), (n, pts, side, k, nn, out)
    return (nn, out)


def _best_table(n, pts):
    """memo: 每个状态到单孔的最少步数。"""
    start = (n, tuple(sorted(set(pts))))
    memo = {s: 10 ** 6 for s in [start]}
    q = deque([start])
    order = []
    while q:
        st = q.popleft()
        order.append(st)
        if len(st[1]) == 1:
            memo[st] = 0
            continue
        for side in 'LR':
            for k in range(1, st[0] // 2 + 1):
                ns = fold1d(st[0], st[1], side, k)
                if ns is None:
                    continue
                if ns not in memo:
                    memo[ns] = 10 ** 6
                    q.append(ns)
    for st in reversed(order):
        if len(st[1]) == 1:
            continue
        best = 10 ** 6
        for side in 'LR':
            for k in range(1, st[0] // 2 + 1):
                ns = fold1d(st[0], st[1], side, k)
                if ns is not None and memo[ns] + 1 < best:
                    best = memo[ns] + 1
        memo[st] = best
    return memo, start


def solve1d_all(n, pts, max_paths=80):
    """返回 (par, [最优路径...])，路径元素为 (side, k)。"""
    memo, start = _best_table(n, pts)
    par = memo[start]
    if par >= 10 ** 6:
        return None, []
    paths = []
    acc = []

    def walk(st):
        if len(paths) >= max_paths:
            return
        if len(st[1]) == 1:
            paths.append(tuple(acc))
            return
        d = memo[st]
        for side in 'LR':
            for k in range(1, st[0] // 2 + 1):
                ns = fold1d(st[0], st[1], side, k)
                if ns is None or memo[ns] != d - 1:
                    continue
                acc.append((side, k))
                walk(ns)
                acc.pop()

    walk(start)
    return par, paths


def path_quality(n, pts, path):
    """越高越好：方向更多样、折痕更深、空折（没合上任何孔）更少。"""
    cur = (n, tuple(sorted(set(pts))))
    dead = 0
    depth = 0
    for side, k in path:
        nxt = fold1d(cur[0], cur[1], side, k)
        if len(nxt[1]) == len(cur[1]):
            dead += 1
        depth += k
        cur = nxt
    sides = len(set(s for s, _ in path))
    big = sum(1 for _, k in path if k >= 2)
    return (sides + big * 0.5 - dead * 1.6, depth)


_CACHE = {}


def axis(n, want, rng):
    """取一条一维轴：want==0 表示所有孔共用同一坐标（单坐标轴）。"""
    if want == 0:
        return [rng.randrange(n)], []
    key = (n, want)
    if key not in _CACHE:
        _CACHE[key] = pick1d(n, want, random.Random(1000 + n * 31 + want))
    got = _CACHE[key]
    return (got[0][:], got[1][:]) if got else None


def pick1d(n, want, rng, max_paths=60):
    cells = list(range(n))
    best = None
    for cnt in range(2, min(n, 8) + 1):
        for _ in range(700):
            pts = tuple(sorted(rng.sample(cells, cnt)))
            par, paths = solve1d_all(n, pts, max_paths)
            if par != want or not paths:
                continue
            path = max(paths, key=lambda p: path_quality(n, pts, p))
            q = path_quality(n, pts, path)
            spread = (max(pts) - min(pts)) / max(1, n - 1)
            score = q[0] + spread * 2.0
            if best is None or score > best[0]:
                best = (score, list(pts), list(path), cnt)
        if best and best[3] >= 3:
            break
    return None if best is None else (best[1], best[2])


def pair_holes(xs, ys, rng):
    xs = list(xs); ys = list(ys)
    if len(xs) < len(ys):
        xs += [rng.choice(xs) for _ in range(len(ys) - len(xs))]
    elif len(ys) < len(xs):
        ys += [rng.choice(ys) for _ in range(len(xs) - len(ys))]
    for _ in range(60):
        a = xs[:]; b = ys[:]
        rng.shuffle(a); rng.shuffle(b)
        holes = list(dict.fromkeys(zip(a, b)))
        if len(holes) == len(a):
            return sorted(holes)
    return None


def as_x(path):
    return [('L' if s in ('L', 'U') else 'R', k) for s, k in path]


def as_y(path):
    return [('U' if s in ('L', 'U') else 'D', k) for s, k in path]


def verify2d(w, h, holes, moves, par):
    hx = set(p[0] for p in holes)
    hy = set(p[1] for p in holes)
    W, H = w, h
    for side, k in moves:
        if side in 'LR':
            assert 2 * k <= W, (side, k, W)
            if side == 'L':
                hx = set(k - 1 - p if p < k else p - k for p in hx); W -= k
            else:
                c = W - k
                hx = set(2 * c - 1 - p if p >= c else p for p in hx); W -= k
        else:
            assert 2 * k <= H, (side, k, H)
            if side == 'U':
                hy = set(k - 1 - p if p < k else p - k for p in hy); H -= k
            else:
                c = H - k
                hy = set(2 * c - 1 - p if p >= c else p for p in hy); H -= k
        assert all(0 <= p < W for p in hx) and all(0 <= p < H for p in hy)
    return len(hx) == 1 and len(hy) == 1 and len(moves) == par


def show(w, h, holes):
    s = set(map(tuple, holes))
    return '\n'.join(''.join('O' if (x, y) in s else '·' for x in range(w)) for y in range(h))


# (w, h, par, 两轴都要参与?)
PLAN = [
    (3, 3, 1, 0),
    (4, 3, 1, 1),
    (4, 4, 2, 0),
    (5, 4, 2, 1),
    (5, 5, 3, 1),
    (6, 5, 3, 1),
    (6, 6, 4, 1),
    (6, 6, 4, 1),
    (7, 6, 4, 1),
    (7, 7, 5, 1),
    (8, 7, 5, 1),
    (8, 8, 5, 1),
    (8, 8, 6, 1),
    (9, 8, 6, 1),
    (9, 9, 6, 1),
    (9, 9, 7, 1),
    (9, 9, 7, 1),
    (9, 9, 8, 1),
]


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261107
    rng = random.Random(seed)
    out = []
    seen = set()
    for idx, (w, h, target, both) in enumerate(PLAN, 1):
        cand = None
        for _ in range(160):
            order = list(range(0, target + 1))
            if both:
                order = [p for p in order if 1 <= p <= target - 1]
            else:
                order = [0, target]   # 单轴变化：另一轴所有孔同坐标
            rng.shuffle(order)
            for px in order:
                py = target - px
                if both and not (px >= 1 and py >= 1):
                    continue
                ax = axis(w, px, rng)
                if ax is None: continue
                ay = axis(h, py, rng)
                if ay is None: continue
                holes = pair_holes(ax[0], ay[0], rng)
                if holes is None: continue
                if len(holes) < 4 and target > 3: continue
                # 版面铺开：不要全挤在一角
                bw = (max(p[0] for p in holes) - min(p[0] for p in holes) + 1) / w
                bh = (max(p[1] for p in holes) - min(p[1] for p in holes) + 1) / h
                if bw < 0.55 or bh < 0.55: continue
                sig = (w, h, tuple(holes))
                if sig in seen: continue
                mx, my = as_x(ax[1]), as_y(ay[1])
                moves, i, j = [], 0, 0
                while i < len(mx) or j < len(my):
                    if i < len(mx) and (j >= len(my) or rng.random() < .5):
                        moves.append(mx[i]); i += 1
                    else:
                        moves.append(my[j]); j += 1
                if not verify2d(w, h, holes, moves, target):
                    continue
                seen.add(sig)
                cand = {'w': w, 'h': h, 'holes': [list(p) for p in holes],
                        'par': target, 'path': [list(m) for m in moves],
                        'holesN': len(holes),
                        'bigfold': sum(1 for _, k in moves if k >= 2)}
                break
            if cand: break
        if not cand:
            print('!! 生成失败', idx, (w, h, target), flush=True); continue
        out.append(cand)
        print('L%-2d %dx%d par=%d 孔=%d 大折=%d  %s' % (
            idx, w, h, cand['par'], cand['holesN'], cand['bigfold'],
            ' '.join(a + str(b) for a, b in cand['path'])))
        print(show(w, h, cand['holes']))
        print()
        sys.stdout.flush()

    open('tools/levels.json', 'w').write(json.dumps(out, ensure_ascii=False, indent=0))
    print('total', len(out), 'pars', [o['par'] for o in out])


if __name__ == '__main__':
    main()
