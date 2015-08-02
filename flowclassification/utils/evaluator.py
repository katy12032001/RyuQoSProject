"""Method for evaluation."""
from record import statistic
from var import constant


def app_evaluation(flow_list):
    """Method for app valuation."""
    tmp_apprate = {}
    for flow_info in flow_list:
        app_name = flow_info.get('app')
        if app_name in tmp_apprate:
            tmp_apprate[app_name] += int(flow_info.get('rate'))
        else:
            tmp_apprate.update({app_name: int(flow_info.get('rate'))})

    for key in tmp_apprate:
        if key in statistic.database_app_record:
            tmp_object = statistic.database_app_record[key]
            tmp_object.rate = tmp_apprate[key]
            tmp_object.exist = 1
        else:
            flow = statistic.Application_recored(key, tmp_apprate[key])
            flow.exist = 1
            statistic.database_app_record.update({key: flow})

    key_set = statistic.database_app_record.keys()
    for key in key_set:
        flow = statistic.database_app_record[key]
        if flow.exist == 0:
            statistic.database_app_record.pop(key)
        else:
            statistic.database_app_record[key].exist = 0
            print key, flow.rate


def member_evaluation(flow_list):
    """Method for member valuation."""
    tmp_member_rate = {}
    for flow_info in flow_list:
        tmp = None
        if flow_info.get('src_mac') == constant.Gateway_Mac:
            tmp = flow_info.get('dst_mac')
        else:
            tmp = flow_info.get('src_mac')

        if tmp in tmp_member_rate:
            tmp_apprate = tmp_member_rate.get(tmp).apprate
            app_name = flow_info.get('app')
            if app_name in tmp_apprate:
                tmp_apprate[app_name] += int(flow_info.get('rate'))
            else:
                tmp_apprate.update({app_name: int(flow_info.get('rate'))})
        else:
            tmp_member_rate.update({tmp: statistic.Memeber_record(tmp)})
            tmp_apprate = tmp_member_rate.get(tmp).apprate
            tmp_apprate.update({flow_info.get('app'): int(flow_info.get('rate'))})

        tmp_member_rate.get(tmp).flow.append(flow_info)

    statistic.database_member_record = tmp_member_rate

    # for tt in statistic.database_member_record:
    #     print tt
    #     for qq in statistic.database_member_record.get(tt).apprate:
    #         print qq, statistic.database_member_record.get(tt).apprate.get(qq)
