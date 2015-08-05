"""Project for Forwarding."""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether, inet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
from ryu.topology.api import get_switch
from ryu.lib.packet import arp
from ryu.lib import mac

from utils import ofputils
from var import constant
from db import data_collection
from db import collection
import networkx as nx


class forwarding(app_manager.RyuApp):

    """forwarding Class."""

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(forwarding, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.broadip = '255.255.255.255'
        self.broadip2 = '0.0.0.0'

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):

        msg = ev.msg

        datapath = msg.datapath
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_arp = pkt.get_protocol(arp.arp)
        print pkt_eth.dst, pkt_eth.src

        if pkt_arp:
            print 'arp'
            self._handle_arp(msg, datapath, in_port, pkt_eth, pkt_arp)

        elif pkt_ipv4:
            print 'ipv4'
            if (pkt_eth.dst == mac.BROADCAST):
                self._broadcast_pkt(msg)
            elif (pkt_ipv4.dst == self.broadip) or (pkt_ipv4.dst == self.broadip2):
                self._broadcast_pkt(msg)
            else:
                check = self._check_ingroup(pkt_eth.src, pkt_ipv4.src,
                                            pkt_eth.dst, pkt_ipv4.dst)
                # print 'ckeck', check
                if check != "-1":
                    self._handle_ipv4(datapath, in_port, pkt_eth,
                                      pkt_ipv4, pkt, pkt_eth.dst, check)

    def _handle_ipv4(self, datapath, port, pkt_ethernet, pkt_ipv4, pkt,
                     dst_mac, group_id):
        print 'ipv4', group_id
        parser = datapath.ofproto_parser
        group = data_collection.group_list.get(group_id)
        net = group.topology
        m_dst = data_collection.member_list.get(dst_mac)
        if m_dst is not None:
            # print "><><>>"
            # print dst_mac
            # print m_dst.port

            ipv4_path = self._generate_path(net,
                                            pkt_ethernet.src, pkt_ethernet.dst,
                                            port, m_dst.port,
                                            datapath.id, m_dst.datapath.id)
            for next_n in ipv4_path:
                index = ipv4_path.index(next_n)
                if index != 0 and index != len(ipv4_path)-1:
                    out_port = None
                    net = group.topology
                    if index == len(ipv4_path)-2:
                        out_port = m_dst.port
                    else:
                        out_port = net[next_n][ipv4_path[index+1]]['port']

                    actions = [parser.OFPActionOutput(out_port)]
                    out_datapath = get_switch(self.topology_api_app, dpid=next_n)
                    if pkt_ipv4.proto == inet.IPPROTO_TCP:
                        print 'tcp'
                        pkt_tcp = pkt.get_protocol(tcp.tcp)
                        match = parser.OFPMatch(eth_src=pkt_ethernet.src,
                                                eth_dst=pkt_ethernet.dst,
                                                eth_type=ether.ETH_TYPE_IP,
                                                ipv4_src=pkt_ipv4.src,
                                                ipv4_dst=pkt_ipv4.dst,
                                                ip_proto=pkt_ipv4.proto,
                                                tcp_src=pkt_tcp.src_port,
                                                tcp_dst=pkt_tcp.dst_port)
                    elif pkt_ipv4.proto == inet.IPPROTO_UDP:
                        print 'udp'
                        pkt_udp = pkt.get_protocol(udp.udp)
                        match = parser.OFPMatch(eth_src=pkt_ethernet.src,
                                                eth_dst=pkt_ethernet.dst,
                                                eth_type=ether.ETH_TYPE_IP,
                                                ipv4_src=pkt_ipv4.src,
                                                ipv4_dst=pkt_ipv4.dst,
                                                ip_proto=pkt_ipv4.proto,
                                                udp_src=pkt_udp.src_port,
                                                udp_dst=pkt_udp.dst_port)
                    else:
                        print 'icmp'
                        match = parser.OFPMatch(eth_src=pkt_ethernet.src,
                                                eth_dst=pkt_ethernet.dst,
                                                eth_type=ether.ETH_TYPE_IP,
                                                ipv4_src=pkt_ipv4.src,
                                                ipv4_dst=pkt_ipv4.dst)

                    ofputils.add_flow(out_datapath[0].dp, 10, match, actions)

    def _handle_arp(self, msg, datapath, port, pkt_ethernet, pkt_arp):
        """Handle ARP Setting method."""
        tuple_m = (datapath.id, port)
        print datapath.id, port
        if tuple_m not in data_collection.switch_inner_port:
            self._handle_member_info(datapath, port, pkt_ethernet)
        parser = datapath.ofproto_parser
        if pkt_arp.opcode == arp.ARP_REPLY:
            group = data_collection.group_list.get('whole')
            net = group.topology
            dst = data_collection.member_list.get(pkt_arp.dst_mac)
            if dst is not None:
                print dst.port, dst.datapath
                arp_path = self._generate_path(net, pkt_ethernet.src,
                                               pkt_ethernet.dst, port,
                                               dst.port, datapath.id,
                                               dst.datapath.id)
                for next_n in arp_path:
                    index = arp_path.index(next_n)
                    if index != 0 and index != len(arp_path)-1:
                        out_port = None
                        if index == len(arp_path)-2:
                            out_port = dst.port
                        else:
                            out_port = net[next_n][arp_path[index+1]]['port']
                        actions = [datapath.ofproto_parser.
                                   OFPActionOutput(out_port)]
                        out_datapath = get_switch(self.topology_api_app,
                                                  dpid=next_n)
                        match = parser.OFPMatch(eth_src=pkt_ethernet.src,
                                                eth_type=ether.ETH_TYPE_ARP,
                                                arp_op=arp.ARP_REPLY)
                        ofputils.add_flow(out_datapath[0].dp, 10, match,
                                          actions)
        else:
            self._broadcast_pkt(msg)

    def _generate_path(self, topo, src_mac, dst_mac, src_port,
                       dst_port, src_dpid, dst_dpid):
        """Generate path method."""
        net = nx.DiGraph(data=topo)
        net.add_node(src_mac)
        net.add_node(dst_mac)
        net.add_edge(int(src_dpid), src_mac, {'port': int(src_port)})
        net.add_edge(src_mac, int(src_dpid))
        net.add_edge(int(dst_dpid), dst_mac, {'port': int(dst_port)})
        net.add_edge(dst_mac, int(dst_dpid))
        path = nx.shortest_path(net, src_mac, dst_mac)
        print path
        return path

    def _check_ingroup(self, src_mac, src_ip, dst_mac, dst_ip):
        # m_src = data_collection.member_list.get(src_mac)
        # if m_src is not None:
        #     print m_src.group_id
        check = "-1"
        if src_mac == constant.Gateway_Mac:
            check = "whole"
        if dst_mac == constant.Gateway_Mac:
            check = "whole"
        else:
            m_src = data_collection.member_list.get(src_mac)
            m_dst = data_collection.member_list.get(dst_mac)
            if m_dst is not None and m_src is not None:
                if m_dst.group_id == m_src.group_id:
                    check = m_dst.group_id

        return check

    def _handle_member_info(self, datapath, port, pkt_ethernet):
        returnid = None
        if data_collection.member_list.get(pkt_ethernet.src) is not None:
            print 'have register'
            member = data_collection.member_list.get(pkt_ethernet.src)
            member.datapath = datapath
            member.port = port
            # returnid = member.group_id
            print member.datapath, member.port
            group = data_collection.group_list.get(member.group_id)
            if pkt_ethernet.src not in group.members:
                group.members.append(pkt_ethernet.src)
        else:
            print 'none'
            if constant.NeedToAuth == 0 or pkt_ethernet.src == constant.Gateway_Mac:
                member = collection.Member(pkt_ethernet.src, "whole")
                member.datapath = datapath
                member.port = port
                data_collection.member_list.update({pkt_ethernet.src: member})
                # returnid = member.group_id
                print datapath.id, port, pkt_ethernet.src
                print member.datapath.id, member.port

        # return returnid

    def _broadcast_pkt(self, msg):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=msg.buffer_id,
                                  in_port=msg.match['in_port'],
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)
