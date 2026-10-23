
import heapq
from collections import deque


def dijkstra(graph, start):
    """
    Calculate shortest distances from start using Dijkstra's algorithm.

    Returns:
        distances: Shortest distance to each node.
        previous: Previous node on each shortest path.
    """
    if start not in graph:
        raise ValueError(f"Unknown starting node: {start}")

    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}

    distances[start] = 0
    priority_queue = [(0, start)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distances[current_node]:
            continue

        for neighbour, weight in graph[current_node]:
            if neighbour not in graph:
                raise ValueError(f"Unknown neighbour: {neighbour}")

            if weight < 0:
                raise ValueError("Road distances cannot be negative")

            new_distance = current_distance + weight

            if new_distance < distances[neighbour]:
                distances[neighbour] = new_distance
                previous[neighbour] = current_node

                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbour)
                )

    return distances, previous


def reconstruct_path(previous, start, target):
    """
    Reconstruct the shortest path from start to target.

    Returns an empty list if the target is unreachable.
    """
    if start not in previous or target not in previous:
        return []

    if start == target:
        return [start]

    path = []
    current_node = target

    while current_node is not None:
        path.append(current_node)

        if current_node == start:
            return path[::-1]

        current_node = previous[current_node]

    return []


def bfs(graph, start):
    """
    Find all nodes reachable from start using Breadth-First Search.
    """
    if start not in graph:
        raise ValueError(f"Unknown starting node: {start}")

    visited = {start}
    queue = deque([start])

    while queue:
        current_node = queue.popleft()

        for neighbour, _ in graph[current_node]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)

    return visited


def rank_stations(
    graph,
    stations,
    start,
    connector=None,
    min_power=0,
    ranking="balanced",
    battery_capacity=60,
    soc=80,
    consumption=18,
    reserve=10,
    target_soc=80,
):
    """
    Filter and rank EV charging stations.

    Ranking options:
        distance: shortest route first
        cost: lowest estimated charging cost first
        balanced: combined distance and cost score

    Battery estimates use a simplified energy-consumption model.
    """

    # Validate input parameters.
    if start not in graph:
        raise ValueError(f"Unknown starting node: {start}")

    if not 0 <= reserve <= soc <= 100:
        raise ValueError(
            "Require 0 <= reserve <= current SOC <= 100"
        )

    if not 0 < target_soc <= 100:
        raise ValueError(
            "Target SOC must be greater than 0 and at most 100"
        )

    if battery_capacity <= 0:
        raise ValueError("Battery capacity must be positive")

    if consumption <= 0:
        raise ValueError("Energy consumption must be positive")

    if min_power < 0:
        raise ValueError("Minimum charger power cannot be negative")

    if ranking not in {"distance", "cost", "balanced"}:
        raise ValueError(
            "Ranking must be distance, cost, or balanced"
        )

    # Find shortest routes from the starting junction.
    distances, previous = dijkstra(graph, start)

    # Energy available before reaching the reserve threshold.
    available_energy = (
        battery_capacity * (soc - reserve) / 100
    )

    results = []

    for station in stations:
        node = station["node"]

        # Exclude stations with no available charging ports.
        if station["available_ports"] <= 0:
            continue

        # Filter by connector compatibility.
        if connector and connector not in station["connectors"]:
            continue

        # Filter by minimum charger power.
        if station["power_kw"] < min_power:
            continue

        # Exclude disconnected or unknown locations.
        if node not in distances:
            continue

        if distances[node] == float("inf"):
            continue

        distance = distances[node]

        # Estimate energy required to reach the station.
        trip_energy = distance * consumption / 100

        # Check whether the station is reachable while maintaining reserve.
        reachable = trip_energy <= available_energy

        # Estimate additional energy needed to reach target SOC.
        charge_energy = max(
            0,
            battery_capacity * (target_soc - soc) / 100
        )

        # Approximate charging time at 90% charging efficiency.
        if station["power_kw"] > 0:
            charging_hours = charge_energy / (
                station["power_kw"] * 0.90
            )
        else:
            charging_hours = 0

        charging_minutes = round(charging_hours * 60)

        # Estimate cost of the additional energy.
        charging_cost = (
            charge_energy * station["price_per_kwh"]
        )

        results.append({
            **station,
            "distance_km": round(distance, 2),
            "route": reconstruct_path(
                previous,
                start,
                node
            ),
            "trip_energy_kwh": round(trip_energy, 2),
            "reachable": reachable,
            "available_energy_kwh": round(
                available_energy, 2
            ),
            "charge_energy_kwh": round(
                charge_energy, 2
            ),
            "estimated_charge_minutes": charging_minutes,
            "estimated_charge_cost": round(
                charging_cost, 2
            ),
        })

    # Normalize distance and cost so their units do not distort the score.
    if results:
        max_distance = max(
            station["distance_km"] for station in results
        ) or 1

        max_cost = max(
            station["estimated_charge_cost"]
            for station in results
        ) or 1

        for station in results:
            distance_score = (
                station["distance_km"] / max_distance
            )

            cost_score = (
                station["estimated_charge_cost"] / max_cost
            )

            if ranking == "distance":
                score = distance_score

            elif ranking == "cost":
                score = cost_score

            else:
                score = (
                    0.5 * distance_score
                    + 0.5 * cost_score
                )

            station["ranking_score"] = round(score, 3)

    # Reachable stations first, followed by the selected ranking.
    results.sort(
        key=lambda station: (
            not station["reachable"],
            station["ranking_score"],
            station["distance_km"],
        )
    )

    return results
