# Group: x007
# Murshed Jamil Ahmed (mja2196)
# Shijun Hou (sh3658)
# Jiahong He (jh3863)
# Robert Fea (rf2638)
# IoT Lab 2, part 2

import boto
import boto.dynamodb2
import mraa
import time
import json
from boto.dynamodb2.items import Item
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey, BaseSchemaField

DYNAMO_TABLE_NAME = "x007_table" #"x007_table" #YOUR TABLE NAME
ACCOUNT_ID = "338983078332" #YOUR ACCOUNT ID
IDENTITY_POOL_ID = "us-east-1:cac8bed2-325e-4f1d-bcb4-ef3827774540" #YOUR IDENTITY POOL ID
ROLE_ARN = "arn:aws:iam::338983078332:role/Cognito_edisonDemoKinesisUnauth_Role" #YOUR ROLE_ARN


class dynamoMethods:
    def __init__(self, dbName):
        self.table_dynamo = None
        try:
            #1. create new table
            self.table_dynamo = Table.create(dbName, schema=[HashKey('CUID')], 
                    connection=client_dynamo) #HINT: Table.create; #HINT 2: Use CUID as your hashkey
            #self.table_dynamo = client_dynamo.create_table(name=dbName, schema=s)
            print "New Table Created"
        except Exception as e:
            #2.table already exists, so get the table
            self.table_dynamo = Table(dbName, connection=client_dynamo) #HINT: Remember to use "connection=client.dynamo"
            '''
            self.table_dynamo.put_item(data={
                'CUID': 'sh3658',
                'name': 'scott',
                'password': 'pwd',
                })
            '''
            print "Table Already Exists"
    def dynamoAdd(self, cuid, name, password):
        # Check if the cuid exists in the database.
        user = None
        try:
            print 'try to get item'
            user = self.table_dynamo.get_item(CUID=cuid)#, name=name, password=password)#, name=name, password=password)
            print "Found user."
            print user
        except Exception as e:
            print e

        # If the CUID already exists inside db, perform a partial update on the entry.
        if user != None and user['CUID'] == cuid:
            user['name'] = name
            user['password'] = password
            try:
                user.partial_save()
                print "Updated entry: " + cuid
            except Exception as e:
                print e
        # Otherwise, create a new entry
        else:
            try:
                self.table_dynamo.put_item(data={
                        'CUID' : cuid,
                        'name' : name,
                        'password' : password,
                    })
                print "New entry created."
            except Exception as e:
                print e

    def dynamoDelete(self, cuid):
        ####################################################################
        # YOUR CODE HERE
        #1. Check table for entries that have the same CUID, if so, DELETE
        ####################################################################
        
        try:
            user = self.table_dynamo.get_item(CUID=cuid)#, name=name, password=password)#, name=name, password=password)
            self.table_dynamo.delete_item(CUID=cuid)
            print 'Item deleted'
        except Exception as e:
            print e
    def dynamoViewAll(self):
        string_db = "CUID: NAME\n"
        print string_db
        entries = self.table_dynamo.scan()
        for entry in entries:
            print entry['CUID'], ':', entry['name']

        #1. Get all entries in the table
        #2. Print the CUID: NAME for each entry
        ####################################################################

####################################################################
# DON'T MODIFY BELOW HERE -----------------------------------------#
####################################################################



cognito = boto.connect_cognito_identity()
cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(cognito_id['IdentityId'])

sts = boto.connect_sts()
assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])

client_dynamo = boto.dynamodb2.connect_to_region(
        'us-east-1',
        aws_access_key_id=assumedRoleObject.credentials.access_key,
        aws_secret_access_key=assumedRoleObject.credentials.secret_key,
        security_token=assumedRoleObject.credentials.session_token)

#print 'existing tables are:', client_dynamo.list_tables()
DB = dynamoMethods(DYNAMO_TABLE_NAME)
# debug
#table = Table('x007_table', client_dynamo)
#item = table.get_item(cuid = '1')

state = 0
input_cuid = None
input_name = None
input_password = None

def get_prompt(state_var):
    if state_var == 0:
        return "Choose an option.\n1. Add to DB\n2. Delete from DB\n3. ViewDB\n"
    elif state_var == 1:
        return "Enter CUID to add: "
    elif state_var == 2:
        return "Enter name to add: "
    elif state_var == 3:
        return "Enter password: "
    elif state_var == 4:
        return "Enter CUID to delete: "
    else:
        return "Bad command..."

try:
    while True:
        prompt = get_prompt(state)
        ans = raw_input(prompt)

        if state == 0:
            if ans == "1":
                state = 1
            elif ans == "2":
                state = 4
            elif ans == "3":
                state = 0
                DB.dynamoViewAll()
            else:
                print "Unsupported command.\n"
        elif state == 1:
            state = 2
            input_cuid = ans
        elif state == 2:
            state = 3
            input_name = ans
        elif state == 3:
            state = 0
            input_password = ans
            DB.dynamoAdd(input_cuid, input_name, input_password)
        elif state == 4:
            state = 0
            input_cuid = ans
            DB.dynamoDelete(input_cuid)
        else:
            state = 0
            print "Something is wrong."
except KeyboardInterrupt:
    exit
