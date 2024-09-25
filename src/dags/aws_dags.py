import pandas as pd
import os
import requests
import zipfile
import logging
import boto3
from datetime import datetime,timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils import timezone
# from kaggle.api.kaggle_api_extended import KaggleApi


default_args = {
    'owner' : 'jack',
    'startdate' : datetime.now()
}

def postgres_to_s3():
    #step 1 initiate connection, Define the SQL query to extract data
    postgres_hook = PostgresHook(
        postgres_conn_id="postgres_localhost",
        schema="customer_schema"
    )
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()

    query = """
        SELECT * 
        FROM customer_schema.customer_table 
        WHERE StockCode = '85048'
        """

    # specify filename
    csv_file = "/opt/airflow/data/retail_clean.csv"

    # Define the COPY command with the query, CSV format, and headers
    copy_command = f"COPY ({query}) TO STDOUT WITH CSV HEADER"

    with open(csv_file, "w", encoding='utf-8') as f: # use "w+" to create file if it not exist
        cursor.copy_expert(copy_command, file=f)
    # close cursor and connection
    cursor.close()
    conn.close()

    # specify desired target file name
    object_name = "data_postgres_cleaned.csv"

    # retrieve credentials
    key = pd.read_csv(aws_credentials_path)
    _aws_access_key_id = key["Access key ID"][0]
    _aws_secret_access_key = key["Secret access key"][0]

    # authenticate and upload to S3
    s3 = boto3.client('s3',
                        aws_access_key_id=_aws_access_key_id,
                        aws_secret_access_key=_aws_secret_access_key)
    
    with open(csv_file, "rb") as f:
        # s3.upload_fileobj(f, aws_bucket, object_name)
        s3.put_object(Bucket=aws_bucket, Key=object_name, Body=f)
    f.close()
    logging.info(f"Completed extracting data from postgres database loaded to {object_name}")

with DAG(
    dag_id = "dag_postgres_to_s3_v01",
    default_args = default_args
) as dag:
    task1 = PythonOperator(
        task_id = "postgres_to_s3",
        python_callable=postgres_to_s3
    )
    task1

#minio_s3_conn