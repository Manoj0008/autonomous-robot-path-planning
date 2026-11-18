
import copy
import csv
import os
import time
import statistics
import matplotlib.pyplot as plt

from environment import Environment
from algorithms import bfs, dfs, astar
from dynamic_obstacles import DynamicObstacleManager
from robot import Robot


# ==========================================
# BENCHMARK CONFIGURATION
# ==========================================

TOTAL_SCENARIOS = 30

ALGORITHMS = [
    ("BFS", bfs),
    ("DFS", dfs),
    ("A*", astar)
]

os.makedirs("results", exist_ok=True)


# ==========================================
# RUN ONE ALGORITHM IN ONE ENVIRONMENT
# ==========================================

def run_experiment(base_grid, start, goal,
                   algorithm, schedule):

    grid = copy.deepcopy(base_grid)

    events = copy.deepcopy(schedule)

    robot = Robot(start)

    total_nodes = 0
    total_search_time = 0.0

    replanning_count = 0
    activated_obstacles = 0
    blocked_obstacles = 0

    # Initial path search
    search_start = time.perf_counter()

    path, explored = algorithm(
        grid,
        robot.get_position(),
        goal
    )

    total_search_time += (
        time.perf_counter() - search_start
    )

    total_nodes += explored

    if not path:
        return {
            "success": False,
            "movements": 0,
            "nodes": total_nodes,
            "time": total_search_time,
            "replans": 0,
            "obstacles": 0,
            "blocked": 0
        }

    robot.set_path(path)

    success = True

    # Navigation loop
    while not robot.reached_goal(goal):

        # ----------------------------------
        # ACTIVATE SCHEDULED OBSTACLES
        # ----------------------------------

        for event in events:

            if event["activated"]:
                continue

            if robot.get_movements() < event["step"]:
                continue

            position = event["position"]

            row, col = position

            # Never block robot's current position
            if position == robot.get_position():

                event["activated"] = True
                continue

            # Never place an obstacle behind robot
            if position in robot.visited_cells:

                event["activated"] = True
                continue

            # Avoid overwriting existing obstacles
            if grid[row][col] == 1:

                event["activated"] = True
                continue

            # Add dynamic obstacle
            grid[row][col] = 1

            event["activated"] = True

            activated_obstacles += 1

            # Check if the remaining path is blocked
            remaining_path = robot.get_remaining_path()

            if position in remaining_path:

                blocked_obstacles += 1
                replanning_count += 1

                # Recalculate route from current position
                replan_start = time.perf_counter()

                new_path, new_nodes = algorithm(
                    grid,
                    robot.get_position(),
                    goal
                )

                total_search_time += (
                    time.perf_counter() - replan_start
                )

                total_nodes += new_nodes

                if new_path:

                    robot.set_path(new_path)

                else:

                    success = False
                    break

        if not success:
            break

        # ----------------------------------
        # ROBOT MOVEMENT
        # ----------------------------------

        next_position = robot.get_remaining_path()

        if not next_position:
            success = False
            break

        next_row, next_col = next_position[0]

        # Safety check
        if grid[next_row][next_col] == 1:

            replanning_count += 1

            replan_start = time.perf_counter()

            new_path, new_nodes = algorithm(
                grid,
                robot.get_position(),
                goal
            )

            total_search_time += (
                time.perf_counter() - replan_start
            )

            total_nodes += new_nodes

            if new_path:

                robot.set_path(new_path)

            else:

                success = False
                break

        else:

            robot.move_next()

    return {
        "success": success and robot.reached_goal(goal),
        "movements": robot.get_movements(),
        "nodes": total_nodes,
        "time": total_search_time,
        "replans": replanning_count,
        "obstacles": activated_obstacles,
        "blocked": blocked_obstacles
    }


# ==========================================
# GENERATE ONE SHARED SCENARIO
# ==========================================

def create_scenario(base_grid, start, goal, seed):

    baseline_paths = []

    for name, algorithm in ALGORITHMS:

        path, explored = algorithm(
            copy.deepcopy(base_grid),
            start,
            goal
        )

        baseline_paths.append(path)

    manager = DynamicObstacleManager(seed=seed)

    schedule = manager.generate_schedule(
        base_grid,
        baseline_paths
    )

    return schedule


# ==========================================
# STATISTICAL SUMMARY
# ==========================================

def calculate_summary(all_results):

    summary = []

    for name, algorithm in ALGORITHMS:

        rows = [
            result for result in all_results
            if result["algorithm"] == name
        ]

        successful = [
            row for row in rows
            if row["success"]
        ]

        success_rate = (
            len(successful) / len(rows) * 100
            if rows else 0
        )

        def average(key):

            values = [row[key] for row in rows]

            return statistics.mean(values) if values else 0

        summary.append({

            "algorithm": name,

            "success_rate": success_rate,

            "avg_movements": average("movements"),

            "avg_nodes": average("nodes"),

            "avg_time": average("time"),

            "avg_replans": average("replans"),

            "avg_obstacles": average("obstacles"),

            "successful_runs": len(successful),

            "total_runs": len(rows)

        })

    return summary


# ==========================================
# SAVE CSV FILES
# ==========================================

def save_results(all_results, summary):

    detail_file = "results/benchmark_details.csv"

    with open(
        detail_file,
        "w",
        newline=""
    ) as file:

        fields = list(all_results[0].keys())

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(all_results)

    summary_file = "results/benchmark_summary.csv"

    with open(
        summary_file,
        "w",
        newline=""
    ) as file:

        fields = list(summary[0].keys())

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(summary)

    print("\nCSV files saved successfully!")


# ==========================================
# GENERATE PERFORMANCE GRAPHS
# ==========================================

def generate_graphs(summary):

    names = [
        row["algorithm"] for row in summary
    ]

    metrics = [
        ("avg_movements", "Average Robot Movements",
         "Average Movements", "avg_movements.png"),

        ("avg_nodes", "Average Nodes Explored",
         "Average Nodes", "avg_nodes.png"),

        ("avg_time", "Average Search Time",
         "Time (seconds)", "avg_time.png"),

        ("avg_replans", "Average Replanning Operations",
         "Replanning Count", "avg_replans.png"),

        ("success_rate", "Navigation Success Rate",
         "Success Rate (%)", "success_rate.png")
    ]

    for key, title, ylabel, filename in metrics:

        values = [
            row[key] for row in summary
        ]

        plt.figure(figsize=(8, 5))

        plt.bar(names, values)

        plt.title(title)
        plt.xlabel("Algorithms")
        plt.ylabel(ylabel)

        plt.tight_layout()

        plt.savefig(
            os.path.join("results", filename)
        )

        plt.close()

    print("All benchmark graphs saved!")


# ==========================================
# MAIN BENCHMARK EXECUTION
# ==========================================

def main():

    environment = Environment()

    base_grid = copy.deepcopy(environment.grid)

    start = environment.start
    goal = environment.goal

    all_results = []

    print("\n======================================")
    print(" AUTONOMOUS ROBOT BENCHMARK")
    print("======================================")

    print("Total scenarios:", TOTAL_SCENARIOS)
    print("Algorithms:", len(ALGORITHMS))
    print("Total experiments:", TOTAL_SCENARIOS * len(ALGORITHMS))

    for scenario in range(1, TOTAL_SCENARIOS + 1):

        print(
            "\nScenario",
            scenario,
            "of",
            TOTAL_SCENARIOS
        )

        # Same schedule for all three algorithms
        schedule = create_scenario(
            base_grid,
            start,
            goal,
            seed=1000 + scenario
        )

        print(
            "Random obstacles:",
            len(schedule)
        )

        for name, algorithm in ALGORITHMS:

            result = run_experiment(
                base_grid,
                start,
                goal,
                algorithm,
                schedule
            )

            record = {
                "scenario": scenario,
                "algorithm": name,
                **result
            }

            all_results.append(record)

            print(
                name,
                "| Success:", result["success"],
                "| Movements:", result["movements"],
                "| Nodes:", result["nodes"],
                "| Replans:", result["replans"]
            )

    # Summary
    summary = calculate_summary(all_results)

    print("\n======================================")
    print(" FINAL BENCHMARK SUMMARY")
    print("======================================")

    for row in summary:

        print("\nAlgorithm:", row["algorithm"])

        print(
            "Success rate:",
            round(row["success_rate"], 2), "%"
        )

        print(
            "Average movements:",
            round(row["avg_movements"], 2)
        )

        print(
            "Average nodes:",
            round(row["avg_nodes"], 2)
        )

        print(
            "Average time:",
            round(row["avg_time"], 6),
            "seconds"
        )

        print(
            "Average replanning:",
            round(row["avg_replans"], 2)
        )

    # Save experimental data
    save_results(all_results, summary)

    # Generate graphs
    generate_graphs(summary)

    print("\n======================================")
    print(" BENCHMARK COMPLETED")
    print("======================================")

    print("Total experiments:", len(all_results))
    print("Results folder: results/")


if __name__ == "__main__":
    main()
