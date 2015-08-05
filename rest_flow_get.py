"""Project for Rest API (Flow Info Getting)."""
import json
from webob import Response
from ryu.ofproto import ether, inet
from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication, route

from db import data_collection
from utils import db_util, ofputils
from var import constant

import collections

# url = '/get_flow_info/{flows}'
get_flow_info_instance_name = 'get_flow_info_api_app'
url_flow = '/flow_info_flow'
url = '/flow_info_app/{appname}'

class FlowInfoSetup(app_manager.RyuApp):

    """Get_Flow_Info class."""

    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(FlowInfoSetup, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(FlowInfoSetupRest,
                      {get_flow_info_instance_name: self})

    def set_ratelimite_for_app(self, appname, bandwidth):
        """Set rate control for applications"""
        db_util.update_app_for_flows(constant.FlowClassification_IP)
        flow_to_be_handle = []
        key_set = data_collection.flow_list.keys()
        for key in key_set:
            flow_info = data_collection.flow_list[key]
            if flow_info.app == appname:
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


            od = collections.OrderedDict(sorted(data_collection.meter_list.items()))
            p = od.keys()
            print len(p)
            tmp = p[0]
            for key in p:
                if bandwidth < key:
                    break
                tmp = key
            index = p.index(tmp)
            meter_id = data_collection.meter_list.get(p[index])
            ofputils.add_flow_for_ratelimite(datapath, 20, match, actions, meter_id)


        print appname, bandwidth

# curl -X GET -d http://127.0.0.1:8080/flow_info_flow


# curl -X PUT -d '{"bandwidth" : "8192"}' http://127.0.0.1:8080/flow_info_app/a

class FlowInfoSetupRest(ControllerBase):

    """Get_Member_Info_Rest class."""

    def __init__(self, req, link, data, **config):
        """Initial Setting method."""
        super(FlowInfoSetupRest, self).__init__(req, link, data, **config)
        self.get_flow_info = data[get_flow_info_instance_name]

    @route('flow_data', url_flow, methods=['GET'])
    def get_flow_data(self, req, **kwargs):
        """Get Flow data method."""
        print ">"
        dic = {}
        for key in data_collection.flow_list:
            flow_c = data_collection.flow_list[key]
            list_f = {"src_mac": flow_c.src_mac, "dst_mac": flow_c.dst_mac,
                      "src_ip": flow_c.src_ip, "dst_ip": flow_c.dst_ip,
                      "src_port": flow_c.src_port, "dst_port": flow_c.dst_port,
                      "ip_proto": flow_c.ip_proto, "rate": flow_c.rate, "app": flow_c.app}

            dic.update({key: list_f})
        body = json.dumps(dic)
        return Response(content_type='application/json', body=body)

    @route('rate_for_app', url, methods=['PUT'])
    def set_flow_for_ratelimite_in_app(self, req, **kwargs):
        app = str(kwargs['appname'])
        content = req.body
        json_link = json.loads(content)
        bandwidth = str(json_link.get('bandwidth'))

        self.get_flow_info.set_ratelimite_for_app(app, bandwidth)
