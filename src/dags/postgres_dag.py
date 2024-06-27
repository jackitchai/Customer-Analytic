from datetime import datetime,timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

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
                InvoiceNo TEXT,
                StockCode TEXT,
                "Description" TEXT,
                Quantity INT,
                InvoiceDate TIMESTAMP,
                UnitPrice FLOAT,
                CustomerID TEXT,
                Country TEXT
            );
             """
    )
    task2 = PostgresOperator(
        task_id = 'insert_into_table',
        postgres_conn_id = 'postgres_localhost',
        sql = """
            insert into Orders values(1,'pending')
        """
    )
    task1 >> task2 