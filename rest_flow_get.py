"""Project for Rest API (Flow Info Getting)."""
import json
from webob import Response

from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication, route

from db import data_collection

url = '/get_flow_info'
get_flow_info_instance_name = 'get_flow_info_api_app'


class get_flow_info(app_manager.RyuApp):

    """Get_Flow_Info class."""

    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(get_flow_info, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(get_flow_info_rest,
                      {get_flow_info_instance_name: self})


# curl -X GET -d http://127.0.0.1:8080/get_flow_info
class get_flow_info_rest(ControllerBase):

    """Get_Member_Info_Rest class."""

    def __init__(self, req, link, data, **config):
        """Initial Setting method."""
        super(get_flow_info_rest, self).__init__(req, link, data, **config)
        self.get_flow_info = data[get_flow_info_instance_name]

    @route('flow_data', url, methods=['GET'])
    def get_flow_data_(self, req, **kwargs):
        """Get Flow data method."""
        dic = {}
        for key in data_collection.flow_list:
            flow_c = data_collection.flow_list[key]
            list_f = {"src_mac": flow_c.src_mac, "dst_mac": flow_c.dst_mac,
                      "src_ip": flow_c.src_ip, "dst_ip": flow_c.dst_ip,
                      "src_port": flow_c.src_port, "dst_port": flow_c.dst_port,
                      "ip_proto": flow_c.ip_proto, "rate": flow_c.rate}

            dic.update({key: list_f})
        body = json.dumps(dic)
        return Response(content_type='application/json', body=body)
