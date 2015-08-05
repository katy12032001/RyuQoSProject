from pymongo import MongoClient
from db import data_collection

def update_db_for_group(db_ip, database, collection, data):
    client = MongoClient(db_ip, 27017)
    group_db = client[database]
    group_collection = group_db[collection]

    db_data = group_collection.find({'groupname': data.group_id}).limit(1)
    print 'db_count', db_data.count()
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

def update_app_for_flows(dp_ip):
    client = MongoClient(dp_ip, 27017)
    classifier_db = client['ManagementServer']
    classifier_collection = classifier_db["ClassifiedRecord"]

    key_set = data_collection.flow_list.keys()
    for key in key_set:
        flow_info = data_collection.flow_list[key]
        db_data = classifier_collection.find({"Info.Source IP": flow_info.src_ip,
                                              "Info.Destination IP": flow_info.dst_ip,
                                              "Info.Source Port": flow_info.src_port,
                                              "Info.Destination Port": flow_info.dst_port,
                                              "Info.L4 Protocol": flow_info.ip_proto}).sort("Update Time", -1).limit(1)


        if db_data.count() != 0:
            tmp_result = [d for d in db_data]
            if tmp_result[0].get("Classified Result").get("Classified Name") is not None:
                app_name = tmp_result[0].get("Classified Result").get("Classified Name")
                flow_info.app = app_name
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
