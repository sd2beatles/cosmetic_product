from airflow.models import BaseOperator
from airflow.models.taskinstance import Context
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.contrib.hooks.gcs_hook import GoogleCloudStorageHook
from datetime import datetime
from utilties.transform import *
import pandas as pd
import logging
import csv
import os






class LocalToStorageOperator(BaseOperator):
    def __init__(self,bucket:str,dest_path:str,local_path:str,source:str,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.bucket=bucket
        self.dest_path=dest_path
        self.local_path=local_path
        self.source=source
        
    def execute(self,context):
        gcs=GoogleCloudStorageHook()
        gcs.upload(self.bucket,self.dest_path,self.local_path)
        logging.info("successfully fetch the file,{}".format(self.source))
      
    
        
        
        

class TransformOperator(BaseOperator):
    def __init__(self,db_collection:str,mongo_conn:object,filter:dict,file_name:str,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.db_collection=db_collection
        self.mongo_conn=mongo_conn
        self.filter=filter
        self.file_name=file_name
    
    def transform_user(self,user:pd.DataFrame):
        #integrate the labels of gender
        user['gender']=user.gender.map(lambda x:"F" if x[0].lower()=='f' else "M")
        
        #integrate the labels of countries
        user['country']=user.country.map(lambda x:label_change(x))
        return user
    
    def transform_trans(self,trans:pd.DataFrame):
        
        #removing abnormal_index
        abnormal=trans[(trans.action=='view')&(trans.details=={})]
        if list(abnormal.index):
            trans.loc[abnormal.index,'details']=np.nan
        
        del abnormal
        
        
        #remove private networks
        private_networks=["127.0.0.1",'10.0.0.0/8','172.16.0.0/12','191.0.0.0/24']
        trans=trans[~(trans.ip.isin(private_networks))]
        
        #remove index
        trans.reset_index(inplace=True)
        trans.drop("index",axis=1,inplace=True)
        
        #unwrap iner json data 
        detail=pd.json_normalize(trans.details)
        trans=pd.concat([trans,detail],axis=1)
        trans.drop("details",axis=1,inplace=True)
        
        #correct the abnormal prices
        trans=price_preprocess(trans)
     
        return trans
        

    def save_to_local(self,data:pd.DataFrame):            
        data_file ="/opt/airflow/storage/{}/{}.csv".format(self.db_collection,self.file_name)
        data.to_csv(data_file,index=False)
        
        
        
    
    def execute(self,context):
        query={"last_updated":{"$gte":self.filter['start'],"$lt":self.filter['end']}}
        json_data=self.mongo_conn.find(
            mongo_collection=self.db_collection,
            query=query,
            mongo_db=os.environ.get("TARGET_MONGO_DB")
        )
        
        df=pd.DataFrame(list(json_data))
    
        if self.db_collection=='user':
            df=self.transform_user(df)
        elif self.db_collection=='transaction':
            df=self.transform_trans(df)
    
        self.save_to_local(df)
    
        logging.info("successfully save the file,{}".format(self.db_collection))
        
            
   
        
  
            
            
            
        
        
        
        
        
   
    
      
        
     
    

  
    