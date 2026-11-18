
import random


class DynamicObstacleManager:

    def __init__(self, seed=42):
        self.rng = random.Random(seed)

    # Generate identical obstacle schedule
    # for all three algorithms
    def generate_schedule(self, grid, baseline_paths):

        candidates = set()

        # Collect cells from all initial paths
        for path in baseline_paths:

            for cell in path[1:-1]:

                row, col = cell

                if grid[row][col] == 0:
                    candidates.add(cell)

        candidates = sorted(candidates)

        if not candidates:
            return []

        count = min(
            self.rng.randint(3, 5),
            len(candidates)
        )

        selected = self.rng.sample(
            candidates, count
        )

        events = []

        for i, position in enumerate(selected):

            events.append({
                "step": 5 + (i * 6),
                "position": position,
                "activated": False
            })

        return events

    # Activate a scheduled obstacle
    def activate(self, grid, event, current):

        row, col = event["position"]

        # Never block the robot itself
        if event["position"] == current:
            event["activated"] = True
            return False

        # Never overwrite an existing obstacle
        if grid[row][col] != 0:
            event["activated"] = True
            return False

        grid[row][col] = 1

        event["activated"] = True

        return True
