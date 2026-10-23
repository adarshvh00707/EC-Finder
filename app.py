
import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from algorithms.graph_algorithms import rank_stations, bfs

app = Flask(__name__)

DATA_FILE = Path(__file__).parent / "data" / "network.json"

with DATA_FILE.open(encoding="utf-8") as file:
    DATA = json.load(file)

GRAPH = DATA["graph"]
STATIONS = DATA["stations"]


def get_number(name, default, minimum, maximum):
    """Parse and validate a numeric query parameter."""
    try:
        value = float(request.args.get(name, default))
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number")

    if not minimum <= value <= maximum:
        raise ValueError(
            f"{name} must be between {minimum} and {maximum}"
        )

    return value


@app.get("/")
def home():
    return render_template(
        "index.html",
        nodes=sorted(GRAPH.keys())
    )


@app.get("/api/stations")
def find_stations():
    start = request.args.get("start", "A")
    connector = request.args.get("connector", "").strip() or None
    ranking = request.args.get("ranking", "balanced").lower()

    if start not in GRAPH:
        return jsonify({"error": "Invalid starting junction"}), 400

    try:
        battery_capacity = get_number(
            "battery_capacity", 60, 1, 300
        )
        soc = get_number("soc", 80, 0, 100)
        consumption = get_number("consumption", 18, 1, 100)
        reserve = get_number("reserve", 10, 0, 100)
        target_soc = get_number("target_soc", 80, 1, 100)
        min_power = get_number("min_power", 0, 0, 1000)

        if reserve > soc:
            raise ValueError("Reserve SOC cannot exceed current SOC")

        if ranking not in {"distance", "cost", "balanced"}:
            raise ValueError("Invalid ranking mode")

        stations = rank_stations(
            GRAPH,
            STATIONS,
            start,
            connector=connector,
            min_power=min_power,
            ranking=ranking,
            battery_capacity=battery_capacity,
            soc=soc,
            consumption=consumption,
            reserve=reserve,
            target_soc=target_soc,
        )

        return jsonify({
            "start": start,
            "ranking": ranking,
            "battery": {
                "capacity_kwh": battery_capacity,
                "soc_percent": soc,
                "consumption_kwh_per_100km": consumption,
                "reserve_percent": reserve,
                "target_soc_percent": target_soc,
            },
            "count": len(stations),
            "reachable_count": sum(
                station["reachable"] for station in stations
            ),
            "stations": stations,
        })

    except ValueError as error:
        return jsonify({"error": str(error)}), 400


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
from flask import send_from_directory

@app.get("/service-worker.js")
def service_worker():
    response = send_from_directory(
        app.static_folder,
        "service-worker.js",
        mimetype="application/javascript"
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response

