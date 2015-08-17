import scipy
from scipy.stats import pearsonr
import numpy as np
from flowclassification.record.statistic import database_member_record, database_app_record
from flowclassification.record import statistic
from db import data_collection

def get_similarity_between_members(m1, m2, data):
    check_x = 0
    check_y = 0
    # x = database_member_record.get(m1)
    # y = database_member_record.get(m2)

    # print check_x, check_y
    #
    # if x is not None:
    #     check_x = 1
    #
    # if y is not None:
    #     check_y = 1

    x_bandwidth_for_app = data.get(m1)
    y_bandwidth_for_app = data.get(m2)
    x = [x_bandwidth_for_app.get(app) for app in x_bandwidth_for_app.keys()]
    y = [y_bandwidth_for_app.get(app) for app in y_bandwidth_for_app.keys()]

    # for app in database_app_record.keys():
    #     if check_x == 1:
    #         if x.apprate.get(app) is not None:
    #             x_bandwidth_for_app.append(x.apprate.get(app))
    #         else:
    #             x_bandwidth_for_app.append(0)
    #     else:
    #         x_bandwidth_for_app.append(0)
    #
    #     if check_y == 1:
    #         if y.apprate.get(app) is not None:
    #             y_bandwidth_for_app.append(y.apprate.get(app))
    #         else:
    #             y_bandwidth_for_app.append(0)
    #     else:
    #         y_bandwidth_for_app.append(0)

    # print x_bandwidth_for_app, y_bandwidth_for_app
    # r_row, p_value = pearsonr(x_bandwidth_for_app, y_bandwidth_for_app)

    print x, y
    r_row, p_value = pearsonr(x, y)

    print 'similarity', r_row

    return r_row


def mean_value():
    app_list = statistic.database_app_record.keys()
    print statistic.database_group_record.keys(), app_list
    group_list = data_collection.group_list.keys()
    mean_value_for_group = {}
    for group_id in group_list:
        mean_value = {}
        group = data_collection.group_list.get(group_id)
        members = group.members
        for member in members:
            if member in statistic.database_member_record.keys():
                m = statistic.database_member_record[member]
                print members, m, statistic.database_member_record.keys()
                value = [statistic.database_member_record[member].apprate[key2] for key2 in statistic.database_member_record[member].apprate]
                print 'mean', value, member, round(np.mean(value), 2)
                mean_value.update({member: round(np.mean(value), 2)})
            else:
                mean_value.update({member: 0.0})

        mean_value_for_group.update({group_id: mean_value})

    return mean_value_for_group
