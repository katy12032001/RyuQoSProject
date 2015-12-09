from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology.api import get_switch
from ryu.controller.event import EventBase
from ryu.ofproto import ether
from ryu.ofproto import inet

from setting.db import data_collection
from setting.routing.utils.calculate_route import calculate_least_cost_path
from setting.routing.utils.flow_adjustment_util import flow_adjust


import networkx as nx

class Routing_UpdateEvent(EventBase):
    def __init__(self, msg):
        self.msg = msg

class Routing_Adjustment(app_manager.RyuApp):
    _EVENTS = [Routing_UpdateEvent]
    """Routing_AdjustmentClass."""

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(Routing_Adjustment, self).__init__(*args, **kwargs)
        self.topology_api_app = self

    @set_ev_cls(Routing_UpdateEvent)
    def _routing_adjust(self, ev):
        print '@@####'
        datapath_list = ev.msg
        for datapath_id in datapath_list:
            datapath = get_switch(self.topology_api_app, dpid=datapath_id)
            self._request_stats(datapath[0].dp)

    def _request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        for stat in ev.msg.body:
            if stat.match.get('eth_type') == ether.ETH_TYPE_IP:
                key_tuples = stat.match.get('eth_src')\
                 + stat.match.get('eth_dst')\
                 + stat.match.get('ipv4_src')\
                 + stat.match.get('ipv4_dst')\
                 + str(stat.match.get('ip_proto'))\

                if stat.match.get('ip_proto') == inet.IPPROTO_TCP:
                    key_tuples += str(stat.match.get('tcp_src')) + str(stat.match.get('tcp_dst'))
                elif stat.match.get('ip_proto') == inet.IPPROTO_UDP:
                    key_tuples += str(stat.match.get('udp_src'))\
                                      + str(stat.match.get('udp_dst'))
                flow = data_collection.flow_list.get(key_tuples)

                if flow is not None:
                    print 'flow_rate', flow.rate
                    group = data_collection.group_list.get('whole')
                    topo = group.topology
                    net = nx.DiGraph(data=topo)
                    net.add_node(flow.src_mac)
                    net.add_node(flow.dst_mac)
                    src = data_collection.member_list.get(flow.src_mac)
                    dst = data_collection.member_list.get(flow.dst_mac)
                    net.add_edge(int(src.datapath.id), flow.src_mac, {'port': int(src.port)})
                    net.add_edge(flow.src_mac, int(src.datapath.id))
                    net.add_edge(int(dst.datapath.id), flow.dst_mac, {'port': int(dst.port)})
                    net.add_edge(flow.dst_mac, int(dst.datapath.id))
                    all_paths = nx.all_simple_paths(net, flow.src_mac, flow.dst_mac)
                    path_list = list(all_paths)
                    target_path_index = calculate_least_cost_path(path_list, data_collection.switch_stat)
                    target_path = path_list[target_path_index]

                    for node in target_path:
                        index = target_path.index(node)
                        if index != 0 and index != len(target_path)-1:
                            switches = get_switch(self.topology_api_app, node)
                            target_path[index] = switches[0].dp

                    flow_adjust(net, target_path, flow)
