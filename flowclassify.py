"""Prject for Flow Classify."""

from ryu.base import app_manager
from ryu.lib import hub

from db import data_collection
from flowclassification.utils import evaluator
from flowclassification.record import statistic

class FlowClassify(app_manager.RyuApp):

    """Flow Statistic Class."""

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(FlowClassify, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.monitor_thread = hub.spawn(self._monitor)

    def _monitor(self):
        while True:
            hub.sleep(5)
            evaluator.app_evaluation(data_collection.flow_list)
            print statistic.database_app_record
            evaluator.member_evaluation(data_collection.flow_list, data_collection.member_list)
            print "@@@@@@@@@@@@"
            for key in statistic.database_member_record:
                print "1", key, statistic.database_member_record[key]
                for key2 in statistic.database_member_record[key].apprate:
                    print "2", key2, statistic.database_member_record[key].apprate[key2]

            evaluator.group_evaluation(statistic.database_member_record, data_collection.group_list)


            print statistic.database_group_record
            for key in statistic.database_group_record:
                print "11", key, statistic.database_group_record[key], statistic.database_group_record[key].member.keys()
                for key2 in statistic.database_group_record[key].apprate:
                    print "12", key2, statistic.database_group_record[key].apprate[key2]
