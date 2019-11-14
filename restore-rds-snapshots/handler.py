import os
import sys
import boto3
import pprint
from datetime import datetime

def restore_snapshot(dbname, db_sg, lambda_sg, subnet_group):
    date = datetime.now().strftime("%Y-%m-%d")
    target_db = f"{dbname}-rcvred-{date}"

    session = boto3.session.Session()
    client = session.client(service_name='rds',region_name='ap-southeast-2')
    try:
        response = client.restore_db_instance_to_point_in_time(
        SourceDBInstanceIdentifier=dbname,
        TargetDBInstanceIdentifier=target_db,
        UseLatestRestorableTime=True,
        CopyTagsToSnapshot=True,
        MultiAZ=False,
        VpcSecurityGroupIds=[
            db_sg,
            lambda_sg
        ],
        DBSubnetGroupName=subnet_group
        )

        restored_db_snapshot =  response["DBInstance"]["DBInstanceIdentifier"]
        print(f"db:{restored_db_snapshot} is being restored")
    except:
        print(f"Error: {sys.exc_info()[0]}")
        response = {"DBInstance": {"DBInstanceIdentifier": target_db, "DBInstanceStatus": "exists" }}   

    return response

def subscription_exists():
    session = boto3.session.Session()
    client = session.client(service_name='rds',region_name='ap-southeast-2')
    try:
        response = client.describe_event_subscriptions(SubscriptionName='restore-snapshot-subs')
    except: 
        print("SubscriptionName does not exists")
        return False
    
    if response:
       return True

    return False

def create_event_subscription(dbname,stage):
    session = boto3.session.Session()
    client = session.client(service_name='rds',region_name='ap-southeast-2')
    sts_client = session.client("sts", region_name="ap-southeast-2")
    account_id = sts_client.get_caller_identity()["Account"]

    date = datetime.now().strftime("%Y-%m-%d")
    target_db = f"{dbname}-rcvred-{date}"
    
    sns_arn = f"arn:aws:sns:{session.region_name}:{account_id}:rds-events-dispatcher"
    response = client.create_event_subscription(
        SubscriptionName='restore-snapshot-subs',
        SnsTopicArn=sns_arn,
        SourceType='db-instance',
        EventCategories=[
            'backup',
        ],
        SourceIds=[
            target_db
        ],
        Enabled=True,
        Tags=[
            {
                'Key': 'environment',
                'Value': stage
            },
        ]
    )

    return response

def delete_event_subscription():
    session = boto3.session.Session()
    client = session.client(service_name='rds',region_name='ap-southeast-2')

    response = client.delete_event_subscription(SubscriptionName='restore-snapshot-subs')

    return response    

def restore(event, context):
    dbname = os.environ["DB_NAME"]
    db_sg = os.environ["DB_SECURITY_GROUP_ID"]
    lambda_sg = os.environ["LAMBDA_SECURITY_GROUP_ID"]
    subnet_group = os.environ["DB_SUBNET_GROUP_NAME"]
    stage = os.environ["STAGE"]

    restore_snapshot(dbname, db_sg, lambda_sg, subnet_group)
    
    if subscription_exists():
       delete_event_subscription()
       print("subscription (restore-snapshot-subs) deleted") 


    response_create_subs = create_event_subscription(dbname,stage)

    subscription_id = response_create_subs["EventSubscription"]["CustSubscriptionId"]
    status = response_create_subs["EventSubscription"]["Status"]

    result = f"the subscription {subscription_id} is {status}" 
    print(result)

    return {"result": result}

if __name__ == "__main__":
    restore('', '')  