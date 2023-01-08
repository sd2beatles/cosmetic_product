from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime
import pymongo
import typing
import os


SOURCES_MONGO_COLLECTION="configs"

'''
List of setting values of a database that contains the related information of the target database.
Currently,configs under local database cotains the list of collection names of our assigned databse

The configuration can take the form of

[{
  "name":"sources",
  "sources":["user","tranaction","product","access_log"]
}]
'''

def get_connection():
    try:
        airflow_db_conn=os.environ.get("SOURCES_MONGO_DB_CONN_ID")
        conn=MongoHook(conn_id=airflow_db_conn)
    except ConnectionError as e:
        print(e)
        
    return conn


def get_sources():
  
    hook=get_connection()
    config_collection=hook.get_collection(
        mongo_db=str(os.environ.get("SOURCES_MONGO_DB")),
        mongo_collection=str(os.environ.get("SOURCES_MONGO_COLLECITON"))
    )
  
    
    # sources_config contains infomraiton on the collections 
    sources_config=config_collection.find_one(
        filter={"name":str(os.environ.get("SOURCES_CONFIG_NAME"))},
        sort=[("$natural",-1)],
    )
    
        
    if not sources_config:
        return  []
    
    return sources_config.get(os.environ.get("SOURCES_KEY"))

  
    
        
    
    
    
        
