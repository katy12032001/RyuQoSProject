"""Project for Rest API (Group Setting)."""
import json

from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response
from ryu.topology.api import get_switch

from db import data_collection
from var import constant
from utils import ofputils
from flowclassification.record import statistic

url = '/set_qos_info/{capacity}'
set_qos_info_instance_name = 'set_qos_info_api_app'
app_url = '/get_app_list'
meter_list_url = '/get_meter_list'


class QosSetup(app_manager.RyuApp):

    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(QosSetup, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        wsgi = kwargs['wsgi']
        wsgi.register(QosSetupRest,
                      {set_qos_info_instance_name: self})

    def set_qos_parameter(self, capacity):
        constant.Capacity = capacity



# curl -X PUT http://127.0.0.1:8080/set_qos_info/2
class QosSetupRest(ControllerBase):

    def __init__(self, req, link, data, **config):
        """Initial Setting method."""
        super(QosSetupRest, self).__init__(req, link, data, **config)
        self.get_member_info = data[set_qos_info_instance_name]

    @route('qos_data', url, methods=['PUT'])
    def set_qos_data(self, req, **kwargs):
        capacity = str(kwargs['capacity'])

        self.get_member_info.set_qos_parameter(capacity)
        return Response(content_type='application/json',
                            body=str('Success'))

    @route('qos_data', app_url, methods=['GET'])
    def get_app_list(self, req, **kwargs):
        app_list = statistic.database_app_record.keys()
        dic = {}
        for key in app_list:
            dic.update({key: statistic.database_app_record[key].rate})
        body = json.dumps(dic)
        return Response(content_type='application/json', body=body)

    @route('qos_data', meter_list_url, methods=['GET'])
    def get_meter_list(self, req, **kwargs):
        meter_list = data_collection.meter_list.keys()
        dic = {}
        for key in meter_list:
            dic.update({key: data_collection.meter_list.get(key)})
        body = json.dumps(dic)
        return Response(content_type='application/json', body=body)
