
from algorithms.graph_algorithms import (
    dijkstra,
    reconstruct_path,
    bfs,
)

GRAPH = {
    "A": [("B", 2), ("C", 4)],
    "B": [("A", 2), ("C", 1), ("D", 5)],
    "C": [("A", 4), ("B", 1), ("D", 2)],
    "D": [("B", 5), ("C", 2)],
}


def test_shortest_distance():
    distances, _ = dijkstra(GRAPH, "A")
    assert distances["D"] == 5


def test_shortest_route():
    _, previous = dijkstra(GRAPH, "A")
    assert reconstruct_path(previous, "A", "D") == [
        "A", "B", "C", "D"
    ]


def test_bfs_connectivity():
    assert bfs(GRAPH, "A") == {"A", "B", "C", "D"}


def test_unreachable_node():
    graph = {"A": [("B", 2)], "B": [("A", 2)], "X": []}
    distances, previous = dijkstra(graph, "A")

    assert distances["X"] == float("inf")
    assert reconstruct_path(previous, "A", "X") == []
