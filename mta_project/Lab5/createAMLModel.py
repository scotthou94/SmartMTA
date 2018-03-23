'''
Group: x007
Murshed Jamil Ahmed (mja2196)
Shijun Hou (sh3658)
Jiahong He (jh3863)
Robert Fea (rf2638)
IoT Lab 5
'''
# Creating aws machine learning model
# This program uploads the finalData.csv file to S3, and used it as a data source to train a binary 
# classification model
import time,sys,random

import boto3

import S3

sys.path.append('../utils')
import aws

TIMESTAMP  =  time.strftime('%Y-%m-%d-%H-%M-%S')
S3_BUCKET_NAME = "mtaedisondatax007"
S3_FILE_NAME = 'trainingData.csv'
S3_URI = "s3://{0}/{1}".format(S3_BUCKET_NAME, S3_FILE_NAME)
DATA_SCHEMA = "aml.csv.schema"

machineLearningClient = aws.getClient('machinelearning', 'us-east-1')

# Create a Data Source
dataSourceResponse = machineLearningClient.create_data_source_from_s3(
    DataSourceId='ds_id' + TIMESTAMP,
    DataSourceName='ml_data1',
    DataSpec={
        'DataLocationS3': S3_URI,
        'DataRearrangement': '{\"splitting\":{\"percentBegin\":10,\"percentEnd\":60}}',
        'DataSchemaLocationS3': "s3://{0}/{1}".format(S3_BUCKET_NAME, DATA_SCHEMA)
    },
    ComputeStatistics=True
)

# Create an ML model with a data source
modelResponse = machineLearningClient.create_ml_model(
    MLModelId='ml_id'+TIMESTAMP,
    MLModelName='ml_model1',
    MLModelType='BINARY',
    TrainingDataSourceId = 'ds_id' + TIMESTAMP,
)

# Evaluate the data source
evaluationResponse = machineLearningClient.create_evaluation(
    EvaluationId='eval_id'+TIMESTAMP,
    EvaluationName='ml_eval1',
    MLModelId='ml_id'+TIMESTAMP,
    EvaluationDataSourceId='ds_id' + TIMESTAMP,
)

# Create the endpoint for real time requests
endpointResponse = machineLearningClient.create_realtime_endpoint(
    MLModelId='ml_id'+TIMESTAMP,
)