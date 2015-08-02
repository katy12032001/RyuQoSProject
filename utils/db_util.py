from pymongo import MongoClient


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
