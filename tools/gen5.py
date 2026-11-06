# -*- coding: utf-8 -*-
"""FOLD PAPER 关卡生成器 v5

规则（前端必须一致）：折痕在格与格之间；一侧折过来 k 格需 2k <= 边长。
  低侧 L/U: p<k -> k-1-p, p>=k -> p-k；新边长 n-k
  高侧 R/D: p>=n-k -> 2(n-k)-1-p, 其余不变；新边长 n-k

二维可分解为两条一维纸条，par = par_x + par_y（精确）。

质量约束：只接受"每一折都至少合上一对孔"的最优解，避免高 par 靠折空白边凑数。
"""
import json, random, sys

INF = 10 ** 6
MAXN = 9


def fold_mask(s, mask, side, k):
    """把长度为 s、位掩码为 mask 的纸条折一次，返回 (s', mask') 或 None。"""
    if k < 1 or 2 * k > s:
        return None
    out = 0
    if side in ('L', 'U'):
        for p in range(s):
            if mask >> p & 1:
                out |= 1 << (k - 1 - p if p < k else p - k)
    else:
        c = s - k
        for p in range(s):
            if mask >> p & 1:
                out |= 1 << (2 * c - 1 - p if p >= c else p)
    return (s - k, out)


def popcount(m):
    return bin(m).count('1')


def build_dp(smax=MAXN):
    """dp[s][mask] = 收成单孔的最少折数。"""
    dp = [{} for _ in range(smax + 1)]
    for s in range(1, smax + 1):
        for mask in range(1, 1 << s):
            if popcount(mask) == 1:
                dp[s][mask] = 0
                continue
            best = INF
            for side in 'LR':
                for k in range(1, s // 2 + 1):
                    ns, nm = fold_mask(s, mask, side, k)
                    v = dp[ns].get(nm, INF)
                    if v + 1 < best:
                        best = v + 1
            dp[s][mask] = best
    return dp


def build_free(dp, smax=MAXN):
    """free[s][mask] = 一条"每折都减少孔数"的最优路径（没有则 None）。"""
    free = [{} for _ in range(smax + 1)]
    for s in range(1, smax + 1):
        for mask in range(1, 1 << s):
            if popcount(mask) == 1:
                free[s][mask] = []
                continue
            d = dp[s][mask]
            if d >= INF:
                continue
            cands = []
            for side in 'LR':
                for k in range(1, s // 2 + 1):
                    ns, nm = fold_mask(s, mask, side, k)
                    if dp[ns].get(nm, INF) != d - 1:
                        continue
                    if popcount(nm) >= popcount(mask):
                        continue
                    sub = free[ns].get(nm)
                    if sub is None:
                        continue
                    cands.append([(side, k)] + sub)
            if not cands:
                continue
            # 偏好：方向多样、折痕更深
            def q(p):
                return (len(set(a for a, _ in p)) + sum(1 for _, k in p if k >= 2), sum(k for _, k in p))
            free[s][mask] = max(cands, key=q)
    return free


def build_pool(dp, free, smax=MAXN):
    """pool[s][par] = [(pts, path), ...]"""
    pool = [{} for _ in range(smax + 1)]
    for s in range(1, smax + 1):
        for mask in range(1, 1 << s):
            if popcount(mask) < 2:
                continue
            d = dp[s][mask]
            if d >= INF or free[s].get(mask) is None:
                continue
            pts = [i for i in range(s) if mask >> i & 1]
            pool[s].setdefault(d, []).append((pts, free[s][mask]))
    for s in range(1, smax + 1):
        for d in pool[s]:
            pool[s][d].sort(key=lambda c: (max(k for _, k in c[1]),
                                           max(c[0]) - min(c[0])), reverse=True)
    return pool


def as_x(p):
    return [('L' if a in ('L', 'U') else 'R', k) for a, k in p]


def as_y(p):
    return [('U' if a in ('L', 'U') else 'D', k) for a, k in p]


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


PLAN = [
    (3, 3, 1, 0), (4, 3, 1, 0), (4, 4, 2, 0), (5, 4, 2, 1), (5, 5, 3, 1),
    (6, 5, 3, 1), (6, 6, 4, 1), (6, 6, 4, 1), (7, 6, 4, 1), (7, 7, 5, 1),
    (7, 7, 5, 1), (8, 7, 5, 1), (8, 8, 6, 1), (8, 8, 6, 1), (9, 8, 6, 1),
    (9, 9, 7, 1), (9, 9, 7, 1), (9, 9, 8, 1),
]


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261107
    rng = random.Random(seed)
    dp = build_dp()
    free = build_free(dp)
    pool = build_pool(dp, free)
    for s in range(2, MAXN + 1):
        print('n=%d 可用 par -> 谜题数: %s' % (s, {d: len(v) for d, v in sorted(pool[s].items())}))
    sys.stdout.flush()

    out = []
    used_sig = set()
    used_axis = set()
    for idx, (w, h, target, both) in enumerate(PLAN, 1):
        cand = None
        best_score = -1
        min_holes = 2 if target <= 2 else 3
        px_range = [p for p in range(0, target + 1) if (1 <= p <= target - 1 if both else True)]
        rng.shuffle(px_range)
        for px in px_range:
            py = target - px
            axs = pool[w].get(px, []) if px > 0 else [([rng.randrange(w)], [])]
            ays = pool[h].get(py, []) if py > 0 else [([rng.randrange(h)], [])]
            if not axs or not ays:
                continue
            for ax in axs[:max(1, len(axs) // 3)]:
                for ay in ays[:max(1, len(ays) // 3)]:
                    holes = pair_holes(ax[0], ay[0], rng)
                    if holes is None:
                        continue
                    if len(holes) < min_holes:
                        continue
                    bw = bh = 1.0
                    if px > 0:
                        bw = (max(ax[0]) - min(ax[0]) + 1) / w
                    if py > 0:
                        bh = (max(ay[0]) - min(ay[0]) + 1) / h
                    if bw < 0.55 or bh < 0.55:
                        continue
                    sig = tuple(holes)
                    if sig in used_sig:
                        continue
                    mx, my = as_x(ax[1]), as_y(ay[1])
                    moves, i, j = [], 0, 0
                    while i < len(mx) or j < len(my):
                        if i < len(mx) and (j >= len(my) or rng.random() < .5):
                            moves.append(mx[i]); i += 1
                        else:
                            moves.append(my[j]); j += 1
                    if not verify2d(w, h, holes, moves, target):
                        continue
                    # 打分：孔数别太少（版面好看）、铺得开、轴谜题尽量没重复用过
                    axis_pen = (tuple(ax[0]) in used_axis) + (tuple(ay[0]) in used_axis)
                    score = (len(holes) * 1.1 + bw + bh
                             + (1.6 if len(ax[0]) == len(ay[0]) else 0)
                             - axis_pen * 1.2)
                    if score > best_score:
                        best_score = score
                        cand = {'w': w, 'h': h, 'holes': [list(p) for p in holes],
                                'par': target, 'path': [list(m) for m in moves],
                                'holesN': len(holes), '_ax': tuple(ax[0]), '_ay': tuple(ay[0])}
        if not cand:
            print('!! 生成失败', idx, (w, h, target), flush=True); continue
        used_sig.add(tuple(map(tuple, cand['holes'])))
        used_axis.add(cand['_ax']); used_axis.add(cand['_ay'])
        path = ' '.join(a + str(b) for a, b in cand['path'])
        cand.pop('_ax'); cand.pop('_ay')
        out.append(cand)
        print('L%-2d %dx%d par=%d 孔=%d  %s' % (idx, w, h, cand['par'], cand['holesN'], path), flush=True)
        print(show(w, h, cand['holes']))
        print()

    open('tools/levels.json', 'w').write(json.dumps(out, ensure_ascii=False, indent=0))
    print('total', len(out), 'pars', [o['par'] for o in out])


if __name__ == '__main__':
    main()
