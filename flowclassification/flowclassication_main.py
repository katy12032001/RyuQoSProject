"""Project for application."""
import requests
import time
from pymongo import MongoClient
from var import constant
from record import statistic
from utils import evaluator, database_util

if __name__ == '__main__':
    client = MongoClient(constant.FlowClassification_IP, 27017)
    classifier_db = client['ManagementServer']
    classifier_collection = classifier_db["ClassifiedRecord"]
    while True:
        time.sleep(3)
        response = requests.get('http://127.0.0.1:8080/get_flow_info')
        json_data = response.json()
        # key_set = json_data.keys()
        # print(len(key_set))
        tmp_apprate = {}
        flow_list = []
        for index in json_data:
            flow = json_data[index]
            flow_info = {}
            for key in flow:
                element = {key: str(flow[key])}
                flow_info.update(element)

            db_data = classifier_collection.find({'Info.Source IP': flow_info.get('src_ip'),
                                                  "Info.Destination IP": flow_info.get('dst_ip'),
                                                  "Info.Source Port": int(flow_info.get('src_port')),
                                                  "Info.Destination Port": int(flow_info.get('dst_port')),
                                                  "Info.L4 Protocol": int(flow_info.get('ip_proto'))}).sort("Update Time", -1).limit(1)

            if db_data.count() != 0:
                tmp_result = [d for d in db_data]
                print 'db search', tmp_result[0].get("Classified Result")\
                                                .get("Classified Name")
                if tmp_result[0].get("Classified Result").\
                                 get("Classified Name") is not None:
                    print 'db search2'
                    app_name = tmp_result[0].get("Classified Result").get("Classified Name")
                    flow_info.update({'app': app_name})

            flow_list.append(flow_info)

        statistic.database_flow_record = flow_list
        evaluator.app_evaluation(flow_list)
        database_util.update_data_to_db(1, statistic.database_app_record,
                                        "127.0.0.1", "Rate_for_SlicingProject")
        evaluator.member_evaluation(flow_list)
        database_util.update_data_to_db(2, statistic.database_member_record,
                                        "127.0.0.1", "Rate_for_SlicingProject")
