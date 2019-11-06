# import json
import os
import boto3
from datetime import datetime

def restore_snapshot(dbname,sg,subnet_group):
    date_time = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    target_db = "{}-rcvred-{}".format(dbname, date_time)
    session = boto3.session.Session()
    client = session.client(service_name='rds',region_name='ap-southeast-2')
    response = client.restore_db_instance_to_point_in_time(
    SourceDBInstanceIdentifier=dbname,
    TargetDBInstanceIdentifier=target_db,
    UseLatestRestorableTime=True,
    CopyTagsToSnapshot=True,
    MultiAZ=False,
    VpcSecurityGroupIds=[
        sg
    ],
    DBSubnetGroupName=subnet_group
    # ,IAMDatabaseAuthenticationEnabled=True
    )

    return response

    

def do(event, context):
    dbname = os.environ["DB_NAME"]
    sg = os.environ["DB_SECURITY_GROUP_ID"]
    subnet_group = os.environ["DB_SUBNET_GROUP_NAME"]
    response_body = restore_snapshot(dbname,sg, subnet_group)

    return response_body

if __name__ == "__main__":
    do('', '')  