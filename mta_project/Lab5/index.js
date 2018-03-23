/**
Group: x007
Murshed Jamil Ahmed (mja2196)
Shijun Hou (sh3658)
Jiahong He (jh3863)
Robert Fea (rf2638)
IoT Lab 5
*/

// Modified from AWS Github Code
console.log("Setting handler function . . . ")
exports.handler = function(event, context) {
    // Set up AWS tools and configuration
    var AWS = require('aws-sdk');
    var ml = new AWS.MachineLearning();
    var endpointUrl = 'https://realtime.machinelearning.us-east-1.amazonaws.com';
    var mlModelId = 'ml-emNRYppQiIZ';
    var numMessagesToBeProcessed = event.Records.length;

    // Function to call prediction endpoint
    var callPredict = function(mtaData) {
        console.log('Calling prediction service');
        ml.predict({
            Record: mtaData,
            PredictEndpoint: endpointUrl,
            MLModelId: mlModelId
        }, function(err, data) {
            console.error('Prediction endpoint has responded')
            if (err) {
                console.error(err);
                context.done(null, 'Call to prediction service failed');
            } else {
                console.log('Prediction successful');
                console.log(data)
                if (data.Prediction.predictedLabel === '1') {
                    console.log("SWITCH to the express train")
                } else {
                    console.log("STAY on the local train")
                }
            }
        });
    }


    var processRecords = function() {
        for (var i = 0; i < numMessagesToBeProcessed; ++i) {
            // Amazon Kinesis data is base64 encoded, so must be decoded first
            var encodedPayload = event.Records[i].kinesis.data;
            var payload = new Buffer(encodedPayload, 'base64').toString('utf-8');
            console.log('Decoded Payload: ')
            console.log(payload)

            try {
                var parsedPayload = JSON.parse(payload);
                console.log('JSON Parsed Object: ')
                console.log(parsedPayload)

                //remove '' and 'first' labels
                delete parsedPayload['first'];
                delete parsedPayload['']

                callPredict(parsedPayload);
            } catch (err) {
                console.error('An error has occurred parsing the payload from Kinesis')
                console.log(err, err.stack);
                context.done(null, "failed payload" + payload);
            }
        }
    }

    var checkRealtimeEndpoint = function(err, data) {
        if (err) {
            console.error(err);
            context.done(null, 'Failed to fetch endpoint status and url.');
        } else {
            var endpointInfo = data.EndpointInfo;
            console.log("ML Endpoint Data: ")
            console.log(endpointInfo)

            if (endpointInfo.EndpointStatus === 'READY') {
                endpointUrl = endpointInfo.EndpointUrl;
                console.log('Endpoint URL :' + endpointUrl);
                processRecords();
            } else {
                console.log('Endpoint status : ' + endpointInfo.EndpointStatus);
                context.done(null, 'End point is not Ready.');
            }
        }
    };

    ml.getMLModel({
            MLModelId: mlModelId,
            Verbose: true
        },
        checkRealtimeEndpoint
    );
    //context.succeed("Successfully processed " + event.Records.length + " record.");
};
