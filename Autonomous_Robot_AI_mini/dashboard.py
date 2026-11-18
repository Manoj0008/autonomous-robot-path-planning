
import pygame
import random
import time
import csv
import os
import copy

from datetime import datetime

from environment import Environment
from algorithms import bfs, dfs, astar


# =====================================================
# 1. INITIALIZATION
# =====================================================

pygame.init()

CELL_SIZE = 30
PANEL_WIDTH = 450
PANEL_HEIGHT = 850

environment = Environment()

original_grid = copy.deepcopy(environment.grid)

# Static grid contains original, manual and random obstacles.
static_grid = copy.deepcopy(original_grid)

# Active grid also contains dynamic obstacles.
grid = copy.deepcopy(static_grid)

ROWS = len(grid)
COLS = len(grid[0])

GRID_SIZE = COLS * CELL_SIZE

WIDTH = GRID_SIZE + PANEL_WIDTH
HEIGHT = max(PANEL_HEIGHT, ROWS * CELL_SIZE)

screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption(
    "Autonomous Robot - AI Control Dashboard"
)

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 14)
title_font = pygame.font.SysFont("Arial", 23, bold=True)

start = environment.start
goal = environment.goal

robot_position = start


# =====================================================
# 2. ALGORITHMS
# =====================================================

algorithms = {
    "BFS": bfs,
    "DFS": dfs,
    "A*": astar
}

selected_algorithm = "A*"


# =====================================================
# 3. ROBOT STATE
# =====================================================

path = []
path_index = 0

visited_cells = {start}

robot_running = False
robot_finished = False

nodes_explored = 0
execution_time = 0.0

replanning_count = 0
total_movements = 0

initial_path_length = 0

dynamic_obstacles = []
obstacles_created = 0

MAX_DYNAMIC_OBSTACLES = 5

MOVE_DELAY = 150
last_move_time = 0

run_started = False
run_saved = False


# =====================================================
# 4. CSV RESULT STORAGE
# =====================================================

RESULTS_FOLDER = "results"

RESULTS_FILE = os.path.join(
    RESULTS_FOLDER,
    "dashboard_results.csv"
)

os.makedirs(RESULTS_FOLDER, exist_ok=True)

CSV_HEADERS = [
    "Run_ID",
    "Date_Time",
    "Algorithm",
    "Success",
    "Initial_Path_Length",
    "Actual_Robot_Movements",
    "Nodes_Explored",
    "Execution_Time_Seconds",
    "Replanning_Operations",
    "Dynamic_Obstacles_Added"
]


def save_result(success):

    global run_saved

    if not run_started or run_saved:
        return

    file_exists = (
        os.path.exists(RESULTS_FILE)
        and os.path.getsize(RESULTS_FILE) > 0
    )

    now = datetime.now()

    with open(
        RESULTS_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(CSV_HEADERS)

        writer.writerow([
            now.strftime("%Y%m%d_%H%M%S_%f"),
            now.strftime("%Y-%m-%d %H:%M:%S"),
            selected_algorithm,
            "Yes" if success else "No",
            initial_path_length,
            total_movements,
            nodes_explored,
            round(execution_time, 6),
            replanning_count,
            obstacles_created
        ])

    run_saved = True

    print("\n===================================")
    print(" DASHBOARD RESULT SAVED")
    print("===================================")
    print("Algorithm:", selected_algorithm)
    print("Success:", success)
    print("Initial path length:", initial_path_length)
    print("Actual movements:", total_movements)
    print("Nodes explored:", nodes_explored)
    print("Execution time:", round(execution_time, 6))
    print("Replanning:", replanning_count)
    print("Dynamic obstacles:", obstacles_created)
    print("Saved file:", RESULTS_FILE)
    print("===================================")


# =====================================================
# 5. COLORS
# =====================================================

WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
GREY = (210, 210, 210)

GREEN = (0, 190, 40)
RED = (220, 0, 0)

BLUE = (0, 100, 255)
YELLOW = (255, 220, 0)

ORANGE = (255, 140, 0)
DARK = (35, 40, 55)

BUTTON = (65, 85, 115)
BUTTON_SELECTED = (30, 125, 190)

CYAN = (0, 180, 180)


# =====================================================
# 6. TEXT FUNCTION
# =====================================================

def draw_text(
    text,
    x,
    y,
    color=WHITE,
    selected_font=None
):

    if selected_font is None:
        selected_font = font

    image = selected_font.render(
        str(text),
        True,
        color
    )

    screen.blit(image, (x, y))


# =====================================================
# 7. BUTTON FUNCTION
# =====================================================

buttons = {}


def draw_button(name, label, x, y, width, height):

    rect = pygame.Rect(
        x, y, width, height
    )

    buttons[name] = rect

    if name == selected_algorithm:
        color = BUTTON_SELECTED
    else:
        color = BUTTON

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=8
    )

    image = small_font.render(
        label,
        True,
        WHITE
    )

    text_rect = image.get_rect(
        center=rect.center
    )

    screen.blit(image, text_rect)


# =====================================================
# 8. DRAW GRID
# =====================================================

def draw_grid():

    for row in range(ROWS):

        for col in range(COLS):

            position = (row, col)

            rect = pygame.Rect(
                col * CELL_SIZE,
                row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            if grid[row][col] == 1:

                color = BLACK

            else:

                color = WHITE

            pygame.draw.rect(
                screen,
                color,
                rect
            )

            pygame.draw.rect(
                screen,
                GREY,
                rect,
                1
            )

    # Dynamic obstacles
    for row, col in dynamic_obstacles:

        pygame.draw.rect(
            screen,
            ORANGE,
            (
                col * CELL_SIZE,
                row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
        )

    # Current planned path
    if path:

        points = [
            (
                col * CELL_SIZE + CELL_SIZE // 2,
                row * CELL_SIZE + CELL_SIZE // 2
            )
            for row, col in path
        ]

        if len(points) > 1:

            pygame.draw.lines(
                screen,
                BLUE,
                False,
                points,
                4
            )

    # Complete actual robot trajectory
    for row, col in visited_cells:

        if (row, col) != start:

            pygame.draw.circle(
                screen,
                CYAN,
                (
                    col * CELL_SIZE + CELL_SIZE // 2,
                    row * CELL_SIZE + CELL_SIZE // 2
                ),
                4
            )

    # Start
    pygame.draw.rect(
        screen,
        GREEN,
        (
            start[1] * CELL_SIZE,
            start[0] * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
    )

    # Goal
    pygame.draw.rect(
        screen,
        RED,
        (
            goal[1] * CELL_SIZE,
            goal[0] * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
    )

    # Robot
    row, col = robot_position

    pygame.draw.circle(
        screen,
        YELLOW,
        (
            col * CELL_SIZE + CELL_SIZE // 2,
            row * CELL_SIZE + CELL_SIZE // 2
        ),
        11
    )


# =====================================================
# 9. DRAW DASHBOARD PANEL
# =====================================================

def draw_panel():

    pygame.draw.rect(
        screen,
        DARK,
        (
            GRID_SIZE,
            0,
            PANEL_WIDTH,
            HEIGHT
        )
    )

    x = GRID_SIZE + 20

    draw_text(
        "ROBOT AI DASHBOARD",
        x,
        22,
        WHITE,
        title_font
    )

    # Algorithm selection
    draw_text(
        "Algorithm Selection",
        x,
        85
    )

    draw_button(
        "BFS", "BFS",
        x, 120, 85, 40
    )

    draw_button(
        "DFS", "DFS",
        x + 95, 120, 85, 40
    )

    draw_button(
        "A*", "A*",
        x + 190, 120, 85, 40
    )

    # Controls
    draw_text(
        "Robot Controls",
        x,
        190
    )

    draw_button(
        "RUN",
        "START ROBOT",
        x, 225, 130, 45
    )

    draw_button(
        "RESET",
        "RESET RUN",
        x + 145, 225, 130, 45
    )

    draw_button(
        "RANDOM",
        "RANDOM OBSTACLES",
        x, 290, 275, 45
    )

    draw_button(
        "DYNAMIC",
        "ADD DYNAMIC OBSTACLE",
        x, 350, 275, 45
    )

    draw_button(
        "CLEAR",
        "CLEAR ALL OBSTACLES",
        x, 410, 275, 45
    )

    # Metrics
    draw_text(
        "Performance Metrics",
        x,
        490
    )

    draw_text(
        "Algorithm: " + selected_algorithm,
        x,
        530
    )

    draw_text(
        "Initial path length: " + str(initial_path_length),
        x,
        565,
        WHITE,
        small_font
    )

    draw_text(
        "Robot movements: " + str(total_movements),
        x,
        595,
        WHITE,
        small_font
    )

    draw_text(
        "Nodes explored: " + str(nodes_explored),
        x,
        625,
        WHITE,
        small_font
    )

    draw_text(
        "Search time: " + str(round(execution_time, 6)) + " sec",
        x,
        655,
        WHITE,
        small_font
    )

    draw_text(
        "Replanning: " + str(replanning_count),
        x,
        685,
        WHITE,
        small_font
    )

    draw_text(
        "Dynamic obstacles: " + str(obstacles_created),
        x,
        715,
        WHITE,
        small_font
    )

    # Status
    if robot_finished:

        status = "DESTINATION REACHED"
        color = GREEN

    elif robot_running:

        status = "ROBOT MOVING"
        color = YELLOW

    elif run_saved:

        status = "RESULT SAVED"
        color = GREEN

    else:

        status = "READY"
        color = YELLOW

    draw_text(
        "Status: " + status,
        x,
        775,
        color,
        small_font
    )

    draw_text(
        "CSV: results/dashboard_results.csv",
        x,
        810,
        WHITE,
        small_font
    )


# =====================================================
# 10. CALCULATE PATH
# =====================================================

def calculate_path():

    global path
    global path_index
    global nodes_explored
    global execution_time
    global robot_running

    algorithm = algorithms[selected_algorithm]

    search_start = time.perf_counter()

    new_path, explored = algorithm(
        grid,
        robot_position,
        goal
    )

    elapsed = time.perf_counter() - search_start

    execution_time += elapsed
    nodes_explored += explored

    if not new_path:

        path = []
        robot_running = False

        print("No valid path found.")

        return False

    # Validate path starts at current robot position
    if new_path[0] != robot_position:

        print("Error: Algorithm returned an invalid path.")
        path = []
        robot_running = False

        return False

    path = new_path
    path_index = 0

    robot_running = True

    print(
        selected_algorithm,
        "path found:",
        len(path) - 1
    )

    return True


# =====================================================
# 11. START NEW RUN
# =====================================================

def start_new_run():

    global grid
    global robot_position
    global path
    global path_index

    global nodes_explored
    global execution_time
    global replanning_count
    global total_movements
    global initial_path_length

    global robot_running
    global robot_finished
    global run_saved
    global run_started

    global visited_cells
    global dynamic_obstacles
    global obstacles_created

    robot_running = False

    # Preserve user-created static obstacles.
    # Remove only dynamic obstacles from previous run.
    grid = copy.deepcopy(static_grid)

    robot_position = start

    path = []
    path_index = 0

    nodes_explored = 0
    execution_time = 0.0

    replanning_count = 0
    total_movements = 0
    initial_path_length = 0

    robot_finished = False
    run_saved = False
    run_started = True

    visited_cells = {start}

    dynamic_obstacles = []
    obstacles_created = 0

    print("\n================================")
    print("NEW ROBOT RUN")
    print("Algorithm:", selected_algorithm)
    print("================================")

    if calculate_path():

        initial_path_length = len(path) - 1

        # Start already equals destination
        if robot_position == goal:

            robot_running = False
            robot_finished = True

            save_result(True)

    else:

        save_result(False)


# =====================================================
# 12. RESET RUN
# =====================================================

def reset_robot():

    global grid
    global robot_position
    global path
    global path_index

    global nodes_explored
    global execution_time
    global replanning_count
    global total_movements
    global initial_path_length

    global robot_running
    global robot_finished
    global run_saved
    global run_started

    global visited_cells
    global dynamic_obstacles
    global obstacles_created

    robot_running = False

    # Preserve static map
    grid = copy.deepcopy(static_grid)

    robot_position = start

    path = []
    path_index = 0

    nodes_explored = 0
    execution_time = 0.0

    replanning_count = 0
    total_movements = 0
    initial_path_length = 0

    robot_finished = False
    run_saved = False
    run_started = False

    visited_cells = {start}

    dynamic_obstacles = []
    obstacles_created = 0

    print("Robot reset. Static obstacles preserved.")


# =====================================================
# 13. RANDOM STATIC OBSTACLES
# =====================================================

def generate_random_obstacles():

    global static_grid
    global grid

    if robot_running:
        print("Reset the robot before changing the map.")
        return

    static_grid = copy.deepcopy(original_grid)

    available = []

    for row in range(ROWS):

        for col in range(COLS):

            position = (row, col)

            if (
                static_grid[row][col] == 0
                and position != start
                and position != goal
            ):

                available.append(position)

    count = min(20, len(available))

    selected = random.sample(
        available,
        count
    )

    for row, col in selected:

        static_grid[row][col] = 1

    grid = copy.deepcopy(static_grid)

    print(
        "Random static obstacles generated:",
        count
    )

    reset_robot()


# =====================================================
# 14. ADD DYNAMIC OBSTACLE AND REPLAN
# =====================================================

def add_dynamic_obstacle():

    global grid
    global replanning_count
    global obstacles_created
    global robot_running

    if not robot_running:

        print("Start the robot before adding a dynamic obstacle.")
        return

    if obstacles_created >= MAX_DYNAMIC_OBSTACLES:

        print("Maximum dynamic obstacles reached.")
        return

    remaining = path[path_index + 1:]

    # Choose a cell on the remaining path.
    candidates = [
        position
        for position in remaining[1:9]
        if (
            grid[position[0]][position[1]] == 0
            and position != goal
            and position != robot_position
            and position not in visited_cells
        )
    ]

    if not candidates:

        print("No suitable path cell for a new obstacle.")
        return

    obstacle = random.choice(candidates)

    row, col = obstacle

    grid[row][col] = 1

    dynamic_obstacles.append(obstacle)

    obstacles_created += 1

    print("\nDynamic obstacle created:", obstacle)

    # It was deliberately placed on the remaining path.
    # Therefore replanning is required.
    replanning_count += 1

    robot_running = False

    print("Path blocked. Replanning started.")

    if calculate_path():

        print("Alternative path found.")

    else:

        print("No alternative path exists.")

        save_result(False)


# =====================================================
# 15. CLEAR ALL USER-CREATED OBSTACLES
# =====================================================

def clear_added_obstacles():

    global static_grid
    global grid

    if robot_running:

        print("Reset the robot before clearing obstacles.")
        return

    static_grid = copy.deepcopy(original_grid)

    grid = copy.deepcopy(original_grid)

    reset_robot()

    print("All added static obstacles cleared.")


# =====================================================
# 16. MAIN EVENT LOOP
# =====================================================

running = True

while running:

    screen.fill(WHITE)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            mx, my = pygame.mouse.get_pos()

            # -----------------------------------------
            # GRID MOUSE INTERACTION
            # -----------------------------------------

            if mx < GRID_SIZE:

                row = my // CELL_SIZE
                col = mx // CELL_SIZE

                if (
                    row < ROWS
                    and col < COLS
                    and not robot_running
                ):

                    position = (row, col)

                    if (
                        position != start
                        and position != goal
                    ):

                        if event.button == 1:

                            # Left click toggles static obstacle
                            static_grid[row][col] = (
                                0 if static_grid[row][col] == 1 else 1
                            )

                            grid = copy.deepcopy(static_grid)

                            reset_robot()

                        elif event.button == 3:

                            # Right click removes obstacle
                            static_grid[row][col] = 0

                            grid = copy.deepcopy(static_grid)

                            reset_robot()

            # -----------------------------------------
            # DASHBOARD BUTTON INTERACTION
            # -----------------------------------------

            else:

                for name, rect in list(buttons.items()):

                    if rect.collidepoint(mx, my):

                        if name in algorithms:

                            if not robot_running:

                                selected_algorithm = name

                                reset_robot()

                                print(
                                    "Selected algorithm:",
                                    selected_algorithm
                                )

                        elif name == "RUN":

                            if not robot_running:

                                start_new_run()

                        elif name == "RESET":

                            reset_robot()

                        elif name == "RANDOM":

                            generate_random_obstacles()

                        elif name == "DYNAMIC":

                            add_dynamic_obstacle()

                        elif name == "CLEAR":

                            clear_added_obstacles()

                        break

    # =================================================
    # 17. ROBOT MOVEMENT
    # =================================================

    if robot_running:

        current_time = pygame.time.get_ticks()

        if current_time - last_move_time >= MOVE_DELAY:

            last_move_time = current_time

            if path_index < len(path) - 1:

                next_position = path[path_index + 1]

                next_row, next_col = next_position

                # Safety check
                if grid[next_row][next_col] == 1:

                    robot_running = False

                    replanning_count += 1

                    print("Unexpected obstacle detected.")

                    if not calculate_path():

                        save_result(False)

                else:

                    path_index += 1

                    robot_position = path[path_index]

                    total_movements += 1

                    visited_cells.add(robot_position)

            # Destination reached
            if (
                robot_position == goal
                and not run_saved
            ):

                robot_running = False

                robot_finished = True

                print("\nRobot reached destination!")

                save_result(True)

    # =================================================
    # 18. DRAW INTERFACE
    # =================================================

    buttons.clear()

    draw_grid()

    draw_panel()

    pygame.display.flip()

    clock.tick(60)


# =====================================================
# 19. EXIT
# =====================================================

pygame.quit()
