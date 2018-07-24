"""

"""
import queue as queue
import THREE
import heapq
from Heightmap import *
from Array2D import *


def nonimy():
    return None


# Create a priority queue abstract base class
class Priority_queue:
    # Initialize the instance
    def __init__(self):
        # Create a list to use as the queue
        self._queue = []
        # Create an index to use as ordering
        self._index = 0

    # Create a function to add a task to the queue
    def push(self, item, priority):
        # Push the arguments to the _queue using a heap
        heapq.heappush(self._queue, (priority, self._index, item))
        # Add one to the index
        self._index += 1

    # Create a function to get the next item from the queue
    def pop(self):
        # Return the next item in the queue
        return heapq.heappop(self._queue)[-1]

    # Create a function to get the next item from the queue
    def empty(self):
        # Return the next item in the queue
        return len(self._queue) == 0


class AStar:
    directions = {
        "downward": THREE.Vector2(0, 1),
        "upward": THREE.Vector2(0, -1),
        "leftward": THREE.Vector2(-1, 0),
        "rightward": THREE.Vector2(1, 0),
        "downright": THREE.Vector2(1, 1),
        "downleft": THREE.Vector2(-1, 1),
        "upright": THREE.Vector2(1, -1),
        "upleft": THREE.Vector2(-1, -1)
    }
    neighbors = ["upward", "leftward", "downward", "rightward"]

    """

    """
    def __init__(self, heightmap, size, source, target):
        """
        
        :param heightmap: 
        :param size: 
        :param source: 
        :param target: 
        """
        self.path = None
        self.source = source
        self.target = target
        self.heightmap = heightmap
        self.size = size
        
        self.came_from = Array2D(size, THREE.Vector2)
        for i in range(size*size):
            self.came_from.map[i] = None

        self.cost_so_far = Heightmap(size)
        self.done = Heightmap(size)
        self.done.setV(source, True)
        
        self.frontier = Priority_queue()
        self.frontier.push(source, 0)
        self.prev = None

    def parse_graph(self):
        """

        :return:
        """
        frontier = self.frontier
        target = self.target
        heightmap = self.heightmap
        came_from = self.came_from
        cost_so_far = self.cost_so_far
        done = self.done
        size = self.size

        loop = 999999
        reached = False
        next = THREE.Vector2()
        path = THREE.Vector2()

        while not frontier.empty() and loop > 0 and not reached:
            loop -= 1
            current = frontier.pop()
            prev = came_from.getV(current)

            if current.equals(target):
                reached = True
                break

            z = heightmap.getV(current)

            for i in range(4):
                n = AStar.neighbors[i]
                d = AStar.directions[n]

                next.addVectors(current, d)

                if next.equals(target):
                    came_from.setV(next, current)
                    reached = True
                    break

                if next.x < 0 or next.y < 0 or next.x >= size or next.y >= size:
                    continue

                # // Manhattan distance on a square grid
                dl = (abs(target.x - next.x) + abs(target.y - next.y))/1
                # dl = Math.sqrt((target.x - next.x)*(target.x - next.x) + (target.y - next.y)*(target.y - next.y))
                z1 = heightmap.getV(next)

                # // add extra weight to avoid 90deg angle or too straight line
                if prev:
                    path.subVectors(next, prev)
                    bias = (path.x == 0) + (path.y == 0)
                else:
                    bias = 0

                _cost = cost_so_far.getV(current) + abs(z - z1)+bias
                cost_next = cost_so_far.getV(next)

                if not done.getV(next) or _cost < cost_next:
                    cost_so_far.setV(next, _cost)
                    done.setV(next, 1)
                    # // var priority = _cost * d  // increase priority when we are fare from the target
                    priority = _cost + dl       # // increase priority when we are fare from the target
                    a = next.clone()
                    frontier.push(a, priority)
                    came_from.setV(next, current)

        if not reached:
            exit(-1)

        self.render_path()

    def dijkstra(self):
        """

        :return:
        """
        frontier = self.frontier
        target = self.target
        heightmap = self.heightmap
        came_from = self.came_from
        cost_so_far = self.cost_so_far
        size = self.size

        reached = False
        next = THREE.Vector2()
        loop = 10000

        while not frontier.empty() > 0 and loop > 0:
            loop -= 1
            priority, current = frontier.get()

            if current.equals(target):
                reached = True
                break

            z = heightmap.getV(current)

            for i in range(4):
                n = AStar.neighbors[i]
                d = AStar.directions[n]

                next.addVectors(current, d)

                if next.equals(target):
                    came_from.setV(next, current)
                    reached = True
                    loop = -1
                    break

                if next.x < 0 or next.y < 0 or next.x >= size or next.y >= size:
                    continue

                z1 = heightmap.getV(next)
                graph_cost = abs(z - z1)

                _cost = cost_so_far.getV(current) + graph_cost
                cost_next = cost_so_far.getV(next)

                if cost_next is None or _cost < cost_next:
                    cost_so_far.setV(next, _cost)
                    # //var priority = _cost * d  // increase priority when we are fare from the target
                    priority = _cost
                    frontier.put((priority, next.clone()))
                    came_from.setV(next, current)

        if not reached:
            exit(-1)

        return self.frontier

    def render_path(self):
        """

        :return:
        """
        # // draw the path from the target to the source
        current = self.target
        came_from = self.came_from
        path = []

        safety = 1999

        while current is not None and safety > 0:
            path.append(current)
            current = came_from.getV(current)

            safety -= 1

        if safety < 0:
            exit(-1)

        self.path = path
