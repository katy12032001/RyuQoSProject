"""Mehthod for rate control in dynamic qos."""
from dynamic_qos.setup import meter_mapping
from ratelimitation.utils import control
from utils import ofputils


def meter_setup(switch_list, bandwidth, index, app, group, status):
    """Set meters."""
    # for dp in switch_list:
    #     ofputils.set_meter_entry(dp.dp, int(bandwidth), int(index), 'ADD')
    # meter_mapping.meter_and_group.update()
    if status == 0:
        meter_setup = meter_mapping.Meter_setup(int(bandwidth), app, group, index)
        if meter_mapping.meter_and_group.get(group) is None:
            data = {'meter_list': [index], 'Meter_setup': [meter_setup]}
            meter_mapping.meter_and_group.update({group: data})
            for dp in switch_list:
                ofputils.set_meter_entry(dp.dp, int(bandwidth), int(index), 'ADD')
        else:
            meter_list = meter_mapping.meter_and_group[group].get('meter_list')
            if index not in meter_list:
                for dp in switch_list:
                    ofputils.set_meter_entry(dp.dp, int(bandwidth), int(index), 'ADD')
                meter_list.append(index)
                setup_list = meter_mapping.meter_and_group[group].get('Meter_setup')
                setup_list.append(meter_setup)
            else:
                i = meter_list.index(index)
                M_list = meter_mapping.meter_and_group[group].get('Meter_setup')
                M_list[i] = meter_setup
                for dp in switch_list:
                    ofputils.set_meter_entry(dp.dp, int(bandwidth), int(index), 'MODIFY')
    else:
        for group in meter_mapping.meter_and_group.keys():
            list = meter_mapping.meter_and_group[group].get('Meter_setup')
            for M in list:
                for dp in switch_list:
                    print 'delete entry', M.meter
                    ofputils.set_meter_entry(dp.dp, int(M.apprate), int(M.meter), 'DELETE')


def rate_control_for_apps(rate_list, group_total_list, group_list,
                          ratio_app, switch_list, capacity):
    """Handle rate control for apps."""
    if sum(group_total_list) != 0:
        group_total_list = [i/sum(group_total_list) for i in group_total_list]
    print 'INFO [dynamic_qos.rate_control_for_apps]\n  >>'
    print 'the used bandwidth =>', sum(rate_list)
    print 'maximum we can used =>', 0.9 * capacity * 1024

    if sum(rate_list) >= 0.9 * capacity * 1024:
        if meter_mapping.have_control == 0:
            meter_mapping.have_control = 1
        for group_id in group_list:
            if group_id != 'whole':
                index = (group_list.index(group_id)+1)*10
                print 'index', index, group_list.index(group_id), ratio_app[group_id]
                for app in ratio_app.get(group_id).keys():
                    print 'app meter', index, app
                    if ratio_app[group_id].get(app) > 0:
                        index += 1
                        app_r = capacity * 1024 * ratio_app[group_id].get(app)
                        print 'app rate', app_r*8/1024, ratio_app[group_id].get(app)
                        meter_setup(switch_list, app_r*8/1024, index, app, group_id, 0)
                        control.set_ratelimite_for_app(app, index, group_id, 'up', 'd')
    else:
        if meter_mapping.have_control == 1:
            meter_mapping.have_control = 0
            meter_setup(switch_list, 0, 0, 0, 0, 1)
