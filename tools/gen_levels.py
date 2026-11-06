# -*- coding: utf-8 -*-
"""折纸孔洞关卡生成 + 求解器

规则（与游戏内一致）：
  纸是 w×h 的格阵，某些格有孔。
  每次只能折最外侧的一条（最左/最右/最上/最下），折过来盖住相邻那一条：
    折左：第 0 列镜像到第 1 列，纸的左边界右移 1，宽度 -1
    折右 / 折上 / 折下 同理
  孔跟着镜像走，落在同一格即叠成一摞。
  目标：所有孔叠成 1 摞。

状态：(x0, y0, w, h, frozenset(holes 相对坐标))
用 BFS 求最少步数（作为三星基准 par）。
"""
from collections import deque
import random


def fold(state, side):
    x0, y0, w, h, holes = state
    if side == 'L':
        if w <= 1:
            return None
        nh = set()
        for (x, y) in holes:
            nh.add((1 if x == 0 else x - 1, y))
        return (x0 + 1, y0, w - 1, h, frozenset(nh))
    if side == 'R':
        if w <= 1:
            return None
        nh = set()
        for (x, y) in holes:
            nh.add((w - 2 if x == w - 1 else x, y))
        return (x0, y0, w - 1, h, frozenset(nh))
    if side == 'U':
        if h <= 1:
            return None
        nh = set()
        for (x, y) in holes:
            nh.add((x, 1 if y == 0 else y - 1))
        return (x0, y0 + 1, w, h - 1, frozenset(nh))
    if side == 'D':
        if h <= 1:
            return None
        nh = set()
        for (x, y) in holes:
            nh.add((x, h - 2 if y == h - 1 else y))
        return (x0, y0, w, h - 1, frozenset(nh))
    return None


def solve(state, sealed=frozenset(), limit=400000):
    """返回 (最少步数, 路径)；不可解返回 (None, None)"""
    if len(state[4]) <= 1:
        return (0, [])
    seen = {state}
    q = deque([(state, [])])
    n = 0
    while q:
        n += 1
        if n > limit:
            return (None, None)
        st, path = q.popleft()
        for side in 'LRUD':
            if (st[0], st[1], st[2], st[3], side) in sealed:
                continue
            ns = fold(st, side)
            if ns is None:
                continue
            if ns in seen:
                continue
            np = path + [side]
            if len(ns[4]) == 1:
                return (len(np), np)
            seen.add(ns)
            q.append((ns, np))
    return (None, None)


def build(w, h, holes):
    return (0, 0, w, h, frozenset((x, y) for x, y in holes))


def show(w, h, holes):
    grid = [['.' for _ in range(w)] for _ in range(h)]
    for (x, y) in holes:
        grid[y][x] = 'O'
    return '\n'.join(''.join(r) for r in grid)


if __name__ == '__main__':
    # 手工指定若干候选，验证并打印
    cands = [
        ('1', 3, 3, [(0, 1), (2, 1)]),
        ('2', 4, 4, [(0, 0), (3, 2), (3, 3)]),
        ('3', 4, 4, [(1, 0), (0, 3), (3, 3)]),
        ('4', 5, 5, [(0, 0), (4, 0), (2, 4)]),
        ('5', 5, 5, [(0, 2), (4, 2), (2, 0)]),
    ]
    for name, w, h, holes in cands:
        st = build(w, h, holes)
        n, path = solve(st)
        print('L%s %dx%d holes=%d -> par=%s path=%s' % (name, w, h, len(holes), n, ''.join(path) if path else None))
