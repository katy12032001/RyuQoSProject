"""Project for Initial."""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.topology.api import get_switch, get_link
from ryu.topology import event
from dynamic_qos.utils import rate_setup

from db import data_collection
from db import collection
from var import constant
from utils import log
from ratelimitation.setting import setup

import networkx as nx


class initial(app_manager.RyuApp):

    """Initial Class."""

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(initial, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.net = nx.DiGraph()
        # log.log_backup_r('datacollection_grouplist.pkl', data_collection.group_list)
        # log.log_backup_r('datacollection_switchinnerport.pkl', data_collection.switch_inner_port)
        # log.log_backup_r('datacollection_memberlist.pkl', data_collection.member_list)
        # log.log_backup_r('ratelimite_setup_for_specialcase.pkl', setup.ratelimite_setup_for_specialcase)
        # log.log_backup_r('datacollection_meterlist.pkl', data_collection.meter_list)

    def add_table_miss_flow(self, datapath, priority, match, actions,
                            buffer_id=None):
        """Add table miss flow entry method."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
        self.get_topology_data()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handling Switch Feature Event."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_table_miss_flow(datapath, 0, match, actions)

    def get_topology_data(self):
        """Topology Info Handling."""
        self.net = nx.DiGraph()

        switch_list = get_switch(self.topology_api_app, None)
        switches = [switch.dp.id for switch in switch_list]
        self.net.add_nodes_from(switches)

        # for switch in switch_list:
        #     self.nodes[switch.dp.id] = switch.dp

        links_list = get_link(self.topology_api_app, None)
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no})
                 for link in links_list]
        self.net.add_edges_from(links)

        links = [(link.dst.dpid, link.src.dpid, {'port': link.dst.port_no})
                 for link in links_list]
        self.net.add_edges_from(links)

        data_collection.switch_inner_port = []
        for link in links_list:
            inner_port1 = (link.src.dpid, link.src.port_no)
            inner_port2 = (link.dst.dpid, link.dst.port_no)

            if inner_port1 not in data_collection.switch_inner_port:
                data_collection.switch_inner_port.append(inner_port1)
            if inner_port2 not in data_collection.switch_inner_port:
                data_collection.switch_inner_port.append(inner_port2)

        group = collection.Group('whole')
        group.topology = self.net
        group.switches = switches
        group.links = links

        if data_collection.group_list.get('whole') is not None:
            # print 'a'
            g = data_collection.group_list.get('whole')

            g.switches = group.switches
            g.topology = group.topology
            g.links = group.links
            # print g.switches, g.topology, g.links
        else:
            # print 'b'
            data_collection.group_list.update({'whole': group})
        # g2 = data_collection.group_list.get('whole')
        # print g2.switches
        # print g2.topology.nodes(), g2.topology.edges()
        # print g2.links
        
        # log.log_backup_w('datacollection_grouplist.pkl', data_collection.group_list)
        # log.log_backup_w('datacollection_switchinnerport.pkl', data_collection.switch_inner_port)

    @set_ev_cls(event.EventLinkAdd)
    def get_topology_for_add(self, ev):
        """Link add."""
        print "EventLinkAdd"
        self.get_topology_data()

    @set_ev_cls(event.EventLinkDelete)
    def get_topology_for_delete(self, ev):
        """Link delete."""
        print "EventLinkDelete"
        self.get_topology_data()

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_for_swadd(self, ev):
        """Switch add."""
        print "EventSwitchEnter"
        self.get_topology_data()
        switch_list = get_switch(self.topology_api_app, None)
        rate_setup.init_meter_setup(constant.Capacity, switch_list)

    @set_ev_cls(event.EventSwitchLeave)
    def get_topology_for_swdelete(self, ev):
        """Switch delete."""
        print "EventSwitchDelete"
        self.get_topology_data()
