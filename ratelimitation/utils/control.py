__author__ = 'katywu'

from ryu.ofproto import ether, inet

from utils import ofputils
from db import data_collection


def set_ratelimite_for_app(appname, meter_id, group, state):
        """Set rate control for applications"""
        flow_to_be_handle = []
        key_set = data_collection.flow_list.keys()
        memberlist = data_collection.group_list.get(group).members
        for key in key_set:
            flow_info = data_collection.flow_list[key]
            if flow_info.app == appname:
                if flow_info.src_mac in memberlist or flow_info.dst_mac in memberlist:
                    flow_to_be_handle.append(flow_info)

        for flow in flow_to_be_handle:
            datapath = data_collection.member_list.get(flow.dst_mac).datapath
            out_port = data_collection.member_list.get(flow.dst_mac).port

            parser = datapath.ofproto_parser
            actions = [parser.OFPActionOutput(out_port)]
            if flow.ip_proto == inet.IPPROTO_TCP:
                match = parser.OFPMatch(eth_src=flow.src_mac,
                                        eth_dst=flow.dst_mac,
                                        eth_type=ether.ETH_TYPE_IP,
                                        ipv4_src=flow.src_ip,
                                        ipv4_dst=flow.dst_ip,
                                        ip_proto=flow.ip_proto,
                                        tcp_src=flow.src_port,
                                        tcp_dst=flow.dst_port)
            else:
                match = parser.OFPMatch(eth_src=flow.src_mac,
                                        eth_dst=flow.dst_mac,
                                        eth_type=ether.ETH_TYPE_IP,
                                        ipv4_src=flow.src_ip,
                                        ipv4_dst=flow.dst_ip,
                                        ip_proto=flow.ip_proto,
                                        udp_src=flow.src_port,
                                        udp_dst=flow.dst_port)

            ofputils.add_flow_for_ratelimite(datapath, 20, match, actions, meter_id, state)
