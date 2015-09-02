"""Prject for Flow Classify."""

from ryu.base import app_manager
from ryu.lib import hub

from ryu.controller.handler import set_ev_cls
from db import data_collection
from flowclassification.utils import evaluator
from flowclassification.record import statistic
from utils import db_util

from var import constant
from flowstatistic_monitor import APP_UpdateEvent
import time, itertools


class FlowClassify(app_manager.RyuApp):

    """Flow Statistic Class."""

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(FlowClassify, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(APP_UpdateEvent)
    def app_event_handler(self, ev):
        print ('[INFO FlowClassify.app_event_handler] %s' % ev.msg)
        db_util.update_app_for_flows(data_collection.flow_list, constant.FlowClassification_IP)

    def _monitor(self):
        while True:
            hub.sleep(8)
            evaluator.app_evaluation(data_collection.flow_list)
            # print statistic.database_app_record
            evaluator.member_evaluation(data_collection.flow_list, data_collection.member_list)
            print '[INFO FlowClassify._monitor]Flow Statistic Class\n>> member'
            for key in statistic.database_member_record:
                print " >", key, statistic.database_member_record[key]
                for key2 in statistic.database_member_record[key].apprate:
                    print " >", key2, statistic.database_member_record[key].apprate[key2]

            evaluator.group_evaluation(statistic.database_member_record, data_collection.group_list)
            print '[INFO FlowClassify._monitor]Flow Statistic Class\n>> group'
            for key in statistic.database_group_record:
                print " >", key, statistic.database_group_record[key], statistic.database_group_record[key].member.keys()
                v = 0.0
                for key2 in statistic.database_group_record[key].apprate:
                    print " >", key2, statistic.database_group_record[key].apprate[key2]
                    v += statistic.database_group_record[key].apprate[key2]
                statistic.database_group_record[key].total = v
                print ' > total bandwidth: ', statistic.database_group_record[key].total
