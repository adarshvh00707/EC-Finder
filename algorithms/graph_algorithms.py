
import heapq
from collections import deque


def dijkstra(graph, start):
    """Calculate shortest distances and predecessor nodes."""
    if start not in graph:
        raise ValueError(f"Unknown starting node: {start}")

    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    distances[start] = 0
    queue = [(0, start)]

    while queue:
        distance, node = heapq.heappop(queue)

        if distance > distances[node]:
            continue

        for neighbour, weight in graph[node]:
            if weight < 0:
                raise ValueError("Negative edge weights are not supported")

            new_distance = distance + weight

            if new_distance < distances[neighbour]:
                distances[neighbour] = new_distance
                previous[neighbour] = node
                heapq.heappush(queue, (new_distance, neighbour))

    return distances, previous


def reconstruct_path(previous, start, target):
    """Reconstruct a shortest path."""
    if target not in previous:
        return []

    path = []
    node = target

    while node is not None:
        path.append(node)
        if node == start:
            return path[::-1]
        node = previous[node]

    return []


def bfs(graph, start):
    """Find every node reachable from start."""
    if start not in graph:
        raise ValueError(f"Unknown starting node: {start}")

    visited = {start}
    queue = deque([start])

    while queue:
        node = queue.popleft()

        for neighbour, _ in graph[node]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)

    return visited


def rank_stations(graph, stations, start, connector=None):
    """Rank available compatible stations by shortest distance."""
    distances, previous = dijkstra(graph, start)
    results = []

    for station in stations:
        node = station["node"]

        if station["available_ports"] <= 0:
            continue

        if connector and connector not in station["connectors"]:
            continue

        if node not in distances or distances[node] == float("inf"):
            continue

        results.append({
            **station,
            "distance_km": round(distances[node], 2),
            "route": reconstruct_path(previous, start, node)
        })

    results.sort(
        key=lambda station: (
            station["distance_km"],
            station["price_per_kwh"]
        )
    )

    return results
