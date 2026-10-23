
import streamlit as st
import networkx as nx
import plotly.graph_objects as go

from topology import (
    DEVICE_TYPES,
    add_device,
    connect_devices,
    create_sample_network,
    export_json,
    get_shortest_path,
)

st.set_page_config(
    page_title="NetTopo | Network Simulator",
    page_icon="🌐",
    layout="wide",
)

if "network" not in st.session_state:
    st.session_state.network = create_sample_network()

if "notice" not in st.session_state:
    st.session_state.notice = None

if "route" not in st.session_state:
    st.session_state.route = None


def show_topology(graph, route=None):
    """Draw devices and weighted links using Plotly."""
    if graph.number_of_nodes() == 0:
        st.info("No devices available. Add a device to begin.")
        return

    positions = nx.spring_layout(graph, seed=42, weight="cost")

    route_edges = set()
    if route and len(route) > 1:
        route_edges = {
            frozenset((route[i], route[i + 1]))
            for i in range(len(route) - 1)
        }

    normal_x, normal_y = [], []
    route_x, route_y = [], []
    edge_labels = []

    for source, target, attrs in graph.edges(data=True):
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        edge_key = frozenset((source, target))

        if edge_key in route_edges:
            route_x.extend([x1, x2, None])
            route_y.extend([y1, y2, None])
        else:
            normal_x.extend([x1, x2, None])
            normal_y.extend([y1, y2, None])

        edge_labels.append({
            "x": (x1 + x2) / 2,
            "y": (y1 + y2) / 2,
            "text": str(attrs.get("cost", 1)),
        })

    figure = go.Figure()

    figure.add_trace(go.Scatter(
        x=normal_x,
        y=normal_y,
        mode="lines",
        line=dict(color="#64748b", width=2),
        hoverinfo="skip",
        name="Connections",
    ))

    figure.add_trace(go.Scatter(
        x=route_x,
        y=route_y,
        mode="lines",
        line=dict(color="#22c55e", width=5),
        hoverinfo="skip",
        name="Shortest path",
    ))

    colors = {
        "Computer": "#38bdf8",
        "Router": "#a78bfa",
        "Switch": "#fbbf24",
    }

    node_x, node_y, node_text, node_colors = [], [], [], []

    for node, attrs in graph.nodes(data=True):
        x, y = positions[node]
        device_type = attrs.get("device_type", "Computer")

        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br>{device_type}")
        node_colors.append(colors.get(device_type, "#94a3b8"))

    figure.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=list(graph.nodes()),
        textposition="bottom center",
        customdata=node_text,
        hovertemplate="%{customdata}<extra></extra>",
        marker=dict(
            size=34,
            color=node_colors,
            line=dict(color="#ffffff", width=1.5),
        ),
        name="Devices",
    ))

    for label in edge_labels:
        figure.add_annotation(
            x=label["x"],
            y=label["y"],
            text=label["text"],
            showarrow=False,
            bgcolor="white",
            bordercolor="#cbd5e1",
            borderpad=3,
            font=dict(size=11, color="#111827"),
        )

    figure.update_layout(
        title="Network Topology Map",
        height=520,
        template="plotly_dark",
        showlegend=True,
        margin=dict(l=20, r=20, t=55, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    st.plotly_chart(figure, use_container_width=True)


# Sidebar
st.sidebar.title("🌐 NetTopo")
st.sidebar.caption("Network Topology Simulator")
st.sidebar.markdown("---")
st.sidebar.write("Manage devices and network links below.")

if st.sidebar.button("Reset sample network", use_container_width=True):
    st.session_state.network = create_sample_network()
    st.session_state.route = None
    st.session_state.notice = ("success", "Sample network restored.")
    st.rerun()

graph = st.session_state.network

# Header
st.title("🌐 NetTopo")
st.subheader("Interactive Network Topology Simulator")
st.caption(
    "Create network devices, connect links, and calculate "
    "the lowest-cost route using Dijkstra's algorithm."
)

notice = st.session_state.notice
if notice:
    level, message = notice
    if level == "success":
        st.success(message)
    else:
        st.error(message)
    st.session_state.notice = None

# Metrics
devices = graph.number_of_nodes()
links = graph.number_of_edges()
components = nx.number_connected_components(graph) if devices else 0

m1, m2, m3 = st.columns(3)
m1.metric("Network Devices", devices)
m2.metric("Connections", links)
m3.metric("Connected Components", components)

st.markdown("---")

# Main graph
left, right = st.columns([1.7, 1])

with left:
    st.subheader("Network Visualization")
    show_topology(graph, st.session_state.route)

    st.caption(
        "Blue = Computer | Purple = Router | Yellow = Switch | "
        "Green = selected shortest path"
    )

with right:
    st.subheader("Network Overview")

    if devices:
        rows = [
            {
                "Device": name,
                "Type": attrs.get("device_type", "Computer"),
                "Connections": graph.degree(name),
            }
            for name, attrs in graph.nodes(data=True)
        ]
        st.dataframe(
            rows,
            hide_index=True,
            use_container_width=True,
        )

    st.subheader("Link Details")

    if links:
        edge_rows = [
            {"From": u, "To": v, "Cost": d.get("cost", 1)}
            for u, v, d in graph.edges(data=True)
        ]
        st.dataframe(
            edge_rows,
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No connections have been added.")

st.markdown("---")
st.header("Manage Your Network")

tab_add, tab_connect, tab_remove, tab_route = st.tabs([
    "➕ Add Device",
    "🔗 Connect Devices",
    "🗑️ Remove Device",
    "🧭 Shortest Path",
])

with tab_add:
    with st.form("add_device_form"):
        device_name = st.text_input(
            "Device name",
            placeholder="Example: PC3",
        )
        device_type = st.selectbox("Device type", DEVICE_TYPES)

        submitted = st.form_submit_button(
            "Add Device",
            use_container_width=True,
        )

        if submitted:
            try:
                add_device(graph, device_name, device_type)
                st.session_state.route = None
                st.session_state.notice = (
                    "success",
                    f"Device '{device_name.strip()}' added successfully.",
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

with tab_connect:
    node_names = sorted(graph.nodes())

    if len(node_names) < 2:
        st.info("Add at least two devices before connecting them.")
    else:
        with st.form("connect_form"):
            source = st.selectbox("Source device", node_names)
            target = st.selectbox(
                "Destination device",
                node_names,
                index=1,
            )
            cost = st.number_input(
                "Link cost (positive integer)",
                min_value=1,
                max_value=100000,
                value=1,
                step=1,
            )

            submitted = st.form_submit_button(
                "Create Connection",
                use_container_width=True,
            )

            if submitted:
                try:
                    connect_devices(graph, source, target, cost)
                    st.session_state.route = None
                    st.session_state.notice = (
                        "success",
                        f"Connection {source} ↔ {target} saved.",
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

with tab_remove:
    node_names = sorted(graph.nodes())

    if not node_names:
        st.info("There are no devices to remove.")
    else:
        with st.form("remove_form"):
            remove_name = st.selectbox(
                "Select device to remove",
                node_names,
            )
            confirm = st.checkbox("Confirm device removal")

            submitted = st.form_submit_button(
                "Remove Device",
                use_container_width=True,
            )

            if submitted:
                if not confirm:
                    st.error("Please confirm the removal.")
                else:
                    graph.remove_node(remove_name)
                    st.session_state.route = None
                    st.session_state.notice = (
                        "success",
                        f"Device '{remove_name}' removed.",
                    )
                    st.rerun()

with tab_route:
    node_names = sorted(graph.nodes())

    if len(node_names) < 2:
        st.info("Add at least two devices to calculate a path.")
    else:
        source_node = st.selectbox(
            "Starting device",
            node_names,
            key="path_source",
        )
        target_node = st.selectbox(
            "Destination device",
            node_names,
            index=1,
            key="path_target",
        )

        if st.button("Calculate Shortest Path", type="primary"):
            if source_node == target_node:
                st.error("Choose two different devices.")
            else:
                try:
                    path, total_cost = get_shortest_path(
                        graph, source_node, target_node
                    )
                    if path is None:
                        st.session_state.route = None
                        st.warning(
                            "No route exists between these devices."
                        )
                    else:
                        st.session_state.route = path
                        st.success("Shortest path found!")
                        st.write(" → ".join(path))
                        st.metric("Total Path Cost", total_cost)
                        st.rerun()
                except (ValueError, nx.NetworkXNoPath) as exc:
                    st.error(str(exc))

st.markdown("---")

st.subheader("Export Network Configuration")
st.download_button(
    "⬇️ Download Network JSON",
    data=export_json(graph),
    file_name="network_topology.json",
    mime="application/json",
)

st.caption(
    "Academic simulation only. Link costs are user-defined values; "
    "they do not represent measured real-world latency."
)
