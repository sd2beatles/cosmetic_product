from airflow import DAG
from airflow.operators.python import PythonOperator,BranchPythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyTableOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.sensors.filesystem import FileSensor
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.task_group import TaskGroup
from utilties.connection  import get_sources
from utilties.operator import TransformOperator,LocalToStorageOperator
from utilties.connection import get_connection
from datetime import datetime
import datetime as dt
import sys
import os


def test(**context):
    PROJECT_ID=context['params']['PROJECT_ID']
    DATASET=context['params']['DATASET']
    TABLE=context['params']['TABLE']
    SOURCE=context['params']['SOURCE']
    hook=context['params']['hook']
    
    
    result=hook.table_exists(project_id=PROJECT_ID,dataset_id=DATASET,table_id=TABLE)
    
    if result:
        return "{}.insert_data".format(SOURCE)
    return "{}.create_table".format(SOURCE)
      
    

with DAG("dpt_cosmetic",start_date=datetime(2022,12,31),schedule_interval="@daily",catchup=False) as dag:
    
    split_files_by_source = BashOperator(task_id="split_files_by_source",
                                         bash_command="sleep 1")
    # #configuration for mongodb
    # mongo_conn=get_connection()
    mongo_conn=None
    # sources=get_sources()
    today=datetime.utcnow()+dt.timedelta(days=1)
    start_date=today-dt.timedelta(days=7)
    
    #configuration of google storage
    BUCKET=os.environ.get("BUCKET")
    LOCAL_DIR=os.environ.get("LOCAL_DIR")
    DEST_MAIN_DIR=os.environ.get("DEST_MAIN_DIR")
    FILE_NAME=None
    
    #configuration of google bingquery
    PROJECT_ID=os.environ.get("PROJECT_ID")
    DATASET=os.environ.get("DATASET") 
    

    
    next_job=DummyOperator(
            task_id="first_stage_completed",
            trigger_rule="all_success"
        )
    
    sources=['user','transaction','product','website','ab-test','private_info']
    limited_access=sources
    for source in sources:
        with TaskGroup(group_id=source) as task_group:
            filter={"start":start_date,"end":today}
            if not FILE_NAME:
                FILE_NAME=datetime.strftime(filter['end'],"%Y-%m-%d")
            
            if source in limited_access:
                transform= BashOperator(task_id="transform",
                                         bash_command="sleep 1")
            else:
                if source=="user":
                    cols=['user_id','email','gender',
                          'age','country','credit_card','membership','register_date','last_updated']
                elif source=='transaction':
                    cols=['user_id','short_term','long_term','access_day','action','device','user_agent'
                          ,'source','ip','last_updated','product_id','product_name','main','category','product_type',
                          'original_price','special_price','qunatity']
                    
                transform=TransformOperator(task_id="transform",
                                            db_collection=source,
                                            mongo_conn=mongo_conn,
                                            filter=filter,
                                            file_name=FILE_NAME)
            if source in limited_access:
                file_check= BashOperator(task_id="check_file_exists",
                                         bash_command="sleep 1")
            else:
                #just in case we don't have a filename
                dest_path=os.path.join(DEST_MAIN_DIR,source,FILE_NAME)+".csv"
                local_path=os.path.join(LOCAL_DIR,source,FILE_NAME)+".csv"
                
                
                
                file=os.path.join(source,FILE_NAME)+".csv"
                file_check=FileSensor(
                    task_id="check_file_exists",
                    fs_conn_id="file_sensor",
                    filepath=file
                )
            
            if source in limited_access:
                load_to_google_storage=BashOperator(task_id="load_to_google_storage",
                                         bash_command="sleep 1")
            else:
                load_to_google_storage=LocalToStorageOperator(task_id="load_to_google_storage",
                                                            bucket=BUCKET,
                                                            dest_path=dest_path,
                                                            local_path=local_path,
                                                            source=source)
            
            transform >> file_check >> load_to_google_storage
        split_files_by_source >> task_group >> next_job
    
    
    #After all the load tasks is completed,the second job will be triggered
    second_job=DummyOperator(
            task_id="second_stage_completed",
            trigger_rule='none_failed_min_one_success')
    hook=BigQueryHook(gcp_conn_id="google_cloud_default")
    
    FILE_NAME="2023-01-03.csv"
    for source in ['user_01','transaction_01']:
        with TaskGroup(group_id=source) as load_groups:
            table=source.split('_')[0]
            check_table=BranchPythonOperator(
                task_id="check_table",
                python_callable=test,
                provide_context=True,
                params={"PROJECT_ID":PROJECT_ID,
                        "DATASET":DATASET,
                        "TABLE":table,
                        'SOURCE':source,
                        'hook':hook})
            
            create_table = BigQueryCreateEmptyTableOperator(
                task_id="create_table",
                dataset_id=DATASET,
                table_id=table,
                gcs_schema_object="gs://{}/schema/{}.json".format(
                    BUCKET,table
                ))
            
            full_src_path=os.path.join(DEST_MAIN_DIR,table,FILE_NAME)
            bigquery_table='{}.{}'.format(DATASET,table)
            insert_data=GCSToBigQueryOperator(
                task_id="insert_data",
                bucket=BUCKET,
                source_objects=[full_src_path],
                destination_project_dataset_table=bigquery_table,
                write_disposition="WRITE_APPEND",
                source_format="csv",
                allow_quoted_newlines="true",
                skip_leading_rows=1,
                # create_disposition='CREATE_IF_NEEDED',
                schema_object="schema/{}.json".format(table),
                trigger_rule='none_failed_min_one_success'
                )
            check_table >>create_table >> insert_data
            check_table >>insert_data
        next_job >> load_groups>>second_job
    
    
    trigger_target=TriggerDagRunOperator(
        task_id="trigger_target",
        trigger_dag_id="bq_process"
        )
    
    task_group >> next_job >>load_groups >> second_job >> trigger_target
  
        

    