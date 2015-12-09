def calculate_least_cost_path(path_list, switch_stats):
    target_path = None
    target_cost = -1
    print path_list
    for path in path_list:
        path_index = path_list.index(path)
        for node in path:
            index = path.index(node)
            if index != 0 and index != len(path)-1:
                port = switch_stats.get(node)
                if port is not None:
                    port_stats = switch_stats.get(node).get('weight')
                    cost = 0
                    if port_stats is not None:
                        for port in port_stats.keys():
                            counter_list = port_stats.get(port)
                            cost = counter_list[1] + counter_list[0] + cost

                        if cost < target_cost:
                            target_path = path_index
                            target_cost = cost
                        elif cost == target_cost:
                            target_path_length = len(path_list[target_path])
                            path_length = len(path)
                            if path_length < target_path_length:
                                target_path = path_index
                                target_cost = cost
                        elif target_cost == -1:
                            target_path = path_index
                            target_cost = cost

    return target_path

def check_switch_load(switch_list, switch_stats, limitation):
    valid = 0
    target_switch_list = []
    for switch in switch_list:
        port = switch_stats.get(switch)
        if port is not None:
            port_stats = switch_stats.get(switch).get('weight')
            if port_stats is not None:
                for port in port_stats.keys():
                    counter_list = port_stats.get(port)
                    if counter_list[0] > limitation:
                        valid = 1
                    elif counter_list[1] > limitation:
                        valid = 1
                    else:
                        if counter_list[2] > 0:
                            valid = 1
                    if valid == 1:
                        target_switch_list.append(switch)
                        break
    return target_switch_list
