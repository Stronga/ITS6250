"""
Visualization Module for Distance Vector Routing Simulation.

This module defines the function for dynamically visualizing the network topology 
of routers using NetworkX and Matplotlib. It renders an interactive graph to display 
router states, link costs, and active/inactive statuses.

Modules Used:
- networkx: For creating and managing the network graph.
- matplotlib: For rendering the graph and animating updates.

Key Features:
- Real-time visualization of router activity and topology changes.
- Customizable node and edge attributes (e.g., active state, costs).
- Non-blocking interactive mode to integrate with a CLI application.

Citation:
- NetworkX Documentation: https://networkx.org/documentation/stable/index.html
- Matplotlib Animation Guide: https://matplotlib.org/stable/gallery/animation/index.html
- Python Matplotlib Documentation: https://matplotlib.org/stable/contents.html

Author: Yaw Akosah
"""

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def update_network_graph(routers):
    G = nx.Graph()

    # Add nodes and edges to the graph
    for router_name, router in routers.items():
        G.add_node(router_name, 
                   active=router.running, 
                   port=router.port)
        
        for neighbor_name, (neighbor_port, cost) in router.neighbors.items():
            if neighbor_name in routers:  # Only add if the neighbor router exists
                G.add_edge(router_name, neighbor_name, 
                           weight=cost, 
                           active=router.interfaces.get(neighbor_port, False) and routers[neighbor_name].running)

    # Define fixed positions for nodes
    pos = {
        'R10': (0, 0.5),  
        'R20': (1, 0.5), 
        'R30': (0, -0.5), 
        'R40': (1, -0.5), 
        'R50': (1.5, 1)  
    }

    fig, ax = plt.subplots()

    def update(frame):
        ax.clear()
        
        # Node colors based on active state
        node_colors = ['green' if G.nodes[node]['active'] else 'red' for node in G.nodes()]
        
        # Edge colors and widths
        edge_colors = []
        edge_widths = []
        edge_labels = {}
        for u, v, data in G.edges(data=True):
            active = data['active'] and G.nodes[u]['active'] and G.nodes[v]['active']
            edge_colors.append('lightblue' if active else 'gray')
            edge_widths.append(4) 
            edge_labels[(u, v)] = data['weight']

        # Draw graph with manual positions
        nx.draw(G, pos, ax=ax, with_labels=True, node_color=node_colors, 
                edge_color=edge_colors, width=edge_widths, node_size=4000, font_size=15, font_color="white")
        
        # Update edge labels for weights
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

        # Node labels with port information
        node_labels = {node: f"\n \n{G.nodes[node]['port']}" for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10, ax=ax)

        ax.set_title("Five Router Topology with Active/Inactive Nodes and Links")

    ani = FuncAnimation(fig, update, interval=1000, frames=30)  # Update every 1 second
    plt.show()
