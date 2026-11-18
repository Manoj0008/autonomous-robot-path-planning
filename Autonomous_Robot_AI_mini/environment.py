
import pygame

# Screen settings
CELL_SIZE = 30
ROWS = 20
COLS = 20

WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE

# Colors
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
GRAY = (190, 190, 190)
GREEN = (0, 200, 0)
RED = (220, 0, 0)
BLUE = (50, 100, 255)


class Environment:

    def __init__(self):

        self.grid = [
            [0 for _ in range(COLS)]
            for _ in range(ROWS)
        ]

        # Starting position
        self.start = (0, 0)

        # Destination
        self.goal = (19, 19)

        # Static obstacles
        self.obstacles = [
            (3, 3), (3, 4), (3, 5),
            (4, 5), (5, 5), (6, 5),
            (8, 8), (8, 9), (8, 10),
            (9, 10), (10, 10),
            (12, 14), (13, 14),
            (14, 14), (15, 14)
        ]

        for row, col in self.obstacles:
            self.grid[row][col] = 1

    def draw(self, screen):

        screen.fill(WHITE)

        for row in range(ROWS):
            for col in range(COLS):

                x = col * CELL_SIZE
                y = row * CELL_SIZE

                rect = pygame.Rect(
                    x, y, CELL_SIZE, CELL_SIZE
                )

                if self.grid[row][col] == 1:
                    pygame.draw.rect(screen, BLACK, rect)

                else:
                    pygame.draw.rect(screen, WHITE, rect)

                pygame.draw.rect(
                    screen, GRAY, rect, 1
                )

        # Draw start position
        pygame.draw.rect(
            screen,
            GREEN,
            (0, 0, CELL_SIZE, CELL_SIZE)
        )

        # Draw goal position
        pygame.draw.rect(
            screen,
            RED,
            (
                self.goal[1] * CELL_SIZE,
                self.goal[0] * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
        )
