'''rest flow get'''
url_flow = '/api/flow_info_flow'
url_flow_app = '/api/flow_info_app/{appname}'
url_flow_member = '/api/flow_info_member/{mac}'

'''rest meter&capacity set'''
url_meter_set = '/api/set_meter_info/{meterid}'
url_capacity_set = '/api/set_capacity/{capacity}'

'''rest qos set'''
url_qos_app_list_get = '/api/get_app_list/{groupid}'
url_qos_meter_list_get = '/api/get_meter_list'
url_qos_policy_get = '/api/get_qos_policy/{groupid}'

url_member_list_for_app = '/api/get_member_for_app/{app}'

url_member_list = '/api/get_member_list'

url_group_list = '/api/get_group_list'
url_group_add = '/api/add_group/{groupid}'

url_dynamic_en = '/api/enable_dynamic_qos/{enable}'
counter = 0
