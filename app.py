
import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from algorithms.graph_algorithms import rank_stations, bfs

app = Flask(__name__)

data_path = Path(__file__).parent / "data" / "network.json"

with data_path.open(encoding="utf-8") as file:
    data = json.load(file)

GRAPH = data["graph"]
STATIONS = data["stations"]


@app.get("/")
def home():
    return render_template("index.html", nodes=sorted(GRAPH))


@app.get("/api/stations")
def find_stations():
    start = request.args.get("start", "A")
    connector = request.args.get("connector", "").strip() or None

    if start not in GRAPH:
        return jsonify({"error": "Invalid starting junction"}), 400

    results = rank_stations(GRAPH, STATIONS, start, connector)

    return jsonify({
        "start": start,
        "count": len(results),
        "stations": results
    })


@app.get("/api/reachable")
def reachable_nodes():
    start = request.args.get("start", "A")

    if start not in GRAPH:
        return jsonify({"error": "Invalid starting junction"}), 400

    return jsonify({
        "start": start,
        "reachable": sorted(bfs(GRAPH, start))
    })


if __name__ == "__main__":
    app.run(debug=True)
