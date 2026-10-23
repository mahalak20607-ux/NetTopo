
import json
import networkx as nx


DEVICE_TYPES = ["Computer", "Router", "Switch"]


def create_sample_network():
    """Create an example network for the first dashboard launch."""
    graph = nx.Graph()

    devices = [
        ("PC1", "Computer"),
        ("R1", "Router"),
        ("SW1", "Switch"),
        ("PC2", "Computer"),
        ("R2", "Router"),
    ]

    for name, device_type in devices:
        graph.add_node(name, device_type=device_type)

    links = [
        ("PC1", "SW1", 2),
        ("SW1", "R1", 1),
        ("R1", "R2", 3),
        ("R2", "PC2", 2),
        ("SW1", "PC2", 8),
    ]

    for source, target, cost in links:
        graph.add_edge(source, target, cost=cost)

    return graph


def add_device(graph, name, device_type):
    name = name.strip()

    if not name:
        raise ValueError("Device name cannot be empty.")

    if device_type not in DEVICE_TYPES:
        raise ValueError("Choose a valid device type.")

    if name in graph:
        raise ValueError(f"Device '{name}' already exists.")

    graph.add_node(name, device_type=device_type)


def connect_devices(graph, source, target, cost):
    if source not in graph or target not in graph:
        raise ValueError("Both devices must exist.")

    if source == target:
        raise ValueError("A device cannot connect to itself.")

    if cost <= 0:
        raise ValueError("Link cost must be greater than zero.")

    graph.add_edge(source, target, cost=int(cost))


def get_shortest_path(graph, source, target):
    if source not in graph or target not in graph:
        raise ValueError("Choose valid source and destination devices.")

    if not nx.has_path(graph, source, target):
        return None, None

    path = nx.dijkstra_path(graph, source, target, weight="cost")
    total_cost = nx.dijkstra_path_length(
        graph, source, target, weight="cost"
    )

    return path, total_cost


def export_network(graph):
    """Return a JSON-serializable network configuration."""
    return {
        "devices": [
            {
                "name": name,
                "type": attributes.get("device_type", "Computer"),
            }
            for name, attributes in graph.nodes(data=True)
        ],
        "connections": [
            {
                "source": source,
                "target": target,
                "cost": attributes.get("cost", 1),
            }
            for source, target, attributes in graph.edges(data=True)
        ],
    }


def export_json(graph):
    return json.dumps(export_network(graph), indent=2)
