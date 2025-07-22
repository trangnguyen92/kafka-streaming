```bash
docker-compose up airflow-init
docker-compose up
```

## Configure Postgres Connection
- Open the Airflow UI at `http://localhost:8080`
- Log in with the default credentials:
  - Username: `airflow`
  - Password: `airflow`
  - Note: You can change these credentials in the `docker-compose.yaml` file.
  - Go to Admin -> Connections
  - Click on "Create" to add a new connection
  - Connection ID: `tutorial_pg_conn`
  - Connection Type: `Postgres`
  - Host: `postgres`
  - Login: `airflow`
  - Password: `airflow`
  - Database: `airflow`

## Configure GCP connection
### Setup Google Cloud Service Account
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Navigate to "IAM & Admin" -> "Service Accounts".
4. Click on "Create Service Account".
5. Enter a name for the service account (e.g., `airflow-trang-sa`).
6. Assign the role `Owner` the tasks.
7. Click "Done" to create the service account.
8. Create a key for the service account:
   - Click on the service account you just created.
   - Go to the "Keys" tab.
   - Click "Add Key" -> "Create new key".
   - Choose JSON format and click "Create".
   - Save the downloaded JSON file securely.

### Configure Airflow to use the GCP Service Account
- Go to Admin -> Connections
- Click on "Create" to add a new connection
- Connection ID: `gcp_trang_default`
- Connection Type: `Google Cloud`
- Keyfile JSON: Paste the content of your GCP service account JSON key file here.

## Create a GCS bucket
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to "Storage" -> "Browser".
3. Click on "Create bucket".
4. Enter a unique name for your bucket (e.g., `airflow-trang-bucket-2`).
5. Choose a location for your bucket.
6. Click "Create" to create the bucket.


## Create a BigQuery dataset
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to "BigQuery".
3. Click on your project name in the left sidebar.
4. Click on "Create Dataset".
5. Enter a name for your dataset (e.g., `airflow_trang_dataset`).
6. Choose a data location.
7. Click "Create Dataset" to create the dataset.

## Run the DAG
- Open the Airflow UI at `http://localhost:8080`
- You should see the DAG `process_employees` in the list of DAGs.
- Turn on the DAG by toggling the switch next to it.
- Click on the DAG name to view its details.
- You can manually trigger the DAG by clicking on the "Trigger DAG" button.