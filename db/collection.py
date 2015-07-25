"""class for member & group."""
import networkx as nx


class member:

    """Class for Member."""

    def __init__(self, name, group):
        """Initial Setting methid."""
        self.name = name
        self.group_id = group
        self.datapath = None
        self.port = None


class group:

    """Class for Group."""

    def __init__(self, group_id):
        """Initial Setting methid."""
        self.group_id = group_id
        self.topology = nx.DiGraph()
        self.switches = []
        self.links = []
        self.members = []
