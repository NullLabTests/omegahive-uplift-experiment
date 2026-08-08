"""Env A: MAZE-LITE — grid navigation with partial observability.

The agent sees only a 3x3 neighborhood and must reach the goal. Each episode
is an independent navigation attempt (walls learned within the episode only);
the shared AtomSpace is not used here — maze is the planning faculty's proving
ground, while memory/estimation are exercised by repoops/selflab.

Policy (fixed core):
  1. goal visible  -> step toward it
  2. else          -> pick a frontier cell (unknown cell adjacent to the known
     free region), BFS over traversable cells, commit to it until reached.
     Baseline picks the NEAREST frontier; mechanisms may replace the frontier
     selection (attention budget caps the considered set; uncertainty planning
     re-ranks by information gain and goal bias).

Score vector: success_rate, efficiency (1 - excess-steps ratio), robustness
(min success across mazes), transfer_gain (late-maze minus early-maze success),
steps (raw).
"""

from __future__ import annotations

import random
from collections import deque

from hive.atomspace import AtomSpace
from hive.hooks import HookPipe

N_MAZES = 4
EPISODES = 5
STEP_BUDGET = 95
GRID = 9


def _neighbors(r: int, c: int):
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _in_grid(r: int, c: int) -> bool:
    return 0 <= r < GRID and 0 <= c < GRID


def _build_maze(rng: random.Random) -> tuple[set, tuple, tuple]:
    start, goal = (0, 0), (GRID - 1, GRID - 1)
    walls = set()
    for r in range(GRID):
        for c in range(GRID):
            if (r, c) == start or (r, c) == goal:
                continue
            if rng.random() < 0.30:
                walls.add((r, c))
    # carve a guaranteed corridor
    r, c = 0, 0
    while (r, c) != goal:
        if r < GRID - 1 and rng.random() < 0.55:
            r += 1
        elif c < GRID - 1:
            c += 1
        elif r > 0:
            r -= 1
        else:
            walls = {w for w in walls if False}
            return _build_maze(rng)
        walls.discard((r, c))
    return walls, start, goal


def _bfs(traversable: set, start: tuple, target) -> list | None:
    if start not in traversable:
        return None
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == target:
            path = []
            while cur is not None:
                path.append(cur)
                cur = prev[cur]
            return path[::-1]
        for nb in _neighbors(*cur):
            if nb in traversable and nb not in prev:
                prev[nb] = cur
                q.append(nb)
    return None


class MazeAgent:
    def __init__(self, walls: set, start: tuple, goal: tuple):
        self.walls = walls
        self.start = start
        self.goal = goal
        self.known_free: set = {start}
        self.known_walls: set = set()
        self.pos = start
        self.steps = 0
        self.reached = False

    def observe(self) -> dict:
        r, c = self.pos
        view = {}
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                cell = (r + dr, c + dc)
                if not _in_grid(*cell):
                    continue
                if cell == self.goal:
                    view[cell] = "goal"
                elif cell in self.walls:
                    view[cell] = "wall"
                else:
                    view[cell] = "free"
        return view

    def record_observation(self, view: dict) -> None:
        for cell, kind in view.items():
            if kind == "wall":
                self.known_walls.add(cell)
            elif kind == "free":
                self.known_free.add(cell)

    def step_toward_goal(self) -> bool:
        r, c = self.pos
        gr, gc = self.goal
        dr = 1 if gr > r else (-1 if gr < r else 0)
        dc = 1 if gc > c else (-1 if gc < c else 0)
        cands = [(r + dr, c + dc), (r + dr, c), (r, c + dc)]
        for cand in cands:
            if _in_grid(*cand) and cand not in self.walls:
                self.pos = cand
                self.known_free.add(cand)
                self.steps += 1
                return self.pos == self.goal
        return False

    def frontier(self) -> list:
        out = set()
        for cell in self.known_free:
            for nb in _neighbors(*cell):
                if not _in_grid(*nb) or nb == self.goal:
                    continue
                if nb in self.known_free or nb in self.known_walls:
                    continue
                out.add(nb)
        return sorted(out)

    def traversable(self) -> set:
        return {(r, c) for r in range(GRID) for c in range(GRID)
                if (r, c) not in self.known_walls}


class _PlanView:
    """Adapter so mechanisms see map info without MazeAgent internals."""

    def __init__(self, agent: MazeAgent):
        self.agent = agent

    def is_known(self, r: int, c: int) -> bool:
        if not _in_grid(r, c):
            return True
        cell = (r, c)
        return cell in self.agent.known_free or cell in self.agent.known_walls

    @property
    def pos(self) -> tuple:
        return self.agent.pos

    @property
    def goal(self) -> tuple:
        return self.agent.goal

    @property
    def grid(self) -> int:
        return GRID


def _run_episode(agent: MazeAgent, atomspace: AtomSpace, pipe: HookPipe, ctx: dict,
                 rng: random.Random, use_uncertainty: bool) -> bool:
    target = None
    while agent.steps < STEP_BUDGET:
        view = agent.observe()
        agent.record_observation(view)
        if agent.goal in view:
            target = None
            if agent.step_toward_goal():
                return True
            continue

        r, c = agent.pos
        if target is not None and (target in agent.known_walls
                                   or target in agent.known_free):
            target = None

        if target is None:
            frontier = agent.frontier()
            if use_uncertainty:
                ctx = pipe.choose_action(ctx, _PlanView(agent), frontier)
                ranked = ctx.get("uncertainty_planning", {}).get("ranked", [])
                ordered = [c for _, c in ranked] + [c for c in frontier
                                                    if c not in {x[1] for x in ranked}]
            else:
                # naive baseline: pick a RANDOM frontier cell
                ordered = list(frontier)
                rng.shuffle(ordered)
            for cand in ordered:
                path = _bfs(agent.traversable(), agent.pos, cand)
                if path and len(path) > 1:
                    target = cand
                    break
            if target is None:
                open_moves = [nb for nb in _neighbors(r, c)
                              if _in_grid(*nb) and nb not in agent.known_walls
                              and nb not in agent.walls]
                if not open_moves:
                    return False
                nxt = rng.choice(open_moves)
                agent.pos = nxt
                agent.known_free.add(nxt)
                agent.steps += 1
                if agent.pos == agent.goal:
                    return True
                continue

        path = _bfs(agent.traversable(), agent.pos, target)
        if path and len(path) > 1:
            nxt = path[1]
        else:
            target = None
            continue
        if nxt in agent.walls:
            agent.known_walls.add(nxt)
            target = None
            continue
        agent.pos = nxt
        agent.known_free.add(nxt)
        agent.steps += 1
        if agent.pos == agent.goal:
            return True
    return False


def run(active: list[str], atomspace: AtomSpace, pipe: HookPipe, seed: int) -> dict:
    rng = random.Random(seed)
    ctx = {m: {} for m in active}
    use_uncertainty = "uncertainty_planning" in active

    per_maze = []
    successes = []
    steps = []
    for _ in range(N_MAZES):
        walls, start, goal = _build_maze(rng)
        maze_ok = 0
        for _ep in range(EPISODES):
            agent = MazeAgent(walls, start, goal)
            ok = _run_episode(agent, atomspace, pipe, ctx, rng, use_uncertainty)
            successes.append(1 if ok else 0)
            if ok:
                maze_ok += 1
                steps.append(agent.steps)
        per_maze.append(maze_ok / EPISODES)

    success_rate = sum(successes) / (N_MAZES * EPISODES)
    avg_steps = sum(steps) / len(steps) if steps else STEP_BUDGET
    efficiency = max(0.0, min(1.0, 1.0 - (avg_steps - 16) / (STEP_BUDGET - 16)))
    robustness = min(per_maze) if per_maze else 0.0
    early = sum(per_maze[:2]) / 2
    late = sum(per_maze[2:]) / 2
    transfer_gain = max(0.0, late - early)

    return {
        "env": "maze",
        "success_rate": round(success_rate, 4),
        "efficiency": round(efficiency, 4),
        "robustness": round(robustness, 4),
        "transfer_gain": round(transfer_gain, 4),
        "steps": round(avg_steps, 1),
    }
