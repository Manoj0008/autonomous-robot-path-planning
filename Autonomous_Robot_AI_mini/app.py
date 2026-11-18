
import copy
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from environment import Environment
from algorithms import bfs, dfs, astar
from robot import Robot


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Autonomous Robot Path Planning",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}

.block-container {
    padding-top: 2rem;
}

div.stButton > button {
    background-color: #ff4b4b;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 0.55rem 1.2rem;
    font-weight: bold;
}

div.stButton > button:hover {
    background-color: #e33b3b;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# ALGORITHM SELECTION
# --------------------------------------------------

ALGORITHMS = {
    "BFS": bfs,
    "DFS": dfs,
    "A*": astar
}


# --------------------------------------------------
# SIMULATION FUNCTION
# --------------------------------------------------

def run_simulation(algorithm_name, enable_dynamic):
    """Run one algorithm and deliberately activate obstacles on its route.

    Obstacles are inserted several cells ahead of the robot. This makes
    each activation block the current route and requires the selected
    algorithm to calculate a replacement path.
    """
    environment = Environment()
    original_grid = copy.deepcopy(environment.grid)
    grid = copy.deepcopy(original_grid)

    start = environment.start
    goal = environment.goal
    algorithm = ALGORITHMS[algorithm_name]

    initial_path, initial_nodes = algorithm(
        copy.deepcopy(grid), start, goal
    )

    if not initial_path:
        return {
            "success": False,
            "message": "No initial path found.",
            "grid": grid,
            "initial_path": [],
            "nodes": initial_nodes,
            "replans": 0,
            "dynamic_obstacles": 0,
            "trail": {start}
        }

    robot = Robot(start)
    robot.set_path(initial_path)

    nodes_explored = initial_nodes
    replans = 0
    dynamic_obstacles_added = 0
    robot_trail = {start}

    # Add an obstacle at each of these movement counts. The obstacle is
    # selected from the robot's CURRENT remaining route, not from another
    # algorithm's path or an unrelated grid location.
    obstacle_trigger_steps = [3, 9, 15, 21]
    next_trigger_index = 0
    max_iterations = 10000
    iterations = 0

    while not robot.reached_goal(goal):
        iterations += 1
        if iterations > max_iterations:
            break

        remaining_path = robot.get_remaining_path()
        if not remaining_path:
            break

        # Place a dynamic obstacle four cells ahead (or at the furthest
        # available future cell). It must be on the current route.
        if (
            enable_dynamic
            and next_trigger_index < len(obstacle_trigger_steps)
            and robot.total_movements >= obstacle_trigger_steps[next_trigger_index]
        ):
            target_index = min(3, len(remaining_path) - 1)
            obstacle_position = remaining_path[target_index]
            row, col = obstacle_position

            if (
                obstacle_position not in robot.visited_cells
                and obstacle_position != goal
                and grid[row][col] == 0
            ):
                grid[row][col] = 1
                dynamic_obstacles_added += 1

                # The selected route is guaranteed to contain this cell,
                # so this activation must cause a replanning attempt.
                new_path, explored = algorithm(
                    copy.deepcopy(grid), robot.position, goal
                )
                nodes_explored += explored
                replans += 1

                if not new_path:
                    return {
                        "success": False,
                        "message": "Robot could not find a new path.",
                        "grid": grid,
                        "robot": robot,
                        "initial_path": initial_path,
                        "nodes": nodes_explored,
                        "replans": replans,
                        "dynamic_obstacles": dynamic_obstacles_added,
                        "trail": robot_trail
                    }

                robot.set_path(new_path)

            # Move on to the next scheduled insertion. Each insertion is
            # tied to the current route at activation time.
            next_trigger_index += 1
            continue

        # Safety check before every movement.
        remaining_path = robot.get_remaining_path()
        if not remaining_path:
            break

        next_position = remaining_path[0]
        row, col = next_position

        if grid[row][col] == 1:
            new_path, explored = algorithm(
                copy.deepcopy(grid), robot.position, goal
            )
            nodes_explored += explored
            replans += 1

            if not new_path:
                break

            robot.set_path(new_path)
            continue

        robot.move_next()
        robot_trail.add(robot.position)

    success = robot.reached_goal(goal)

    return {
        "success": success,
        "message": (
            "Destination reached successfully!"
            if success
            else "Destination could not be reached."
        ),
        "grid": grid,
        "robot": robot,
        "initial_path": initial_path,
        "nodes": nodes_explored,
        "replans": replans,
        "dynamic_obstacles": dynamic_obstacles_added,
        "trail": robot_trail
    }


# --------------------------------------------------
# GRID VISUALIZATION
# --------------------------------------------------

def display_grid(result, show_path=True):

    grid = result["grid"]

    robot = result.get("robot")
    trail = result.get("trail", set())

    start = (0, 0)
    goal = (19, 19)

    dynamic_positions = set()

    if robot:
        # Static obstacles are also present in grid.
        # Dynamic obstacles are identified by comparing
        # against the original environment.
        original = Environment().grid

        for r in range(20):
            for c in range(20):
                if grid[r][c] == 1 and original[r][c] == 0:
                    dynamic_positions.add((r, c))

    path_cells = set()

    if robot and show_path:
        path_cells = set(robot.path)

    html = """
    <div style="overflow-x:auto;">
    <table style="
        border-collapse:collapse;
        width:100%;
        table-layout:fixed;
        text-align:center;
        font-size:12px;
    ">
    """

    # Column headings.
    html += "<tr><th></th>"

    for c in range(20):
        html += f"""
        <th style="
            background:#252936;
            color:#bbbbbb;
            border:1px solid #444;
            padding:5px 0;
        ">{c}</th>
        """

    html += "</tr>"

    for r in range(20):

        html += f"""
        <tr>
        <th style="
            background:#252936;
            color:#bbbbbb;
            border:1px solid #444;
            padding:5px;
        ">{r}</th>
        """

        for c in range(20):

            position = (r, c)

            color = "#10141c"
            symbol = ""

            if grid[r][c] == 1:
                color = "#33333d"
                symbol = "⬛"

            if position in dynamic_positions:
                color = "#b45309"
                symbol = "🟠"

            if position in trail and position not in (start, goal):
                color = "#166534"
                symbol = "🟢"

            if position in path_cells and position not in (start, goal):
                color = "#1d4ed8"
                symbol = "🔵"

            if position == start:
                color = "#047857"
                symbol = "🟢"

            if position == goal:
                color = "#b91c1c"
                symbol = "🏁"

            if robot and position == robot.position:
                color = "#7c3aed"
                symbol = "🤖"

            html += f"""
            <td style="
                background:{color};
                border:1px solid #343944;
                height:29px;
                padding:2px;
            ">{symbol}</td>
            """

        html += "</tr>"

    html += "</table></div>"

    components.html(html, height=750, scrolling=True)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("⚙️ Simulation Settings")

    selected_algorithm = st.selectbox(
        "Select Path Planning Algorithm",
        ["BFS", "DFS", "A*"]
    )

    show_path = st.checkbox(
        "Display calculated path",
        value=True
    )

    enable_dynamic = st.checkbox(
        "Enable dynamic obstacles",
        value=True
    )

    st.markdown("---")

    st.caption("Grid: 20 × 20")
    st.caption("Start: (0, 0)")
    st.caption("Destination: (19, 19)")


# --------------------------------------------------
# MAIN DASHBOARD
# --------------------------------------------------

st.title("🤖 Autonomous Robot Path Planning")

st.write(
    "Compare BFS, DFS and A* algorithms for "
    "autonomous robot navigation with dynamic "
    "obstacle avoidance."
)

if st.button("Find Robot Path", use_container_width=False):

    with st.spinner("Calculating robot path..."):

        result = run_simulation(
            selected_algorithm,
            enable_dynamic
        )

        st.session_state["simulation_result"] = result
        st.session_state["selected_algorithm"] = selected_algorithm


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

if "simulation_result" in st.session_state:

    result = st.session_state["simulation_result"]

    if result["success"]:
        st.success(result["message"])
    else:
        st.error(result["message"])

    if "robot" in result:

        robot = result["robot"]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Algorithm",
            st.session_state["selected_algorithm"]
        )

        col2.metric(
            "Path Movements",
            robot.total_movements
        )

        col3.metric(
            "Nodes Explored",
            result["nodes"]
        )

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Replanning Operations",
            result["replans"]
        )

        col5.metric(
            "Dynamic Obstacles Added",
            result["dynamic_obstacles"]
        )

        col6.metric(
            "Final Robot Position",
            str(robot.position)
        )

        st.markdown("---")

        st.subheader("📍 Robot Navigation Grid")

        display_grid(result, show_path)

        st.markdown("---")

        st.subheader("📊 Simulation Summary")

        st.write(
            f"**Initial Path Length:** "
            f"{len(result['initial_path']) - 1} movements"
        )

        st.write(
            f"**Actual Robot Movements:** "
            f"{robot.total_movements}"
        )

        st.write(
            f"**Nodes Explored:** "
            f"{result['nodes']}"
        )

        st.write(
            f"**Replanning Operations:** "
            f"{result['replans']}"
        )

        st.write(
            f"**Dynamic Obstacles Added:** "
            f"{result['dynamic_obstacles']}"
        )

        st.write(
            f"**Final Position:** "
            f"{robot.position}"
        )

    else:
        st.info("No robot path is available to display.")

else:

    st.info(
        "Select an algorithm and click "
        "'Find Robot Path' to start the simulation."
    )

    st.subheader("📍 Robot Navigation Grid")

    st.write(
        "The simulation uses a 20 × 20 grid "
        "with static obstacles."
    )


# --------------------------------------------------
# BENCHMARK ALGORITHM COMPARISON
# --------------------------------------------------

st.markdown("---")

st.header("📈 Algorithm Performance Comparison")

st.write(
    "This section compares BFS, DFS and A* using the saved "
    "benchmark dataset. It is separate from the single "
    "simulation above."
)

BASE_DIR = Path(__file__).resolve().parent

BENCHMARK_CANDIDATES = [
    BASE_DIR / "results" / "benchmark_details.csv",
    BASE_DIR / "benchmark_details.csv",
]

benchmark_file = next(
    (p for p in BENCHMARK_CANDIDATES if p.exists()),
    None
)


if benchmark_file is None:

    st.warning(
        "Benchmark data was not found. Place "
        "benchmark_details.csv inside the results folder "
        "(recommended) or beside app.py, then refresh."
    )

else:

    try:

        benchmark_df = pd.read_csv(benchmark_file)

        required_columns = {
            "scenario",
            "algorithm",
            "success",
            "movements",
            "nodes",
            "time",
            "replans"
        }

        missing_columns = required_columns.difference(
            benchmark_df.columns
        )

        if missing_columns:

            st.error(
                "The benchmark CSV is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        else:

            benchmark_df["algorithm"] = (
                benchmark_df["algorithm"]
                .astype(str)
                .str.strip()
            )

            benchmark_df = benchmark_df[
                benchmark_df["algorithm"].isin(["BFS", "DFS", "A*"])
            ].copy()

            for column in ["movements", "nodes", "time", "replans"]:

                benchmark_df[column] = pd.to_numeric(
                    benchmark_df[column],
                    errors="coerce"
                )

            # Convert common CSV success representations into 1/0.
            benchmark_df["success_numeric"] = (
                benchmark_df["success"]
                .astype(str)
                .str.strip()
                .str.lower()
                .map({
                    "true": 1,
                    "1": 1,
                    "yes": 1,
                    "success": 1,
                    "false": 0,
                    "0": 0,
                    "no": 0,
                    "failed": 0
                })
            )

            # Calculate average performance for each algorithm.
            summary = (
                benchmark_df
                .groupby("algorithm", sort=False)
                .agg(
                    scenarios=("scenario", "nunique"),
                    avg_movements=("movements", "mean"),
                    avg_nodes=("nodes", "mean"),
                    avg_time=("time", "mean"),
                    avg_replans=("replans", "mean"),
                    success_rate=("success_numeric", "mean")
                )
                .reindex(["BFS", "DFS", "A*"])
            )

            summary["success_rate"] = (
                summary["success_rate"] * 100
            )

            # Data source information.
            st.caption(
                f"Data source: {benchmark_file.relative_to(BASE_DIR)} · "
                f"{len(benchmark_df)} experiment records"
            )

            # Benchmark overview metrics.
            m1, m2, m3 = st.columns(3)

            m1.metric(
                "Benchmark experiments",
                len(benchmark_df)
            )

            m2.metric(
                "Scenarios per algorithm",
                int(summary["scenarios"].min())
            )

            m3.metric(
                "Overall success rate",
                (
                    f"{benchmark_df['success_numeric'].mean() * 100:.1f}%"
                    if benchmark_df["success_numeric"].notna().any()
                    else "N/A"
                )
            )

            # Benchmark summary table.
            st.subheader("📋 Benchmark Summary")

            display_summary = summary.rename(
                columns={
                    "scenarios": "Scenarios",
                    "avg_movements": "Average movements",
                    "avg_nodes": "Average nodes explored",
                    "avg_time": "Average execution time (seconds)",
                    "avg_replans": "Average replanning operations",
                    "success_rate": "Success rate (%)"
                }
            )

            st.dataframe(
                display_summary.round(4),
                use_container_width=True
            )

            # ------------------------------------------
            # DISPLAY ALL FIVE COMPARISON GRAPHS
            # ------------------------------------------

            st.markdown("---")

            st.header("📊 Algorithm Comparison Graphs")

            # Graph 1: Average movements.
            st.subheader("1. Average Path Movements")

            movements_chart = summary[
                ["avg_movements"]
            ].rename(
                columns={
                    "avg_movements": "Average Movements"
                }
            )

            st.bar_chart(
                movements_chart,
                use_container_width=True
            )

            # Graph 2: Average nodes explored.
            st.subheader("2. Average Nodes Explored")

            nodes_chart = summary[
                ["avg_nodes"]
            ].rename(
                columns={
                    "avg_nodes": "Average Nodes"
                }
            )

            st.bar_chart(
                nodes_chart,
                use_container_width=True
            )

            # Graph 3: Average execution time.
            st.subheader("3. Average Execution Time")

            time_chart = summary[
                ["avg_time"]
            ].rename(
                columns={
                    "avg_time": "Execution Time (seconds)"
                }
            )

            st.bar_chart(
                time_chart,
                use_container_width=True
            )

            # Graph 4: Average replanning operations.
            st.subheader("4. Average Replanning Operations")

            replans_chart = summary[
                ["avg_replans"]
            ].rename(
                columns={
                    "avg_replans": "Average Replanning"
                }
            )

            st.bar_chart(
                replans_chart,
                use_container_width=True
            )

            # Graph 5: Success rate.
            st.subheader("5. Algorithm Success Rate")

            success_chart = summary[
                ["success_rate"]
            ].rename(
                columns={
                    "success_rate": "Success Rate (%)"
                }
            )

            st.bar_chart(
                success_chart,
                use_container_width=True
            )

            st.markdown("---")

            st.success(
                "All five algorithm comparison graphs are displayed "
                "using the benchmark dataset."
            )

            st.info(
                "Interpretation: Lower movements, explored nodes, "
                "execution time and replanning counts indicate lower "
                "values for those metrics. A higher success rate is better. "
                "Compare all metrics together."
            )

    except Exception as exc:

        st.error(
            f"Could not load benchmark results: {exc}"
        )
