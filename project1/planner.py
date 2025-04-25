import sys
import heapq

# movement actions and their deltas
action_moves = {
    'N': (-1, 0),
    'S': (1, 0),
    'W': (0, -1),
    'E': (0, 1),
}


def read_world(path):
    with open(path) as f:
        cols = int(f.readline().strip())
        rows = int(f.readline().strip())
        grid = [list(f.readline().rstrip('\n')) for _ in range(rows)]

    start = None
    dirty = set()
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '@':
                start = (r, c)
                grid[r][c] = '_'
            elif grid[r][c] == '*':
                dirty.add((r, c))
                grid[r][c] = '_'
    return grid, start, frozenset(dirty), rows, cols


def get_successors(state, grid, rows, cols):
    r, c, dirty = state
    # move
    for act, (dr, dc) in action_moves.items():
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != '#':
            yield act, (nr, nc, dirty)
    # vacuum
    if (r, c) in dirty:
        new_dirty = set(dirty)
        new_dirty.remove((r, c))
        yield 'V', (r, c, frozenset(new_dirty))

# dfs
def depth_first_search(start_state, grid, rows, cols): 
    stack = [(start_state, [])]
    visited = set([start_state])
    nodes_generated = 0
    nodes_expanded = 0

    while stack:
        state, path = stack.pop()
        nodes_expanded += 1
        _, _, dirty = state
        if not dirty:
            return path, nodes_generated, nodes_expanded
        # expand
        for act, nxt in get_successors(state, grid, rows, cols):
            nodes_generated += 1
            if nxt not in visited:
                visited.add(nxt)
                stack.append((nxt, path + [act]))
    # no solution found
    return None, nodes_generated, nodes_expanded

#ucs
def uniform_cost_search(start_state, grid, rows, cols):
    frontier = []  # (cost, count, state, path)
    entry_count = 0
    heapq.heappush(frontier, (0, entry_count, start_state, []))
    best_cost = {start_state: 0}
    nodes_generated = 0
    nodes_expanded = 0

    while frontier:
        cost, _, state, path = heapq.heappop(frontier)
        # if there's a better cost already, skip
        if cost > best_cost.get(state, float('inf')):
            continue
        nodes_expanded += 1
        _, _, dirty = state
        if not dirty:
            return path, nodes_generated, nodes_expanded
        for act, nxt in get_successors(state, grid, rows, cols):
            new_cost = cost + 1
            nodes_generated += 1
            if new_cost < best_cost.get(nxt, float('inf')):
                best_cost[nxt] = new_cost
                entry_count += 1
                heapq.heappush(frontier, (new_cost, entry_count, nxt, path + [act]))
    # no solution found womp womp
    return None, nodes_generated, nodes_expanded


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 planner.py [uniform-cost|depth-first] <world-file>")
        sys.exit(1)

    algo = sys.argv[1]
    world_file = sys.argv[2]
    grid, start, dirty, rows, cols = read_world(world_file)
    start_state = (start[0], start[1], dirty)

    if algo == 'depth-first':
        plan, gen, exp = depth_first_search(start_state, grid, rows, cols)
    elif algo == 'uniform-cost':
        plan, gen, exp = uniform_cost_search(start_state, grid, rows, cols)
    else:
        print("Error: algorithm must be 'uniform-cost' or 'depth-first'.")
        sys.exit(1)

    if plan is None:
        print("No plan found.")
        sys.exit(1)

    for action in plan:
        print(action)
    print(f"{gen} nodes generated")
    print(f"{exp} nodes expanded")


if __name__ == '__main__':
    main()
