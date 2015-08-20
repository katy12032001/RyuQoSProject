"""Project for Rest API (Group Setting)."""
import json

from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response

import networkx as nx
from db import data_collection
from db import collection
from utils import db_util

url = '/handle_group_info/topology/{groupid}'
get_group_info_instance_name = 'get_group_info_api_app'


class group_setting(app_manager.RyuApp):

    """Get_Group_Info class."""

    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(group_setting, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(group_setting_rest,
                      {get_group_info_instance_name: self})

    def save_data_to_database(self, groupid, topology, switches, links):
        """Save Group data to database method."""
        if data_collection.group_list.get(groupid) is None:
            group = collection.Group(groupid)
            group.topology = topology
            group.switches = switches
            group.links = links
            data_collection.group_list.update({groupid: group})

        else:
            group = data_collection.group_list.get(groupid)
            group.topology = topology
            group.switches = switches
            group.links = links

        group = data_collection.group_list.get(groupid)
        # db_util.update_db_for_group("127.0.0.1", "Rate_for_SlicingProject",
        #                             "Group_collection", group)


# curl -X PUT -d '{"link" : "(1, 2, 4):(2, 1, 3)", "switches" : "2, 1"}'
#               http://127.0.0.1:8080/handle_group_info/topology/group_1
class group_setting_rest(ControllerBase):

    """Get_Group_Info_Rest class."""

    def __init__(self, req, link, data, **config):
        """Initial Setting method."""
        super(group_setting_rest, self).__init__(req, link, data, **config)
        self.get_group_info = data[get_group_info_instance_name]

    @route('group_data', url, methods=['PUT'])
    def put_group_data_(self, req, **kwargs):
        """Put Group data method."""
        groupid = (kwargs['groupid'])
        link_str = req.body
        json_link = json.loads(link_str)
        print json_link.get('link')

        net = nx.DiGraph()
        switches = []
        links = []

        if json_link.get('link') is not None:
            group_link = str(json_link.get('link'))
            list1 = group_link.split(":")

            for string_t in list1:
                k = string_t.split(", ")
                p = k[0].split("(")
                p2 = k[2].split(")")
                print p[1], k[1], p2[0]
                t = (int(p[1]), int(k[1]), {'port': int(p2[0])})
                links.append(t)
                # if int(p[1]) not in switches:
                #     switches.append(int(p[1]))
                # if int(k[1]) not in switches:
                #     switches.append(int(k[1]))

        group_switch = str(json_link.get('switches'))

        switch = group_switch.split(", ")
        switches = [int(sw) for sw in switch]

        print switches
        print links

        net.add_nodes_from(switches)
        net.add_edges_from(links)

        self.get_group_info.save_data_to_database(str(groupid),
                                                  net, switches, links)
        return Response(content_type='application/json',
                        body=str('Success'))
