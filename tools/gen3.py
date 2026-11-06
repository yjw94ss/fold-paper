# -*- coding: utf-8 -*-
"""FOLD PAPER 关卡生成器（正确版）

折叠规则（与前端完全一致）：
  折痕落在「格与格之间」；从某侧折过来 k 格，必须满足 2k <= 该方向边长。
  低侧折 L/U：折痕在 k，孔 p<k -> 2k-1-p，其余 p>=k -> p-k；新边长 n-k，原点平移 k
  高侧折 R/D：折痕在 n-k，孔 p>=n-k -> 2(n-k)-1-p，其余不动；新边长 n-k
  （以上为当前纸张局部坐标；低侧折后局部坐标 = 绝对坐标 - k）

关键性质：x 只受左右折影响，y 只受上下折影响，且合法性约束各自独立
  => 二维谜题可分解为两条一维纸条，最优步数 par = par_x + par_y（精确）
"""
from collections import deque
import json, random, sys

LO = {'L', 'U'}   # 低侧
HI = {'R', 'D'}   # 高侧


def fold1d(n, pts, side, k):
    """对长度为 n、孔位于 pts（局部坐标）的一维纸条折一次。返回 (n', pts') 或 None。"""
    if k < 1 or 2 * k > n:
        return None
    if side in LO:
        out = [k - 1 - p if p < k else p - k for p in pts]
    else:
        c = n - k
        out = [2 * c - 1 - p if p >= c else p for p in pts]
    nn = n - k
    out = tuple(sorted(set(out)))
    # 硬断言：任何孔都不许跑出纸外
    assert all(0 <= p < nn for p in out), (n, pts, side, k, nn, out)
    return (nn, out)


def solve1d(n, pts, cap=60000):
    """BFS 求把 pts 收成单孔的最少步数与路径。返回 (steps, [(side,k), ...]) 或 (None,None)。"""
    start = (n, tuple(sorted(set(pts))))
    if len(start[1]) <= 1:
        return 0, []
    parent = {start: None}
    moveof = {}
    q = deque([start])
    while q:
        st = q.popleft()
        for side in 'LRUD':          # 一维里 L/U 同义、R/D 同义，保留四个名便于输出
            for k in range(1, st[0] // 2 + 1):
                ns = fold1d(st[0], st[1], side, k)
                if ns is None or ns in parent:
                    continue
                parent[ns] = st
                moveof[ns] = (side, k)
                if len(ns[1]) == 1:
                    path = []
                    cur = ns
                    while parent[cur] is not None:
                        path.append(moveof[cur])
                        cur = parent[cur]
                    path.reverse()
                    return len(path), path
                if len(parent) > cap:
                    return None, None
                q.append(ns)
    return None, None


def apply1d(n, pts, path):
    cur = (n, tuple(sorted(set(pts))))
    for side, k in path:
        cur = fold1d(cur[0], cur[1], side, k)
        assert cur is not None
    return cur


def as_x(path):
    """一维解里的方向贴回 x 轴语义：低侧 -> L，高侧 -> R。"""
    return [('L' if s in LO else 'R', k) for s, k in path]


def as_y(path):
    """贴回 y 轴语义：低侧 -> U，高侧 -> D。"""
    return [('U' if s in LO else 'D', k) for s, k in path]


def pair_holes(xs, ys, rng):
    """把 x 集合与 y 集合配对成孔洞坐标（保证每个值至少用一次，且无重复点）。"""
    xs = list(xs); ys = list(ys)
    if len(xs) < len(ys):
        xs = xs + [rng.choice(xs) for _ in range(len(ys) - len(xs))]
    elif len(ys) < len(xs):
        ys = ys + [rng.choice(ys) for _ in range(len(xs) - len(ys))]
    for _ in range(40):
        a = xs[:]; b = ys[:]
        rng.shuffle(a); rng.shuffle(b)
        holes = list(dict.fromkeys(zip(a, b)))
        if len(holes) == len(a):
            return sorted(holes)
    return None


def verify2d(w, h, holes, moves, par):
    """独立复核：把 2D 解按坐标帧真实走一遍，确认最后只剩一个孔、且步数正确。"""
    hx = set(p[0] for p in holes)
    hy = set(p[1] for p in holes)
    W, H = w, h
    for side, k in moves:
        if side in 'LR':
            assert 2 * k <= W
            if side == 'L':
                hx = set(k - 1 - p if p < k else p - k for p in hx); W -= k
            else:
                c = W - k
                hx = set(2 * c - 1 - p if p >= c else p for p in hx); W -= k
        else:
            assert 2 * k <= H
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


# 目标：18 关，par 由 1 递增到 9；尺寸随关卡放大
PLAN = [
    (3, 3, 1), (4, 3, 1), (4, 4, 2), (5, 4, 2), (5, 5, 3), (5, 5, 3),
    (6, 5, 4), (6, 6, 4), (6, 6, 5), (7, 6, 5), (7, 6, 6), (7, 7, 6),
    (7, 7, 7), (8, 7, 7), (8, 8, 8), (8, 8, 8), (9, 8, 9), (9, 9, 9),
]


def build_pool(sizes, rng, samples=2600):
    """pool[size][cnt][par] = [(pts, path), ...]，穷举采样一维题库。"""
    pool = {}
    for n in sizes:
        pool[n] = {}
        cells = list(range(n))
        for cnt in range(2, min(n, 7) + 1):
            for _ in range(samples):
                pts = tuple(sorted(rng.sample(cells, cnt)))
                par, path = solve1d(n, pts)
                if par is None:
                    continue
                pool[n].setdefault(cnt, {}).setdefault(par, []).append((list(pts), path))
    return pool


def pick(pool, n, want, rng, prefer_big=True):
    """在长度 n 的题库里挑一个 par == want 的一维谜题。"""
    cands = []
    for cnt, bypar in pool[n].items():
        cands.extend(bypar.get(want, []))
    if not cands:
        return None
    def score(c):
        pts, path = c
        depth = sum(k for _, k in path)
        return (max(k for _, k in path), depth) if prefer_big else (depth,)
    cands.sort(key=score, reverse=True)
    top = cands[:max(1, len(cands) // 5)]
    return rng.choice(top)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261106
    rng = random.Random(seed)
    sizes = sorted(set([w for w, _, _ in PLAN] + [h for _, h, _ in PLAN]))
    print('采样题库', sizes, '...')
    sys.stdout.flush()
    pool = build_pool(sizes, rng)
    print('题库就绪：', {n: {c: len(v) for c, v in pool[n].items()} for n in sizes})
    sys.stdout.flush()

    out = []
    for idx, (w, h, target) in enumerate(PLAN, 1):
        joined = None
        for px in range(0, target + 1):
            py = target - px
            ax = pick(pool, w, px, rng) if px > 0 else ([0], [])
            if ax is None: continue
            ay = pick(pool, h, py, rng) if py > 0 else ([0], [])
            if ay is None: continue
            if not px and not py: continue
            holes = pair_holes(ax[0], ay[0], rng)
            if holes is None: continue
            mx, my = as_x(ax[1]), as_y(ay[1])
            moves, i, j = [], 0, 0
            while i < len(mx) or j < len(my):
                if i < len(mx) and (j >= len(my) or rng.random() < .5):
                    moves.append(mx[i]); i += 1
                else:
                    moves.append(my[j]); j += 1
            if not verify2d(w, h, holes, moves, target):
                continue
            joined = {'w': w, 'h': h, 'holes': [list(p) for p in holes],
                      'par': target, 'path': [list(m) for m in moves],
                      'holesN': len(holes),
                      'bigfold': sum(1 for _, k in moves if k >= 2)}
            break
        if not joined:
            print('!! 生成失败', idx, (w, h, target)); continue
        out.append(joined)
        print('L%-2d %dx%d par=%d 孔=%d 大折=%d  %s' % (
            idx, w, h, joined['par'], joined['holesN'], joined['bigfold'],
            ' '.join(a + str(b) for a, b in joined['path'])))
        print(show(w, h, joined['holes']))
        print()
        sys.stdout.flush()

    open('tools/levels3.json', 'w').write(json.dumps(out, ensure_ascii=False, indent=0))
    print('total', len(out), 'pars', [o['par'] for o in out])


if __name__ == '__main__':
    main()
