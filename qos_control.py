"""Prject for Qos Control."""

from ryu.base import app_manager
from ryu.lib import hub

from ratelimitation.setting import setup
from ratelimitation.utils import control
from flowclassification.record import statistic
from db import data_collection
from dynamic_qos.utils import similarity

import numpy as np
import math

class QosControl(app_manager.RyuApp):

    """Qos Control Class."""

    def __init__(self, *args, **kwargs):
        """Initial Setting method."""
        super(QosControl, self).__init__(*args, **kwargs)
        self.monitor_thread = hub.spawn(self._monitor)

    def _monitor(self):
        while True:
            self._control_manual()
            self._control_dynamic()

            hub.sleep(5)

    def _control_manual(self):
        print 'manual'
        setting = setup.ratelimite_setup_for_specialcase
        for group in setting.keys():
            for app in setting.get(group).keys():
                if setting.get(group).get(app).get('state') == 'up':
                    control.set_ratelimite_for_app(app, setting.get(group).get(app).get("meter_id"), group, 'up')
                else:
                    control.set_ratelimite_for_app(app, setting.get(group).get(app).get("meter_id"), group, 'down')
                    setting.get(group).pop(app)

    def _control_dynamic(self):
        print 'dynamic'
        mean_value_for_group = similarity.mean_value()
        print mean_value_for_group
        group_list = data_collection.group_list.keys()
        print group_list

        whole_predict_data = {}
        ratio_app = {}
        for group_id in group_list:
            data = self._predict(group_id, mean_value_for_group)
            '''
            whole_predict_data.update({group_id: data})
            app_list = statistic.database_app_record.keys()
            member_list = data.keys()
            ratio = []
            ratio_a = {}
            for app in app_list:
                tmp = 0.0
                for member in member_list:
                    tmp += data.get(member).get(app)
                ratio_a.update({app: tmp})
                ratio.append(tmp)

            keys_r = ratio_a.keys()
            for d in keys_r:
                if sum(ratio) != 0:
                    ratio_a[d] = ratio_a.get(d)/sum(ratio)
                else:
                    ratio_a[d] = 0
            ratio_app.update({group_id: ratio_a})
            '''

    def _get_array(self, group_id):
        ans = {}
        app_list = statistic.database_app_record.keys()
        group = data_collection.group_list.get(group_id)
        members = group.members
        for member in members:
            a = {}
            for app in app_list:
                print member
                if member in statistic.database_member_record.keys():
                    m = statistic.database_member_record.get(member)
                    if m.apprate.get(app) is None:
                        a.update({app: -1.0})
                    else:
                        a.update({app: m.apprate.get(app)})
                else:
                    a.update({app: -1.0})
            ans.update({member: a})
        print 'array', ans
        return ans

    def _predict(self, group_id, mean_value_for_group):
        data = self._get_array(group_id)
        data_m = data.keys()
        print data_m
        for m in data_m:
            m_d = data.get(m)
            app = m_d.keys()
            for a in app:
                if m_d.get(a) == -1.0:
                    p1 = mean_value_for_group.get(group_id).get(m)
                    p2_u = 0.0
                    p2_d = 0.0
                    for pm in data_m:
                        print pm, "@@@@@@@@@"
                        if pm != m and pm != 'ac:22:0b:d7:0b:ca':
                            # m = 'ac:22:0b:d7:0b:ca'
                            # pm = '00:0e:c6:f2:37:7b'
                            t = data.get(pm).get(a) - mean_value_for_group.get(group_id).get(pm)
                            t = t*similarity.get_similarity_between_members(m, pm, data)
                            p2_u += t
                            p2_d += math.fabs(similarity.get_similarity_between_members(m,pm,data))
                    if p2_d + p1 != 0:
                        m_d[a] = round(p2_u / p2_d + p1, 2)
                    # print '2', m_d[a]
        print 'data', data
        return data
