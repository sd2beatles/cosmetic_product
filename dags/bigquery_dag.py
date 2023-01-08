from airflow import DAG
from airflow.operators.python import BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyTableOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.utils.task_group import TaskGroup
from datetime import datetime
from utilties import queries as qr
import os


def test(**context):
    PROJECT_ID=context['params']['PROJECT_ID']
    DATASET=context['params']['DATASET']
    TABLE=context['params']['TABLE']
    hook=context['params']['hook']
    
    
    result=hook.table_exists(project_id=PROJECT_ID,dataset_id=DATASET,table_id=TABLE)
    
    if result:
        return "{}.execute_query".format(TABLE)
    return "{}.create_table".format(TABLE)
      
with DAG("bq_process",start_date=datetime(2022,12,31),schedule_interval="@daily",catchup=False) as dag:
    hook=BigQueryHook(gcp_conn_id="google_cloud_default")
    
    file='2023-01-03.csv'
    
    PROJECT_ID=os.environ.get("PROJECT_ID")
    DATASET=os.environ.get("DATASET") 
    
    #configuration of google storage
    BUCKET=os.environ.get("BUCKET")
    
    
    
    final_job=DummyOperator(
            task_id="final_stage_completed",
            trigger_rule="all_success"
        )


    
    tables=['conversion_stats','view_stats','product_stats']
    for table in tables:
        with TaskGroup(group_id=table) as bq_group:
            check_table=BranchPythonOperator(
                task_id="check_table",
                python_callable=test,
                provide_context=True,
                params={"PROJECT_ID":PROJECT_ID,
                        "DATASET":DATASET,
                        "TABLE":table,
                        'hook':hook})


            create_table = BigQueryCreateEmptyTableOperator(
                task_id="create_table",
                dataset_id=DATASET,
                table_id=table,
                gcs_schema_object="gs://{}/schema/{}.json".format(
                    BUCKET,table
                ))
            
            if table=="conversion_stats":
                query=qr.conversion_qeury
                
                
            elif table=="product_stats":
                query=qr.product_query
               
            elif table=="view_stats":
                query=qr.view_query
                
            bq_executor=BigQueryInsertJobOperator(
                task_id="execute_query",
                configuration={
                    "query": {
                        "query": query,
                        "useLegacySql": False,
                        "destinationTable": {
                            "projectId": PROJECT_ID,
                            "datasetId": DATASET,
                            "tableId": table,
                        },
                        "writeDisposition": "WRITE_APPEND",
                    }
                },
                trigger_rule='none_failed_min_one_success'
            )
            
            check_table >> create_table >> bq_executor
            check_table >> bq_executor
        bq_group >> final_job
    bq_group >> final_job
    
            
                
                
            
            
            
            
            
       
    
   
