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
        print '<<<<dynamic>>>>>>'
        # mean_value_for_group = similarity.mean_value()
        # print mean_value_for_group
        group_list = data_collection.group_list.keys()
        print group_list
        original_data = self._get_all_data_from_db()
        normalize_d, mean_d = similarity.normalization_and_average(original_data)

        whole_predict_data = {}
        ratio_app = {}
        for group_id in group_list:
            if group_id != 'whole':
                data = self._predict(group_id, mean_d, normalize_d)
                print 'mean', mean_d
                print 'data', normalize_d

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


    def _get_all_data_from_db(self):
        group_list = data_collection.group_list.keys()
        all_data = {}
        for group_id in group_list:
            app_list = statistic.database_app_record.keys()
            if group_id != 'whole':
                group = data_collection.group_list.get(group_id)
                members = group.members
                member_data = {}
                for member in members:
                    a = {}
                    for app in app_list:
                        print member
                        if member in statistic.database_member_record.keys():
                            m = statistic.database_member_record.get(member)
                            if m.apprate.get(app) is not None:
                                a.update({app: m.apprate.get(app)})
                    member_data.update({member: a})
                all_data.update({group_id: member_data})
        print "<!!!!!!!!!!!all data!!!!!!!!!!!!!!>", all_data
        return all_data

    def _get_array_for_group(self, group_id, whole_data):
        group_data = whole_data.get(group_id)
        print group_data
        if group_data is not None:
            for key in group_data.keys():
                app_list = group_data.get(key).get('app_list').keys()
                for i in range(len(app_list)):
                    value = group_data.get(key).get('app_data')
                    data = group_data.get(key).get('app_list')
                    data[app_list[i]] = value[i]
                group_data[key] = group_data.get(key).get('app_list')
        print group_data
        app_list = statistic.database_app_record.keys()
        member_list = group_data.keys()
        if member_list is not None:
            for member in member_list:
                app_list_m = group_data.get(member).keys()
                member = group_data[member]
                for app in app_list:
                    if app not in app_list_m:
                        member.update({app: -1.0})
        return group_data


    def _predict(self, group_id, mean_value_for_group, data_ori):
        print '<predict begin>'
        data = self._get_array_for_group(group_id, data_ori)
        print 'orginal data =>', data
        data_ans = {}

        if data is not None:
            data_ans = data.copy()
            data_m = data.keys()
            print data_m
            for m in data_m:
                print 'predict people', m
                m_d = data.get(m)
                app = m_d.keys()
                for a in app:
                    print a, m, m_d.get(a)
                    if m_d.get(a) == -1.0:
                        p1 = mean_value_for_group.get(group_id).get(m)
                        p2_u = 0.0
                        p2_d = 0.0
                        for pm in data_m:
                            if pm != m:
                                print 'handle people', pm
                                if data.get(pm).get(a) != -1:
                                    print 't :hd & mean', data.get(pm).get(a) , mean_value_for_group.get(group_id).get(pm)
                                    t = data.get(pm).get(a) - mean_value_for_group.get(group_id).get(pm)
                                    t = t*similarity.get_similarity_between_members(m, pm, data)
                                    print 't', t
                                    p2_u += t
                                    p2_d += math.fabs(similarity.get_similarity_between_members(m,pm,data))
                        print p2_d, p2_u, p1
                        if p2_d!= 0:
                            gg = data_ans.get(m)
                            gg[a] = round(p2_u / p2_d + p1, 2)
                            print '2', gg[a]
            print 'data', data_ans
        return data_ans
