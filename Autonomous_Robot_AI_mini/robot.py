
class Robot:

    def __init__(self, start):

        self.start = start
        self.position = start

        self.path = []
        self.path_index = 0

        self.visited_cells = {start}
        self.total_movements = 0

    # Assign a new path to the robot
    def set_path(self, new_path):

        if not new_path:
            self.path = []
            self.path_index = 0
            return False

        # New path must begin at current position
        if new_path[0] != self.position:
            raise ValueError(
                "New path must start at the robot's current position"
            )

        self.path = new_path
        self.path_index = 0

        return True

    # Get cells remaining in the path
    def get_remaining_path(self):

        if not self.path:
            return []

        return self.path[self.path_index + 1:]

    # Move robot one cell forward
    def move_next(self):

        if not self.path:
            return None

        if self.path_index >= len(self.path) - 1:
            return None

        self.path_index += 1

        self.position = self.path[self.path_index]

        self.visited_cells.add(self.position)

        self.total_movements += 1

        return self.position

    # Check whether robot reached destination
    def reached_goal(self, goal):

        return self.position == goal

    # Check whether a path exists
    def has_path(self):

        return bool(self.path)

    # Check whether robot can move
    def can_move(self):

        return (
            bool(self.path)
            and self.path_index < len(self.path) - 1
        )

    # Return current robot position
    def get_position(self):

        return self.position

    # Return number of movements
    def get_movements(self):

        return self.total_movements
