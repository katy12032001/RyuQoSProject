from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology.api import get_switch
from ryu.controller.event import EventBase
from ryu.ofproto import ether
from ryu.ofproto import inet

from setting.db.utils import flowutils
from setting.db import data_collection
from setting.routing.utils.calculate_route import calculate_least_cost_path
from setting.routing.utils.flow_adjustment_util import flow_adjust


import networkx as nx


class Routing_UpdateEvent(EventBase):
    def __init__(self, msg, load):
        self.msg = msg
        self.load = load



class Routing_Adjustment(app_manager.RyuApp):
    _EVENTS = [Routing_UpdateEvent]
    """Routing_AdjustmentClass."""

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(Routing_Adjustment, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.load = 0

    @set_ev_cls(Routing_UpdateEvent)
    def _routing_adjust(self, ev):
        print '@@####'
        datapath_list = ev.msg
        self.load = ev.load

        for datapath_id in datapath_list:
            datapath = get_switch(self.topology_api_app, dpid=datapath_id)
            flow_list_in_dp = flowutils.get_flow_in_dp(datapath[0].dp.id)
            self._adjustment_handler(flow_list_in_dp, datapath[0].dp.id)
            # flow_list_in_dp = db.._get_flow_in_dp(datapath[0].dp.id)
            # self._request_stats(datapath[0].dp)

    def _request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)



    # @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _adjustment_handler(self, flow_list, dpid):
        print '><>><><><>'
        weight = data_collection.switch_stat.get(dpid)
        load = 0
        if weight is not None:
            if weight.get('load') is not None:
                load = max(weight.get('load'))
        # for stat in ev.msg.body:
        #     if stat.match.get('eth_type') == ether.ETH_TYPE_IP:
        #         key_tuples = stat.match.get('eth_src')\
        #          + stat.match.get('eth_dst')\
        #          + stat.match.get('ipv4_src')\
        #          + stat.match.get('ipv4_dst')\
        #          + str(stat.match.get('ip_proto'))\
        #
        #         if stat.match.get('ip_proto') == inet.IPPROTO_TCP:
        #             key_tuples += str(stat.match.get('tcp_src'))\
        #                               + str(stat.match.get('tcp_dst'))
        #         elif stat.match.get('ip_proto') == inet.IPPROTO_UDP:
        #             key_tuples += str(stat.match.get('udp_src'))\
        #                               + str(stat.match.get('udp_dst'))
        for key_tuples in flow_list.keys():
            flow = data_collection.flow_list.get(key_tuples)
            # check_for_limit(flow, key_tuples)
            src = data_collection.member_list.get(flow.src_mac)
            kk = (str(src.datapath.id) + flow.src_mac + flow.dst_mac +
                  flow.src_ip + flow.dst_ip + str(flow.ip_proto) +
                  str(flow.src_port) + str(flow.dst_port))

            ff = data_collection.flow_list.get(kk)
            if ff is not None:
                if ff.r_limited == 1:
                    flow.r_limited = 1

            if flow is not None and flow.r_limited == 0:
                print 'flow_rate & load', key_tuples, flow.rate, load, key_tuples
                flow.r_limited = 1
                switch_list = get_switch(self.topology_api_app, None)
                for sw in switch_list:
                    sw_flow_tuple = (str(sw.dp.id) +
                                     flow.src_mac + flow.dst_mac +
                                     flow.src_ip + flow.dst_ip +
                                     str(flow.ip_proto) +
                                     str(flow.src_port) + str(flow.dst_port))

                    print 'tu', sw_flow_tuple
                    flow_l = data_collection.flow_list.get(sw_flow_tuple)
                    if flow_l is not None:
                        flow_l.r_limited = 1
                        
                if load <= self.load:
                    break
                elif self.load - flow.rate <= 0:
                    continue
                else:

                    group = data_collection.group_list.get('whole')
                    topo = group.topology
                    net = nx.DiGraph(data=topo)
                    net.add_node(flow.src_mac)
                    net.add_node(flow.dst_mac)
                    src = data_collection.member_list.get(flow.src_mac)
                    dst = data_collection.member_list.get(flow.dst_mac)
                    net.add_edge(int(src.datapath.id), flow.src_mac,
                                 {'port': int(src.port)})
                    net.add_edge(flow.src_mac, int(src.datapath.id))
                    net.add_edge(int(dst.datapath.id), flow.dst_mac,
                                 {'port': int(dst.port)})
                    net.add_edge(flow.dst_mac, int(dst.datapath.id))
                    all_paths = nx.all_simple_paths(net, flow.src_mac,
                                                    flow.dst_mac)
                    path_list = list(all_paths)
                    target_path_index, target_path_cost = calculate_least_cost_path(path_list, data_collection.switch_stat, net)
                    if (target_path_cost + flow.rate) < (load - flow.rate):
                        load = load - flow.rate
                        target_path = path_list[target_path_index]

                        for node in target_path:
                            index = target_path.index(node)
                            if index != 0 and index != len(target_path)-1:
                                switches = get_switch(self.topology_api_app, node)
                                target_path[index] = switches[0].dp


                        print 't', target_path
                        flow_adjust(net, target_path, flow)
