from svgelements import *


class CutPlanner:

    @staticmethod
    def bounding_box(elements):
        if isinstance(elements, SVGElement):
            elements = [elements]
        elif isinstance(elements, list):
            try:
                elements = [e.object for e in elements if isinstance(e.object, SVGElement)]
            except AttributeError:
                pass
        boundary_points = []
        for e in elements:
            box = e.bbox(False)
            if box is None:
                continue
            top_left = e.transform.point_in_matrix_space([box[0], box[1]])
            top_right = e.transform.point_in_matrix_space([box[2], box[1]])
            bottom_left = e.transform.point_in_matrix_space([box[0], box[3]])
            bottom_right = e.transform.point_in_matrix_space([box[2], box[3]])
            boundary_points.append(top_left)
            boundary_points.append(top_right)
            boundary_points.append(bottom_left)
            boundary_points.append(bottom_right)
        if len(boundary_points) == 0:
            return None
        xmin = min([e[0] for e in boundary_points])
        ymin = min([e[1] for e in boundary_points])
        xmax = max([e[0] for e in boundary_points])
        ymax = max([e[1] for e in boundary_points])
        return xmin, ymin, xmax, ymax

    @staticmethod
    def is_inside(inner_path, outer_path):
        """
        Test that path1 is inside path2.
        :param inner_path: inner path
        :param outer_path: outer path
        :return: whether path1 is wholely inside path2.
        """
        if not hasattr(inner_path, 'bounding_box'):
            inner_path.bounding_box = CutPlanner.bounding_box(inner_path)
        if not hasattr(outer_path, 'bounding_box'):
            outer_path.bounding_box = CutPlanner.bounding_box(outer_path)
        if outer_path.bounding_box[0] > inner_path.bounding_box[0]:
            # outer minx > inner minx (is not contained)
            return False
        if outer_path.bounding_box[1] > inner_path.bounding_box[1]:
            # outer miny > inner miny (is not contained)
            return False
        if outer_path.bounding_box[2] < inner_path.bounding_box[2]:
            # outer maxx < inner maxx (is not contained)
            return False
        if outer_path.bounding_box[3] < inner_path.bounding_box[3]:
            # outer maxy < inner maxy (is not contained)
            return False
        if outer_path.bounding_box == inner_path.bounding_box:
            if outer_path == inner_path:  # This is the same object.
                return False
        if not hasattr(outer_path, 'vm'):
            outer_path = Polygon([outer_path.point(i / 100.0, error=1e4) for i in range(101)])
            vm = VectorMontonizer()
            vm.add_cluster(outer_path)
            outer_path.vm = vm
        for i in range(101):
            p = inner_path.point(i / 100.0, error=1e4)
            if not outer_path.vm.is_point_inside(p.x, p.y):
                return False
        return True

    @staticmethod
    def optimize_cut_inside(paths):
        optimized = Path()
        if isinstance(paths, Path):
            paths = [paths]
        subpaths = []
        for path in paths:
            subpaths.extend([abs(Path(s)) for s in path.as_subpaths()])
        for j in range(len(subpaths)):
            for k in range(j + 1, len(subpaths)):
                if CutPlanner.is_inside(subpaths[k], subpaths[j]):
                    t = subpaths[j]
                    subpaths[j] = subpaths[k]
                    subpaths[k] = t
        for p in subpaths:
            optimized += p
            try:
                del p.vm
            except AttributeError:
                pass
            try:
                del p.bounding_box
            except AttributeError:
                pass
        return optimized

    @staticmethod
    def eulerian_fill(paths, distance=16):
        fill = Path()
        for path in paths:
            efill = EulerianFill(distance)
            trace = Polygon([path.point(i / 100.0, error=1e-4) for i in range(101)])
            points = efill.get_fill(trace)
            start = 0
            i = 0
            while i < len(points):
                p = points[i]
                if p is None:
                    fill += Polyline(points[start:i])
                    start = i + 1
                i += 1
            if start != i:
                fill += Polyline(points[start:i])
        return fill

    @staticmethod
    def length_travel(paths):
        distance = 0.0
        for p in paths:
            for s in p:
                if isinstance(s, Move):
                    if s.start is not None:
                        distance += Point.distance(s.start, s.end)
        return distance

    @staticmethod
    def optimize_travel(paths):
        optimized = Path()
        if isinstance(paths, Path):
            paths = [paths]
        subpaths = []
        for path in paths:
            subpaths.extend([abs(Path(s)) for s in path.as_subpaths()])
        improved = True
        while improved:
            improved = False
            for j in range(len(subpaths)):
                for k in range(j + 1, len(subpaths)):
                    new_cut = CutPlanner.delta_distance(subpaths, j, k)
                    if new_cut < 0:
                        CutPlanner.cross(subpaths, j, k)
                        improved = True
        for p in subpaths:
            optimized += p
        return optimized

    @staticmethod
    def cross(subpaths, j, k):
        """
        Reverses subpaths flipping the individual elements from position j inclusive to
        k exclusive.
        :param subpaths:
        :param j:
        :param k:
        :return:
        """
        for q in range(j, k):
            subpaths[q].direct_close()
            subpaths[q].reverse()
        subpaths[j:k] = subpaths[j:k][::-1]

    @staticmethod
    def delta_distance(subpaths, j, k):
        distance = 0.0
        k -= 1
        a1 = subpaths[j][0].end
        b0 = subpaths[k][-1].end
        if k < len(subpaths) - 1:
            b1 = subpaths[k + 1][0].end
            d = Point.distance(b0, b1)
            distance -= d
            d = Point.distance(a1, b1)
            distance += d
        if j > 0:
            a0 = subpaths[j - 1][-1].end
            d = Point.distance(a0, a1)
            distance -= d
            d = Point.distance(a0, b0)
            distance += d
        return distance

    @staticmethod
    def distance_path(subpaths):
        distance = 0.0
        for s in range(len(subpaths) - 1):
            j = subpaths[s]
            k = subpaths[s + 1]
            d = Point.distance(j[-1].end, k[0].end)
            distance += d
        return distance

    @staticmethod
    def is_order_constrained(paths, constraints, j, k):
        """Is the order of the sequences between j and k constrained. Such that reversing this order will violate
        the constraints."""
        for q in range(j, k):
            # search between j and k.
            first_path = paths[q]
            for constraint in constraints:
                if first_path is not constraint[0]:
                    # Constraint does not apply to the value at q.
                    continue
                for m in range(q + 1, k):
                    second_path = paths[m]
                    if second_path is constraint[1]:
                        # Constraint demands the order must be first_path then second_path.
                        return True
        return False

    @staticmethod
    def optimize_general(paths):
        optimized = Path()
        if isinstance(paths, Path):
            paths = [paths]
        subpaths = []
        for path in paths:
            subpaths.extend([abs(Path(s)) for s in path.as_subpaths()])
        constraints = []
        for j in range(len(subpaths)):
            for k in range(j + 1, len(subpaths)):
                if CutPlanner.is_inside(subpaths[k], subpaths[j]):
                    constraints.append((subpaths[k], subpaths[j]))
                elif CutPlanner.is_inside(subpaths[j], subpaths[k]):
                    constraints.append((subpaths[j], subpaths[k]))
        for j in range(len(subpaths)):
            for k in range(j + 1, len(subpaths)):
                if CutPlanner.is_inside(subpaths[k], subpaths[j]):
                    t = subpaths[j]
                    subpaths[j] = subpaths[k]
                    subpaths[k] = t
        # for constraint in constraints:
        #     success = False
        #     for q in range(len(subpaths)):
        #         first_path = subpaths[q]
        #         if first_path is constraint[0]:
        #             for m in range(q, len(subpaths)):
        #                 second_path = subpaths[m]
        #                 if second_path is constraint[1]:
        #                     success = True
        improved = True
        while improved:
            improved = False
            for j in range(len(subpaths)):
                for k in range(j + 1, len(subpaths)):
                    new_cut = CutPlanner.delta_distance(subpaths, j, k)
                    if new_cut < 0:
                        if CutPlanner.is_order_constrained(subpaths, constraints, j, k):
                            # Our order is constrained. Performing 2-opt cross is disallowed.
                            continue
                        CutPlanner.cross(subpaths, j, k)
                        improved = True
        for p in subpaths:
            optimized += p
            try:
                del p.vm
            except AttributeError:
                pass
            try:
                del p.bounding_box
            except AttributeError:
                pass
        return optimized


class GraphNode(Point):
    def __init__(self, x, y=None):
        Point.__init__(self, x, y)
        self.connections = []
        self.visited = 0


class Segment:
    def __init__(self, a, b, index=0):
        self.visited = 0
        self.a = a
        self.b = b
        self.active = False
        self.value = 'RUNG'
        self.index = index
        self.bisectors = []
        self.object = None

    def __len__(self):
        # [False, i, p0, p1, high, low, m, b, path]
        return 9

    def __getitem__(self, item):
        if item == 0:
            return self.active
        if item == 1:
            return self.index
        if item == 2:
            return self.a
        if item == 3:
            return self.b
        if item == 4:
            if self.a.y > self.b.y:
                return self.a
            else:
                return self.b
        if item == 5:
            if self.a.y < self.b.y:
                return self.a
            else:
                return self.b
        if item == 6:
            if self.b[0] - self.a[0] == 0:
                return float('inf')
            return (self.b[1] - self.a[1]) / (self.b[0] - self.a[0])
        if item == 7:
            if self.b[0] - self.a[0] == 0:
                return float('inf')
            im = (self.b[1] - self.a[1]) / (self.b[0] - self.a[0])
            return self.a[1] - (im * self.a[0])
        if item == 8:
            return self.object

    def intersect(self, segment):
        return Segment.line_intersect(self.a[0], self.a[1], self.b[0], self.b[1],
                                      segment.a[0], segment.a[1], segment.b[0], segment.b[1],)

    def sort_bisectors(self):
        def distance(a):
            return self.a.distance_to(a)

        self.bisectors.sort(key=distance)

    def get_intercept(self, y):
        im = (self.b[1] - self.a[1]) / (self.b[0] - self.a[0])
        ib = self.a[1] - (im * self.a[0])
        if isnan(im) or isinf(im):
            return self.a[0]
        return (y - ib) / im

    @staticmethod
    def line_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if denom == 0:
            return None  # Parallel.
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
        if 0.0 <= ua <= 1.0 and 0.0 <= ub <= 1.0:
            return (x1 + ua * (x2 - x1)), (y1 + ua * (y2 - y1))
        return None


class Graph:
    """
    If the graph is fully Eulerian then there should be an even number of input nodes.

    These nodes are treated such that even nodes are input and odd nodes are output nodes.

    If partially Eulerian and odd, then the final node is the start or end node.

    If setup as a circuit then each node should link input to output effectively.

    If a graph is outline, it will be in order, from a to b for each edge, and looped.
    """
    def __init__(self):
        self.nodes = []
        self.links = []

    def add_shape(self, series, close=True):
        first_node = None
        last_node = None
        for i in range(len(series)):
            m = series[i]
            current_node = self.new_node(m)
            if i == 0:
                first_node = current_node
            if last_node is not None:
                segment = self.link(last_node, current_node)
                segment.index = i
                segment.value = 'EDGE'
            last_node = current_node
        if close:
            segment = self.link(last_node, first_node)
            segment.index = len(series)
            segment.value = 'EDGE'

    @staticmethod
    def monotone_fill(graph, outlines, min, max, distance):
        crawler = VectorMontonizer(low_value=min, high_value=max, start=min)
        for outline in outlines:
            crawler.add_segments(outline.links)
        itr = 0
        while crawler.valid_range():
            crawler.next_intercept(distance)
            crawler.sort_actives()
            y = crawler.current

            for i in range(1, len(crawler.actives), 2):
                left_segment = crawler.actives[i-1]
                right_segment = crawler.actives[i]
                left_segment_x = crawler.intercept(left_segment, y)
                right_segment_x = crawler.intercept(right_segment, y)
                left_node = graph.new_node((left_segment_x, y))
                right_node = graph.new_node((right_segment_x, y))
                row = graph.link(left_node, right_node)
                row.value = 'RUNG'
                row.index = itr
                left_segment.bisectors.append(left_node)
                right_segment.bisectors.append(right_node)
            itr += 1
        for outline in outlines:
            itr = 0
            current = None
            previous = None
            for i in range(len(outline.links)):
                s = outline.links[i]
                if len(s.bisectors) == 0:
                    continue
                s.sort_bisectors()
                for bi in s.bisectors:
                    if previous is not None:
                        segment = graph.link(previous, bi)
                        segment.value = 'EDGE'
                        segment.index = itr
                        itr += 1
                    else:
                        current = bi
                    previous = bi
                s.bisectors.clear()
            if current is not None and previous is not None:
                segment = graph.link(previous, current)
                segment.value = 'EDGE'
                segment.index = itr

    def new_node(self, point):
        g = GraphNode(point)
        self.nodes.append(g)
        return g

    def new_edge(self, a, b):
        s = Segment(a, b)
        self.links.append(s)
        return s

    def detach(self, segment):
        self.links.remove(segment)
        segment.a.connections.remove(segment)
        segment.b.connections.remove(segment)

    def link(self, a, b):
        segment = self.new_edge(a, b)
        segment.a.connections.append(segment)
        segment.b.connections.append(segment)
        return segment

    def double(self):
        """
        Makes any graph Eulerian. Any graph that is doubled is by definition Eulerian.
        :return:
        """
        for i in range(len(self.links)):
            s = self.links[i]
            second_copy = self.link(s.a, s.b)
            if s.value == 'RUNG':
                second_copy.value = 'SCAFFOLD_RUNG'
            else:
                second_copy.value = 'SCAFFOLD'
            second_copy.index = None

    def double_odd_edge(self):
        """
        Makes any outline path a Eularian path.
        :return:
        """
        for i in range(len(self.links)):
            segment = self.links[i]
            if segment.value == 'EDGE' and segment.index & 1:
                second_copy = self.link(segment.a, segment.b)
                second_copy.value = 'SCAFFOLD'
                second_copy.index = None

    def walk(self, points):
        if len(self.nodes) == 0:
            return
        walker = GraphWalker(self)
        walker.make_walk()
        walker.clip_scaffold_ends()
        walker.clip_scaffold_loops()
        walker.add_walk(points)
        return points

    def is_eulerian(self):
        ends = 0
        for n in self.nodes:
            if len(n.connections) & 1:
                ends += 1
                if ends > 2:
                    return False
        return True

    def is_euloopian(self):
        for n in self.nodes:
            if len(n.connections) & 1:
                return False
        return True


class GraphWalker:
    """
    Graph Walker takes a graph object and finds walks within it.

    If the graph is discontinuous it will find no segment between these elements and add a blank segment between them.
    """
    def __init__(self, graph):
        self.graph = graph
        self.walk = list()
        self.flip_start = None
        self.flip_end = None

    def other_node_for_segment(self, current_node, next_segment):
        if current_node is next_segment.a:
            return next_segment.b
        else:
            return next_segment.a

    def reset_visited(self):
        for e in self.walk:
            if e is None:
                continue
            e.visited = 0

    def make_walk(self):
        itr = 0
        for g in self.graph.nodes:
            if not g.visited:
                if itr != 0:
                    self.walk.append(None)  # Segment is None. There is no link here.
                self.make_walk_node(g)
                itr += 1

    def make_walk_node(self, g):
        """
        Starting from the given start node it makes a complete walk in a Eulerian circuit.

        It adds the first loop from the start node, then walks its looped walk adding
        any additional loops it finds to the current loop.
        :param g:
        :return:
        """
        start = len(self.walk)
        self.walk.append(g)
        g.visited += 1
        self.add_loop(start, g)

        i = start
        while i < len(self.walk):
            node = self.walk[i]
            unused = self.find_unused_connection(node)
            if unused is None:
                i += 2
                continue
            i += self.add_loop(i, node)
            i += 2

    def add_loop(self, index, node):
        """
        Adds a loop from the current graphnode, without revisiting any nodes.
        Returns the altered index caused by adding that loop.

        Travels along unused connections until no more travel is possible. If properly Eulerian,
        this will only happen when it is looped back on itself.

        :param index: index we are adding loop to.
        :param node: Node to find alternative path through.
        :return: new index after loop is added to the walk.
        """
        index += 1
        i = index
        while True:
            unused = self.find_unused_connection(node)
            if unused is None:
                break
            segment = node.connections[unused]
            self.walk.insert(i, segment)
            i += 1
            node.visited += 1
            segment.visited += 1
            node = self.other_node_for_segment(node, segment)
            self.walk.insert(i, node)
            i += 1
        return i - index

    def find_unused_connection(self, node):
        """
        Finds the first unused edge segment within the graph node, or None if all connections are used.

        :param node: Node to find unused edge segment within.
        :return: index of node connection within the graphnode
        """
        value = None
        for index, c in enumerate(node.connections):
            if not c.visited:
                if value is None:
                    value = index
                if c.value == 'RUNG':
                    return index
        return value

    def add_walk(self, points):
        """
        Adds nodes within the walk to the points given to it.

        If there is an unconnected section, it will simply create a link across where no link exists.
        :param points:
        :return:
        """
        for i in range(0, len(self.walk), 2):
            if i + 1 != len(self.walk):
                if self.walk[i+1] is None:
                    points.append(None)
            points.append(self.walk[i])

    def remove_loop(self, from_pos, to_pos):
        """
        Removes values between the two given points.
        Since start and end are the same node, it leaves one in place.

        :param from_pos:
        :param to_pos:
        :return:
        """
        if from_pos == to_pos:
            return 0
        min_pos = min(from_pos, to_pos)
        max_pos = max(from_pos, to_pos)
        del self.walk[min_pos:max_pos]
        return max_pos - min_pos

    def remove_biggest_loop_in_range(self, start, end):
        """
        Checks scaffolding walk for loops, and removes them if detected.

        It resets the visited values for the scaffold walk.
        It iterates from the outside to the center, setting the visited value for each node.

        If it finds a marked node, that is the biggest loop within the given walk.
        :param start:
        :param end:
        :return:
        """
        for i in range(start, end+2, 2):
            n = self.get_node(i)
            n.visited = None
        for i in range(0, int((end-start)//2), 2):
            left = start + i
            right = end - i
            s = self.get_node(left)
            if s.visited is not None:
                return self.remove_loop(left, s.visited)
                # Loop Detected.
            if left == right:
                break
            s.visited = left
            e = self.get_node(right)
            if e.visited is not None:
                return self.remove_loop(right, e.visited)
                # Loop Detected.
            e.visited = right
        return 0

    def clip_scaffold_loops(self):
        """
        Removes loops consisting of scaffolding from the walk.

        Clips unneeded scaffolding.

        :return:
        """
        start = 0
        index = 0
        ie = len(self.walk)
        while index < ie:
            segment = None
            try:
                segment = self.walk[index+1]
            except IndexError:
                self.remove_biggest_loop_in_range(start, index)
                return
            if segment is None or segment.value == 'RUNG':
                # Segment is essential.
                if start != index:
                    ie -= self.remove_biggest_loop_in_range(start, index)
                start = index + 2
            index += 2

    def remove_scaffold_ends_in_range(self, start, end):
        current = end - start
        new_end = end
        limit = start + 2
        while new_end >= limit:
            j_segment = self.walk[new_end - 1]
            if j_segment is None or j_segment.value == 'RUNG':
                if new_end == end:
                    break
                del self.walk[new_end + 1:end+1]
                end = new_end
                break
            new_end -= 2
        new_start = start
        limit = end - 2
        while new_start <= limit:
            j_segment = self.walk[new_start+1]
            if j_segment is None or j_segment.value == 'RUNG':
                if new_start == start:
                    break
                del self.walk[start:new_start]
                start = new_start
                break
            new_start += 2

    def clip_scaffold_ends(self):
        """Finds contiguous regions, and calls removeScaffoldEnds on that range."""
        end = len(self.walk) - 1
        index = end
        while index >= 0:
            segment = None
            try:
                segment = self.walk[index - 1]
            except IndexError:
                self.remove_scaffold_ends_in_range(index, end)
                return
            if segment is None:
                self.remove_scaffold_ends_in_range(index, end)
                end = index - 2
            index -= 2

    def two_opt(self):
        v = self.get_value()
        while True:
            new_value = self.two_opt_cycle(v)
            if v == new_value:
                break

    def two_opt_cycle(self, value):
        if len(self.walk) == 0:
            return 0
        swap_start = 0
        walk_end = len(self.walk)
        while swap_start < walk_end:
            swap_element = self.walk[swap_start]
            m = swap_element.visited
            swap_end = swap_start + 2
            while swap_end < walk_end:
                current_element = self.walk[swap_end]
                if swap_element == current_element:
                    m -= 1
                    self.flip_start = swap_start + 1
                    self.flip_end = swap_end - 1
                    new_value = self.get_value()
                    if new_value > value:
                        value = new_value
                        self.walk[swap_start+1:swap_end] = self.walk[swap_start+1:swap_end:-1]  # reverse
                    else:
                        self.flip_start = None
                        self.flip_end = None
                    if m == 0:
                        break
                swap_end += 2
            swap_start += 2
        return value

    def get_segment(self, index):
        if self.flip_start is not None and \
                self.flip_end is not None and \
                self.flip_start <= index <= self.flip_end:
            return self.walk[self.flip_end - (index - self.flip_start)]
        return self.walk[index]

    def get_node(self, index):
        if self.flip_start is not None and \
                self.flip_end is not None and \
                self.flip_start <= index <= self.flip_end:
            return self.walk[self.flip_end - (index - self.flip_start)]
        try:
            return self.walk[index]
        except IndexError:
            return None

    def get_value(self):
        """
        Path values with flip.
        :return: Flipped path value.
        """
        if len(self.walk) == 0:
            return 0
        value = 0
        start = 0
        end = len(self.walk) - 1
        while start < end:
            i_segment = self.get_segment(start+1)
            if i_segment.value == 'RUNG':
                break
            start += 2
        while end >= 2:
            i_segment = self.get_segment(end-1)
            if i_segment.value == 'RUNG':
                break
            end -= 2
        j = start
        while j < end:
            j_node = self.get_node(j)
            j += 1
            j_segment = self.get_segment(j)
            j += 1
            if j_segment.value != 'RUNG':
                # if the node connector is not critical, try to find and skip a loop
                k = j
                while k < end:
                    k_node = self.get_node(k)
                    k += 1
                    k_segment = self.get_segment(k)
                    k += 1
                    if k_segment.value == 'RUNG':
                        break
                    if k_node == j_node:
                        # Only skippable nodes existed before returned to original node, so skip that loop.
                        value += (k - j) * 10
                        j = k
                        j_node = k_node
                        j_segment = k_segment
                        break
            if j_segment.value == 'SCAFFOLD':
                value -= j_segment.a.distance_sq(j_segment.b)
            elif j_segment.value == 'RUNG':
                value -= j_segment.a.distance_sq(j_segment.b)
        return value


class EulerianFill:
    def __init__(self, distance):
        self.distance = distance

    def get_fill(self, points):
        outline_graph = Graph()
        outline_graph.add_shape(points, True)
        graph = Graph()
        min_y = min([p[1] for p in points])
        max_y = max([p[1] for p in points])
        Graph.monotone_fill(graph, [outline_graph], min_y, max_y, self.distance)
        graph.double_odd_edge()
        walk = list()
        graph.walk(walk)
        return walk


class VectorMontonizer:
    def __init__(self, low_value=-float('inf'), high_value=float(inf), start=-float('inf')):
        self.clusters = []
        self.dirty_cluster_sort = True

        self.actives = []
        self.dirty_actives_sort = True

        self.current = start
        self.dirty_cluster_position = True

        self.valid_low_value = low_value
        self.valid_high_value = high_value
        self.cluster_range_index = 0
        self.cluster_low_value = float('inf')
        self.cluster_high_value = -float('inf')

    def add_segments(self, links):
        self.dirty_cluster_position = True
        self.dirty_cluster_sort = True
        self.dirty_actives_sort = True
        for s in links:
            self.clusters.append((s[4].y, s))  # High
            self.clusters.append((s[5].y, s))  # Low

    def add_cluster(self, path):
        self.dirty_cluster_position = True
        self.dirty_cluster_sort = True
        self.dirty_actives_sort = True
        for i in range(len(path) - 1):
            p0 = path[i]
            p1 = path[i + 1]
            if p0.y > p1.y:
                high = p0
                low = p1
            else:
                high = p1
                low = p0
            try:
                m = (high.y - low.y) / (high.x - low.x)
            except ZeroDivisionError:
                m = float('inf')

            b = low.y - (m * low.x)
            if self.valid_low_value > high.y:
                continue  # Cluster before range.
            if self.valid_high_value < low.y:
                continue  # Cluster after range.
            cluster = Segment(p0, p1)
            # cluster = [False, i, p0, p1, high, low, m, b, path]
            if self.valid_low_value < low.y:
                self.clusters.append((low.y, cluster))
            if self.valid_high_value > high.y:
                self.clusters.append((high.y, cluster))
            if high.y >= self.current >= low.y:
                cluster.active = True
                self.actives.append(cluster)

    def valid_range(self):
        return self.valid_high_value >= self.current >= self.valid_low_value

    def next_intercept(self, delta):
        self.scanline(self.current + delta)
        self.sort_actives()
        return self.valid_range()

    def sort_clusters(self):
        if not self.dirty_cluster_sort:
            return
        self.clusters.sort(key=lambda e: e[0])
        self.dirty_cluster_sort = False

    def sort_actives(self):
        if not self.dirty_actives_sort:
            return
        self.actives.sort(key=self.intercept)
        self.dirty_actives_sort = False

    def intercept(self, e, y=None):
        if y is None:
            y = self.current
        m = e[6]
        b = e[7]
        if m == float('nan') or m == float('inf'):
            low = e[5]
            return low.x
        return (y - b) / m

    def find_cluster_position(self):
        if not self.dirty_cluster_position:
            return
        self.dirty_cluster_position = False
        self.sort_clusters()

        self.cluster_range_index = -1
        self.cluster_high_value = -float('inf')
        self.increment_cluster()

        while self.is_higher_than_cluster_range(self.current):
            self.increment_cluster()

    def in_cluster_range(self, v):
        return not self.is_lower_than_cluster_range(v) and not self.is_higher_than_cluster_range(v)

    def is_lower_than_cluster_range(self, v):
        return v < self.cluster_low_value

    def is_higher_than_cluster_range(self, v):
        return v > self.cluster_high_value

    def increment_cluster(self):
        self.cluster_range_index += 1
        self.cluster_low_value = self.cluster_high_value
        if self.cluster_range_index < len(self.clusters):
            self.cluster_high_value = self.clusters[self.cluster_range_index][0]
        else:
            self.cluster_high_value = float('inf')
        if self.cluster_range_index > 0:
            return self.clusters[self.cluster_range_index - 1][1]
        else:
            return None

    def decrement_cluster(self):
        self.cluster_range_index -= 1
        self.cluster_high_value = self.cluster_low_value
        if self.cluster_range_index > 0:
            self.cluster_low_value = self.clusters[self.cluster_range_index - 1][0]
        else:
            self.cluster_low_value = -float('inf')
        return self.clusters[self.cluster_range_index][1]

    def is_point_inside(self, x, y):
        self.scanline(y)
        self.sort_actives()
        for i in range(1, len(self.actives), 2):
            prior = self.actives[i - 1]
            after = self.actives[i]
            if self.intercept(prior, y) <= x <= self.intercept(after, y):
                return True
        return False

    def scanline(self, scan):
        self.dirty_actives_sort = True
        self.sort_clusters()
        self.find_cluster_position()

        while self.is_lower_than_cluster_range(scan):
            c = self.decrement_cluster()
            if c.active:
                c.active = False
                self.actives.remove(c)
            else:
                c.active = True
                self.actives.append(c)

        while self.is_higher_than_cluster_range(scan):
            c = self.increment_cluster()
            if c.active:
                c.active = False
                self.actives.remove(c)
            else:
                c.active = True
                self.actives.append(c)

        self.current = scan
