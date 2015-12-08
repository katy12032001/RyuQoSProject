from pymongo import MongoClient
import time, itertools


def update_db_for_group(db_ip, database, collection, data):
    client = MongoClient(db_ip, 27017)
    group_db = client[database]
    group_collection = group_db[collection]

    db_data = group_collection.find({'groupname': data.group_id}).limit(1)
    if db_data.count() != 0:
        # Update
        group_collection.update({'groupname': data.group_id},
                                {'$set': {'member': data.members,
                                          'link': data.links,
                                          'switch': data.switches}})
    else:
        # Insert
        group_collection.insert({'groupname': data.group_id,
                                 'member': data.members,
                                 'link': data.links,
                                 'switch': data.switches})


def update_app_for_flows(flow_list, dp_ip):
    try:
        client = MongoClient(dp_ip, 27017, connectTimeoutMS = 1000, serverSelectionTimeoutMS=1000)
        classifier_db = client['ManagementServer']
        classifier_collection = classifier_db["ClassifiedRecord"]

        key_set = flow_list.keys()
        for key in key_set:
            flow_info = flow_list.get(key)
            if flow_info is not None and flow_info.app == 'Others':
                db_data = classifier_collection.find({"Info.Source IP": flow_info.src_ip,
                                                      "Info.Destination IP": flow_info.dst_ip,
                                                      "Info.Source Port": flow_info.src_port,
                                                      "Info.Destination Port": flow_info.dst_port,
                                                      "Info.L4 Protocol": flow_info.ip_proto}).sort("Update Time", -1).limit(1)
                print 'INFO [db_util.update_app_for_flows]\n  >>  key:', key, db_data.count()
                if db_data.count() != 0:
                    tmp_result = [d for d in db_data]
                    if tmp_result[0].get("Classified Result").get("Classified Name") is not None:
                        app_name = tmp_result[0].get("Classified Result").get("Classified Name")
                        # print 'INFO [db_util.update_app_for_flows]\n  >>  app name:', app_name
                        flow_info.app = app_name
                        key_r = str(flow_info.dst_mac)+str(flow_info.src_mac)+\
                                str(flow_info.dst_ip)+str(flow_info.src_ip)+\
                                str(flow_info.ip_proto)+\
                                str(flow_info.dst_port)+str(flow_info.src_port)
                        flow_info_r = flow_list.get(key_r)
                        if flow_info_r is not None:
                            # print 'INFO [db_util.update_app_for_flows]\n  >>  vapp name:', app_name
                            flow_info_r.app = app_name
                else:
                    db_data_r = classifier_collection.find({"Info.Source IP": flow_info.dst_ip,
                                                          "Info.Destination IP": flow_info.src_ip,
                                                          "Info.Source Port": flow_info.dst_port,
                                                          "Info.Destination Port": flow_info.src_port,
                                                          "Info.L4 Protocol": flow_info.ip_proto}).sort("Update Time", -1).limit(1)
                    if db_data_r.count() != 0:
                        tmp_result = [d for d in db_data_r]
                        if tmp_result[0].get("Classified Result").get("Classified Name") is not None:
                            app_name = tmp_result[0].get("Classified Result").get("Classified Name")
                            flow_info.app = app_name
                            # print 'INFO [db_util.update_app_for_flows]\n  >>  app name:', app_name
                            key_r = str(flow_info.src_mac)+str(flow_info.dst_mac)+\
                                    str(flow_info.src_ip)+str(flow_info.dst_ip)+\
                                    str(flow_info.ip_proto)+\
                                    str(flow_info.src_port)+str(flow_info.dst_port)
                            flow_info_r = flow_list.get(key_r)
                            if flow_info_r is not None:
                                # print 'INFO [db_util.update_app_for_flows]\n  >>  vapp name:', app_name
                                flow_info_r.app = app_name


    except Exception:
        print 'DB Error'
