import os
import sys
import boto3
import pprint
from datetime import datetime
import json
import psycopg2

EventID = "http://docs.amazonwebservices.com/AmazonRDS/latest/UserGuide/USER_Events.html#RDS-EVENT-0002"

def get_db_password(stage,service):
    secret_id = f"{stage}/{service}-service/rdscredential"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager',region_name='ap-southeast-2')
    get_secret_value_response = client.get_secret_value(SecretId=secret_id)
    secret = get_secret_value_response['SecretString']
    json_secret = json.loads(secret)
    # print(f"json_secret:{json_secret}")
    password = json_secret["password"]
    # print(f"password:{password}")
    return password

def connect_to_db_and_query(stage, service, target_db, endpoint_suffix):
    pwd = get_db_password(stage,service)
    host = f"{target_db}{endpoint_suffix}"
    conn = psycopg2.connect(f"host={host} dbname={service} user={service}-service password={pwd} connect_timeout=10 options='-c statement_timeout=5000'") 
    conn.autocommit = True
    query = "SELECT nspname AS schemaname,relname,reltuples FROM pg_class C LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace) WHERE nspname NOT IN ('pg_catalog', 'information_schema') AND relkind='r' ORDER BY reltuples DESC;"
    try:
        cur = conn.cursor()
        print(f"Executing *** {query} *** in database:{host}")
        cur.execute(query)
        cur.close()
    except:
        print("Error:", sys.exc_info()[0])

    conn.close()    

def listen_to_events(event, dbname, endpoint_suffix, stage, service):
    date = datetime.now().strftime("%Y-%m-%d")
    target_db = f"{dbname}-rcvred-{date}"
    try:
        # print(event)
        message_json = event["Records"][0]["Sns"]["Message"]
        # print(message_json)
        # pprint.pprint(message_json)
        message_dict = json.loads(message_json)
        event_id = message_dict["Event ID"]
        print(event_id)
        source_id = message_dict["Source ID"]
        print(source_id)

        if event_id == EventID and source_id == target_db:
           print(f"db:{target_db} is ready") 
           connect_to_db_and_query(stage, service, target_db, endpoint_suffix)
    except:
        print("Error:", sys.exc_info()[0])

def do(event, context):
    
    dbname = os.environ["DB_NAME"]
    service = os.environ["SERVICE"]
    stage = os.environ["STAGE"]
    endpoint_suffix = os.environ["EP_SUFFIX"]

    listen_to_events(event, dbname, endpoint_suffix, stage, service)

if __name__ == "__main__":
    do('', '')  