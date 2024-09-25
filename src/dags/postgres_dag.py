from datetime import datetime,timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import os 

def load_csv_topostgress():
    base_path = os.path.abspath(os.path.join(os.getcwd(), 'data'))
    csv_file_path = os.path.join(base_path, 'retail_clean.csv')
    df = pd.read_csv(csv_file_path)
    postgres_hook = PostgresHook(postgres_conn_id='postgres_localhost')
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()

    # Insert data from the DataFrame into PostgreSQL
    for index, row in df.iterrows():
        insert_query = """
        INSERT INTO customer_schema.customer_table 
        (Invoice, StockCode, "Description", Quantity, InvoiceDate, Price, "Customer ID", Country, Revenue) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            row['Invoice'], 
            row['StockCode'], 
            row['Description'], 
            row['Quantity'], 
            row['InvoiceDate'], 
            row['Price'], 
            row['Customer ID'], 
            row['Country'], 
            row['Revenue']
        ))

    
    conn.commit()
    cursor.close()
    conn.close()


default_args = {
    'owner' : 'jack',
    'retries' : 5,
    'retry_delay': timedelta(minutes = 5)
}

with DAG(
    dag_id = 'dag_with_postgres_operator_v01',
    default_args = default_args,
    start_date= datetime.now(),
    schedule_interval= '0 0 * * *'
) as dag:
    task1 = PostgresOperator(
        task_id = 'create_postgres_table',
        postgres_conn_id = 'postgres_localhost',
        sql = """
            CREATE SCHEMA IF NOT EXISTS customer_schema;

            DROP TABLE IF EXISTS customer_schema.customer_table;

            CREATE TABLE customer_schema.customer_table (
                Invoice TEXT,
                StockCode TEXT,
                "Description" TEXT,
                Quantity INT,
                InvoiceDate TIMESTAMP,
                Price FLOAT,
                "Customer ID" TEXT,
                Country TEXT,
                Revenue FLOAT
            );
             """
    )
    task2 = PythonOperator(
       task_id = 'load_csv_to_postgres',
       python_callable= load_csv_topostgress
    )
    task1 >> task2 