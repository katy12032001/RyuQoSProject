"""Project for Rest API (Flow Info Getting)."""
import json
from webob import Response
from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication, route

from db import data_collection
from ratelimitation.setting import setup

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

    def set_ratelimite_for_app(self, appname, meter_id, group_id, state):
        """Set rate control for applications."""
        if setup.ratelimite_setup_for_specialcase.get(group_id) is not None:
            appset = setup.ratelimite_setup_for_specialcase.get(group_id)
            appset.update({appname: {'state': state, 'meter_id': int(meter_id)}})
        else:
            setup.ratelimite_setup_for_specialcase.update({group_id: {appname: {'state': state, 'meter_id': int(meter_id)}}})


# curl -X GET -d http://127.0.0.1:8080/flow_info_flow
# curl -X PUT -d '{"meter_id" : "8192", "group_id" : "group_1", "state" : "up"}' http://127.0.0.1:8080/flow_info_app/a

class FlowInfoSetupRest(ControllerBase):

    """Get_Member_Info_Rest class."""

    def __init__(self, req, link, data, **config):
        """Initial Setting method."""
        super(FlowInfoSetupRest, self).__init__(req, link, data, **config)
        self.get_flow_info = data[get_flow_info_instance_name]

    @route('flow_data', url_flow, methods=['GET'])
    def get_flow_data(self, req, **kwargs):
        """Get Flow data method."""
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
        meter_id = str(json_link.get('meter_id'))
        group_id = str(json_link.get('group_id'))
        state = str(json_link.get('state'))

        self.get_flow_info.set_ratelimite_for_app(app, meter_id, group_id, state)
