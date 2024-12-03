"""
Router Module for Distance Vector Routing Simulation.

This module defines the Router class and associated utilities for simulating a Distance Vector 
Routing Protocol. It includes features for managing routing tables, sending and receiving 
updates, and dynamic interface control.

Modules Used:
- socket: For UDP socket communication.
- threading: For concurrent operations of routers.
- json: For serializing and deserializing routing tables.
- time: For periodic update delays.
- logging: For managing detailed logs of router activities.

Key Features:
- Dynamic routing table updates using the Bellman-Ford algorithm.
- Support for virtual interfaces and neighbor management.
- Colored logging for enhanced debugging.
- Routing table synchronization across multiple routers.

Citation:
- Bellman-Ford Algorithm Python Implementation: https://github.com/arnab132/Bellman-Ford-Algorithm-Python
- Bellman-Ford Algorithm: https://en.wikipedia.org/wiki/Bellman–Ford_algorithm
- Python Socket Programming Documentation: https://docs.python.org/3/library/socket.html
- Python Logging Documentation: https://docs.python.org/3/library/logging.html

Author: Yaw Akosah
"""

import socket
import threading
import json
import time
import logging

# ANSI color codes
RESET_FORMAT = '\033[0m'
GREEN = '\033[32m'  # For 'send' operations
BLUE = '\033[34m'   # For 'receive' operations
YELLOW = '\033[33m' # For 'update' operations

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Check if the message contains specific keywords to apply color
        if 'sending' in record.msg:
            record.msg = f"{GREEN}{record.msg}{RESET_FORMAT}"
        elif 'received' in record.msg:
            record.msg = f"{BLUE}{record.msg}{RESET_FORMAT}"
        elif 'updated' in record.msg:
            record.msg = f"{YELLOW}{record.msg}{RESET_FORMAT}"
        return super().format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Remove the default handler if it exists
if logger.handlers:
    logger.handlers = []

# Add a new handler with our custom formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())
logger.addHandler(console_handler)

# File handler for logging without color
file_handler = logging.FileHandler("router.log")
file_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))  # Optional: same format for file
logger.addHandler(file_handler)


class Router:
    def __init__(self, name, port, neighbors):
        """
        Initialize a router instance.
        :param name: Name of the router (e.g., "R10").
        :param port: UDP port number for the router.
        :param neighbors: Dictionary of neighbors {neighbor_name: (neighbor_port, link_cost)}.
        """
        self.name = name
        self.port = port
        self.neighbors = neighbors
        self.routing_table = {name: (0, name)}  # Initial routing table {destination: (cost, next_hop)}
        self.running = False  # Flag to control the router's operation
        self.reporting = False  # Disable advertisement reporting by default
        self.previous_routing_table = {}  # Initialize the attribute
        
        # Interfaces: Each neighbor's port is mapped to its active/inactive state
        self.interfaces = {neighbor_port: False for _, (neighbor_port, _) in neighbors.items()}
        
        # Non-blocking UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', port))
        self.socket.setblocking(False)

    def display_routing_table(self):
        """
        Print the current routing table with formatting for clarity.
        """
        print(f"\nRouting Table for {self.name}:")
        print(f"{'Destination':<12} | {'Cost':>8} | {'Next Hop':<12}")
        print("-" * 35)  # Separator line
        for destination, (cost, next_hop) in self.routing_table.items():
            # Highlight changes with color
            if self.previous_routing_table.get(destination, None) != (cost, next_hop):
                print(f"\033[92m{destination:<12} | {cost:>8} | {next_hop:<12}\033[0m")  # Green for changes
            else:
                print(f"{destination:<12} | {cost:>8} | {next_hop:<12}")
        print("-" * 35)  # Closing line
        # Store current table for the next comparison
        self.previous_routing_table = self.routing_table.copy()

    def start_interface(self, interface_port):
        """
        Start a specific virtual interface (port).
        :param interface_port: The UDP port of the interface to start.
        """
        if interface_port in self.interfaces:
            self.interfaces[interface_port] = True
            logger.info(f"Router {self.name} started virtual interface on port {interface_port}")
        else:
            logger.error(f"Router {self.name} does not have a virtual interface on port {interface_port}")

    def stop_interface(self, interface_port):
        """
        Stop a specific virtual interface (port).
        :param interface_port: The UDP port of the interface to stop.
        """
        if interface_port in self.interfaces:
            self.interfaces[interface_port] = False
            logger.info(f"Router {self.name} stopped virtual interface on port {interface_port}")
        else:
            logger.error(f"Router {self.name} does not have a virtual interface on port {interface_port}")

    def send_routing_table(self):
        """
        Send the routing table to all neighbors through active interfaces.
        """
        for neighbor_name, (neighbor_port, _) in self.neighbors.items():
            if self.interfaces.get(neighbor_port, False):  # Only send if the interface is active
                message = {
                    'sender': self.name,
                    'routing_table': self.routing_table
                }
                logger.info(f"Router {self.name} is sending routing table to {neighbor_name} on port {neighbor_port}")
                self.socket.sendto(json.dumps(message).encode(), ('127.0.0.1', neighbor_port))
            else:
                logger.info(f"Router {self.name} interface on port {neighbor_port} is inactive. Skipping.")

    def receive_routing_table(self):
        """
        Receive and process routing table updates from neighbors.
        """
        try:
            data, _ = self.socket.recvfrom(1024)  # Receive up to 1024 bytes
            message = json.loads(data.decode())
            sender = message['sender']
            neighbor_table = message['routing_table']

            logger.info(f"Router {self.name} received routing table from {sender}: {neighbor_table}")
            # Process the received routing table
            self.update_routing_table(sender, neighbor_table)
        except BlockingIOError:
            pass  # No data received; non-blocking socket
        except Exception as e:
            logger.error(f"Router {self.name} encountered an error while receiving data: {e}")

    def update_routing_table(self, neighbor_name, neighbor_table):
        """
        Update the routing table using the Bellman-Ford algorithm.
        :param neighbor_name: The name of the neighbor router sending the update.
        :param neighbor_table: The routing table received from the neighbor.
        """
        link_cost = self.neighbors[neighbor_name][1]
        updated = False

        for destination, (neighbor_cost, _) in neighbor_table.items():
            new_cost = link_cost + neighbor_cost
            if destination not in self.routing_table or new_cost < self.routing_table[destination][0]:
                self.routing_table[destination] = (new_cost, neighbor_name)
                updated = True

        if updated:
            logger.info(f"Router {self.name} updated its routing table based on updates from {neighbor_name}")

    def start(self):
        """
        Start the router's operation: send and receive routing table updates periodically.
        """
        self.running = True
        logger.info(f"Router {self.name} started")

        def run():
            while self.running:
                self.send_routing_table()
                self.receive_routing_table()
                time.sleep(30)  # Adjust the interval as needed

        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        """
        Stop the router's operation.
        """
        self.running = False
        logger.info(f"Router {self.name} stopped")

    def enable_reporting(self):
        """
        Enable reporting of routing advertisements.
        """
        self.reporting = True
        logger.info(f"Router {self.name} enabled advertisement reporting")

    def disable_reporting(self):
        """
        Disable reporting of routing advertisements.
        """
        self.reporting = False
        logger.info(f"Router {self.name} disabled advertisement reporting")

    def add_neighbor(self, neighbor_name, neighbor_port, cost):
        """
        Add a neighbor dynamically.
        :param neighbor_name: Name of the new neighbor.
        :param neighbor_Interface: Interface of the neighbor.
        :param cost: Link cost to the new neighbor.
        """
        self.neighbors[neighbor_name] = (neighbor_port, cost)
        self.routing_table[neighbor_name] = (cost, neighbor_name)
        self.interfaces[neighbor_port] = False  # Add the neighbor's interface as inactive
        logger.info(f"Router {self.name} added neighbor {neighbor_name} with cost {cost}")