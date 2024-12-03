import cmd2
import json
from router import Router
import logging
from router import Router, logger, ColoredFormatter



# Retrieve the root logger
root_logger = logging.getLogger()

# Find the console handler (StreamHandler)
console_handler = next(
    (handler for handler in root_logger.handlers if isinstance(handler, logging.StreamHandler)), None
)

class DVRouterCLI(cmd2.Cmd):
    """
    Command-line interface for managing Distance Vector Routers.
    """

    def __init__(self):
        super().__init__()
        self.routers = {}  # Stores the Router objects
        self.prompt = "Yaw-6250~ "
        self.intro = (
            "Welcome to the ITS 6250 Distance Vector Router Simulation \n"
            "Type 'help' or '?' to list commands.\n"
            "Type 'quit' to exit the application."
        )
        self.logger = logger

    

    
    def do_enable_logging(self, args):
        """
        Enable logging to the console.
        Usage: enable_logging
        """
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ColoredFormatter())
            self.logger.addHandler(console_handler)
            self.poutput("Logging to console enabled.")
        else:
            self.poutput("Logging to console is already enabled.")

    def do_disable_logging(self, args):
        """
        Disable logging to the console.
        Usage: disable_logging
        """
        handlers_to_remove = [
            handler for handler in self.logger.handlers if isinstance(handler, logging.StreamHandler)
        ]
        for handler in handlers_to_remove:
            self.logger.removeHandler(handler)
        self.poutput("Logging to console disabled.")

    def do_show_tables(self, args):
        """
        Show routing tables for all routers.
        Usage: show_tables
        """
        if not self.routers:
            self.perror("No routers loaded. Use 'load_config' first.")
            return
        for router in self.routers.values():
            router.display_routing_table()

    def do_load_config(self, args):
        """
        Load router configurations from config.json.
        Usage: load_config
        """
        try:
            with open('config.json', 'r') as file:
                config = json.load(file)
                for router_name, router_info in config.items():
                    port = router_info['port']
                    neighbors = {
                        name: (details[0], details[1])
                        for name, details in router_info['neighbors'].items()
                    }
                    # Create a router instance
                    self.routers[router_name] = Router(router_name, port, neighbors)
                self.poutput("Configuration loaded successfully.")
        except FileNotFoundError:
            self.perror("Config file not found.")
        except Exception as e:
            self.perror(f"Failed to load configuration: {e}")

    # Starting individual routers
    def do_start_router(self, args):
        """
        Start a single router.
        Usage: start_router <router_name>
        """
        if not args:
            self.perror("Usage: start_router <router_name>")
            return

        router_name = args.strip()
        if router_name not in self.routers:
            self.perror(f"Router {router_name} not found. May be load configuration first.")
            return

        router = self.routers[router_name]
        router.start()
        self.poutput(f"Router {router_name} started.")

    def do_stop_router(self, args):
        """
        Stop a single router.
        Usage: stop_router <router_name>
        """
        if not args:
            self.perror("Usage: stop_router <router_name>")
            return

        router_name = args.strip()
        if router_name not in self.routers:
            self.perror(f"Router {router_name} not found.")
            return

        router = self.routers[router_name]
        router.stop()
        self.poutput(f"Router {router_name} stopped.")

    def do_start_routers(self, args):
        """
        Start all routers.
        Usage: start_routers
        """
        if not self.routers:
            self.perror("No routers loaded. Use 'load_config' first.")
            return
        for router_name, router in self.routers.items():
            router.start()
            self.poutput(f"Router {router_name} started.")
        self.poutput("All routers started.")

    def do_stop_routers(self, args):
        """
        Stop all routers.
        Usage: stop_routers
        """
        if not self.routers:
            self.perror("No routers loaded. Use 'load_config' first.")
            return
        for router_name, router in self.routers.items():
            router.stop()
            self.poutput(f"Router {router_name} stopped.")
        self.poutput("All routers stopped.")


    def do_show_table(self, args):
        """
        Show routing tables for all routers.
        Usage: show_table
        """
        if not self.routers:
            self.perror("No routers loaded. Use 'load_config' first.")
            return
        for router in self.routers.values():
            router.display_routing_table()
    

    def do_start_interface(self, args):
        """
        Start a virtual interface for a router.
        Usage: start_interface <router_name> <interface_port>
        """
        try:
            router_name, interface_port = args.split()
            interface_port = int(interface_port)
            if router_name in self.routers:
                router = self.routers[router_name]
                if interface_port in router.interfaces:
                    router.start_interface(interface_port)
                    self.poutput(f"Started interface {interface_port} on router {router_name}")
                    
                else:
                    self.perror(f"Router {router_name} does not have a virtual interface on port {interface_port}")
            else:
                self.perror(f"Router {router_name} not found.")
        except ValueError:
            self.perror("Usage: start_interface <router_name> <interface_port>")
        except Exception as e:
            self.perror(f"Error: {e}")

    def do_stop_interface(self, args):
        """
        Stop a virtual interface for a router.
        Usage: stop_interface <router_name> <interface_port>
        """
        try:
            router_name, interface_port = args.split()
            interface_port = int(interface_port)
            if router_name in self.routers:
                router = self.routers[router_name]
                if interface_port in router.interfaces:
                    router.stop_interface(interface_port)
                    self.poutput(f"Stopped interface {interface_port} on router {router_name}")
                    
                else:
                    self.perror(f"Router {router_name} does not have a virtual interface on port {interface_port}")
            else:
                self.perror(f"Router {router_name} not found.")
        except ValueError:
            self.perror("Usage: stop_interface <router_name> <interface_port>")
        except Exception as e:
            self.perror(f"Error: {e}")

    def do_start_all_interfaces(self, args):
        """
        Start all virtual interfaces for a specific router.
        Usage: start_all_interfaces <router_name>
        """
        try:
            router_name = args.strip()
            if router_name in self.routers:
                router = self.routers[router_name]
                for interface_port in router.interfaces.keys():
                    router.start_interface(interface_port)
                self.poutput(f"Started all interfaces for router {router_name}")
            else:
                self.perror(f"Router {router_name} not found.")
        except Exception as e:
            self.perror(f"Error: {e}")

    def do_stop_all_interfaces(self, args):
        """
        Stop all virtual interfaces for a specific router.
        Usage: stop_all_interfaces <router_name>
        """
        try:
            router_name = args.strip()
            if router_name in self.routers:
                router = self.routers[router_name]
                for interface_port in router.interfaces.keys():
                    router.stop_interface(interface_port)
                self.poutput(f"Stopped all interfaces for router {router_name}")
            else:
                self.perror(f"Router {router_name} not found.")
        except Exception as e:
            self.perror(f"Error: {e}")

    def do_list_interfaces(self, args):
        """
        List all virtual interfaces for a router.
        Usage: list_interfaces <router_name>
        """
        try:
            router_name = args.strip()
            if router_name in self.routers:
                router = self.routers[router_name]
                self.poutput(f"Interfaces for {router_name}: {router.interfaces}")
            else:
                self.perror(f"Router {router_name} not found.")
        except Exception as e:
            self.perror(f"Error: {e}")

    def do_hide_updates(self, args):
        """
        Disable logging to the console.
        Usage: hide_updates
        """
        try:
            handlers_to_remove = [
                handler for handler in root_logger.handlers if isinstance(handler, logging.StreamHandler)
            ]
            if handlers_to_remove:
                for handler in handlers_to_remove:
                    root_logger.removeHandler(handler)
                self.poutput("Console logging disabled.")
            else:
                self.poutput("Console logging is already disabled.")
        except Exception as e:
            self.perror(f"Error: {e}")

    def do_show_updates(self, args):
        """
        Enable logging to the console.
        Usage: show_updates
        """
        try:
            existing_handlers = [
                handler for handler in root_logger.handlers if isinstance(handler, logging.StreamHandler)
            ]
            if not existing_handlers:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                console_handler.setFormatter(
                    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
                )
                root_logger.addHandler(console_handler)
                self.poutput("Console logging enabled.")
            else:
                self.poutput("Console logging is already enabled.")
        except Exception as e:
            self.perror(f"Error: {e}")


    def do_status(self, args):
        """
        Show the status of all routers and their interfaces.
        Usage: status
        """
        if not self.routers:
            self.perror("No routers loaded. Use 'load_config' first.")
            return
        for router_name, router in self.routers.items():
            self.poutput(f"Router {router_name}: {'Running' if router.running else 'Stopped'}")
            self.poutput(f"Interfaces: {router.interfaces}")
            self.poutput("-" * 40)

    def do_all_interfaces_start(self, args):
        """
        Start all virtual interfaces for all routers.
        Usage: all_interfaces_start
        """
        if not self.routers:
            self.perror("No routers loaded. Use 'load_config' first.")
            return
        for router_name, router in self.routers.items():
            for interface_port in router.interfaces.keys():
                router.start_interface(interface_port)
            self.poutput(f"Started all interfaces for router {router_name}.")
        self.poutput("All interfaces for all routers started.")

    def do_all_interfaces_stop(self, args):
        """
        Stop all virtual interfaces for all routers.
        Usage: all_interfaces_stop
        """
        if not self.routers:
            self.perror("No routers loaded. Use 'load_config' first.")
            return
        for router_name, router in self.routers.items():
            for interface_port in router.interfaces.keys():
                router.stop_interface(interface_port)
            self.poutput(f"Stopped all interfaces for router {router_name}.")
        self.poutput("All interfaces for all routers stopped.")

    def do_show(self, args):
        """
        Open a new window showing the current routing topology.
        Usage: show
        """
        from visualize import update_network_graph
        update_network_graph(self.routers)


if __name__ == '__main__':
    app = DVRouterCLI()
    app.cmdloop()
