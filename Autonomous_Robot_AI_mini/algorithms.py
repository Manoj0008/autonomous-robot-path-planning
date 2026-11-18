
from collections import deque
import heapq


# Four possible movements
MOVES = [
    (-1, 0),  # Up
    (1, 0),   # Down
    (0, -1),  # Left
    (0, 1)    # Right
]


def get_neighbors(node, grid):

    rows = len(grid)
    cols = len(grid[0])

    neighbors = []

    r, c = node

    for dr, dc in MOVES:

        nr = r + dr
        nc = c + dc

        if (0 <= nr < rows and
            0 <= nc < cols and
            grid[nr][nc] == 0):

            neighbors.append((nr, nc))

    return neighbors


# Reconstruct the final path
def reconstruct_path(parent, start, goal):

    path = []
    current = goal

    while current is not None:

        path.append(current)
        current = parent[current]

    path.reverse()

    return path


# 1. Breadth First Search
def bfs(grid, start, goal):

    queue = deque([start])

    parent = {start: None}
    visited = {start}

    while queue:

        current = queue.popleft()

        if current == goal:

            return reconstruct_path(
                parent, start, goal
            ), len(visited)

        for neighbor in get_neighbors(current, grid):

            if neighbor not in visited:

                visited.add(neighbor)
                parent[neighbor] = current

                queue.append(neighbor)

    return [], len(visited)


# 2. Depth First Search
def dfs(grid, start, goal):

    stack = [start]

    parent = {start: None}
    visited = {start}

    while stack:

        current = stack.pop()

        if current == goal:

            return reconstruct_path(
                parent, start, goal
            ), len(visited)

        for neighbor in get_neighbors(current, grid):

            if neighbor not in visited:

                visited.add(neighbor)
                parent[neighbor] = current

                stack.append(neighbor)

    return [], len(visited)


# Manhattan distance heuristic
def heuristic(a, b):

    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# 3. A Star Search

def astar(grid, start, goal):

    priority_queue = []

    # Priority: f-score, heuristic, g-score, node
    heapq.heappush(
        priority_queue,
        (
            heuristic(start, goal),
            heuristic(start, goal),
            0,
            start
        )
    )

    parent = {start: None}
    g_score = {start: 0}
    visited = set()

    while priority_queue:

        f, h, g, current = heapq.heappop(
            priority_queue
        )

        if current in visited:
            continue

        visited.add(current)

        if current == goal:

            return reconstruct_path(
                parent, start, goal
            ), len(visited)

        for neighbor in get_neighbors(current, grid):

            new_cost = g + 1

            if new_cost < g_score.get(
                neighbor, float("inf")
            ):

                g_score[neighbor] = new_cost
                parent[neighbor] = current

                new_h = heuristic(neighbor, goal)
                new_f = new_cost + new_h

                heapq.heappush(
                    priority_queue,
                    (
                        new_f,
                        new_h,
                        new_cost,
                        neighbor
                    )
                )

    return [], len(visited)


