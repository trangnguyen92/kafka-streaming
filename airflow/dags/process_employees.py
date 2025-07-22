import datetime
import pendulum
import os

import pandas as pd
import requests
from airflow.sdk import dag, task, chain, task_group
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

PROJECT_ID = "airflow-trang"
BUCKET_NAME = "airflow-trang-bucket-2"
DATASET_ID = "airflow_trang_dataset"
GCP_CONN_ID = "gcp_trang_default"

@dag(
    dag_id="process_employees",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def ProcessEmployees():
    create_employees_table = SQLExecuteQueryOperator(
        task_id="create_employees_table",
        conn_id="tutorial_pg_conn",
        sql="""
            CREATE TABLE IF NOT EXISTS employees (
                "Serial Number" NUMERIC PRIMARY KEY,
                "Company Name" TEXT,
                "Employee Markme" TEXT,
                "Description" TEXT,
                "Leave" INTEGER
            );""",
    )

    create_employees_temp_table = SQLExecuteQueryOperator(
        task_id="create_employees_temp_table",
        conn_id="tutorial_pg_conn",
        sql="""
            DROP TABLE IF EXISTS employees_temp;
            CREATE TABLE employees_temp (
                "Serial Number" NUMERIC PRIMARY KEY,
                "Company Name" TEXT,
                "Employee Markme" TEXT,
                "Description" TEXT,
                "Leave" INTEGER
            );""",
    )

    @task
    def get_data():
        # NOTE: configure this as appropriate for your airflow environment
        data_path = "/opt/airflow/dags/files/employees.csv"
        os.makedirs(os.path.dirname(data_path), exist_ok=True)

        # Check if the file exists
        if not os.path.exists(data_path):
            # Download the file if it doesn't exist
            url = "https://raw.githubusercontent.com/apache/airflow/main/airflow-core/docs/tutorial/pipeline_example.csv"
            response = requests.request("GET", url)
            with open(data_path, "w") as file:
                file.write(response.text)

        postgres_hook = PostgresHook(postgres_conn_id="tutorial_pg_conn")
        conn = postgres_hook.get_conn()
        cur = conn.cursor()
        with open(data_path, "r") as file:
            cur.copy_expert(
                "COPY employees_temp FROM STDIN WITH CSV HEADER DELIMITER AS ',' QUOTE '\"'",
                file,
            )
        conn.commit()

    @task_group()
    def ingest_to_cloud():
        convert_to_parquet() >> upload_to_gcs() >> create_bigquery_external_table()

    @task
    def convert_to_parquet():
        # Paths for the CSV and Parquet files
        data_path = "/opt/airflow/dags/files/employees.csv"
        parquet_path = "/opt/airflow/dags/files/employees.parquet"

        # Read the CSV file and convert to Parquet
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            df.to_parquet(parquet_path, index=False)
        else:
            raise FileNotFoundError(f"{data_path} does not exist.")

    @task
    def upload_to_gcs():
        parquet_path = "/opt/airflow/dags/files/employees.parquet"

        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Parquet file {parquet_path} does not exist.")

        # GCS configuration
        blob_name = f"employees/processed/employees.parquet"

        try:
            gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)

            # Upload file to GCS
            gcs_hook.upload(
                bucket_name=BUCKET_NAME,
                object_name=blob_name,
                filename=parquet_path,
                mime_type="application/octet-stream"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to upload to GCS: {str(e)}")

        print("Parquet file uploaded successfully.")

    @task
    def create_bigquery_external_table():
        """Create an external table in BigQuery pointing to the GCS parquet file"""

        # BigQuery configuration
        table_id = "employees_external"
        blob_name = f"employees/processed/employees.parquet"
        source_uri = f"gs://{BUCKET_NAME}/{blob_name}"

        try:
            # Initialize BigQuery hook
            bq_hook = BigQueryHook(
                gcp_conn_id=GCP_CONN_ID,
                use_legacy_sql=False
            )

            table_resource = {
                "tableReference": {
                    "projectId": PROJECT_ID,
                    "datasetId": DATASET_ID,
                    "tableId": table_id,
                },
                "externalDataConfiguration": {
                    "sourceFormat": "PARQUET",
                    "sourceUris": [
                        source_uri
                    ],
                    "autodetect": True
                },
                "description": "External table from Parquet files in GCS"
            }

            # Create the external table using create_table
            bq_hook.create_table(
                dataset_id=DATASET_ID,
                table_id=table_id,
                table_resource=table_resource)

        except Exception as e:
            raise RuntimeError(f"Failed to create BigQuery external table: {str(e)}")

    @task
    def merge_data():
        query = """
            INSERT INTO employees
            SELECT *
            FROM (
                SELECT DISTINCT *
                FROM employees_temp
            ) t
            ON CONFLICT ("Serial Number") DO UPDATE
            SET
              "Employee Markme" = excluded."Employee Markme",
              "Description" = excluded."Description",
              "Leave" = excluded."Leave";
        """
        try:
            postgres_hook = PostgresHook(postgres_conn_id="tutorial_pg_conn")
            conn = postgres_hook.get_conn()
            cur = conn.cursor()
            cur.execute(query)
            conn.commit()
            return 0
        except Exception as e:
            return 1

    chain(
        [create_employees_table, create_employees_temp_table],
        get_data(),
        [ingest_to_cloud(), merge_data()],
    )

dag = ProcessEmployees()
