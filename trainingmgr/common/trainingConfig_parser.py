import json

def parse_dict_by_fields(data, fields):
    '''
        It parses the provided data (dicts) by the fields provided
        Example:
            data = {"a": 1, "b": {"c" : 4, "d" : {-1}}}
            fields = ["a", "b", "c"] = 4
            fields = ["a", "b", "d"] = -1
    '''
    try:
        cur = data
        for field in fields:
            cur = cur[field]
        return cur
    except Exception as e:
        raise Exception("Can't parse Fields: {} in Data : {}| recieved-error : {}".format(fields, data, e))
        
        
def __getLeafPaths():
    '''
        It returns paths possible to retrieve data
        Based on TrainingConfig Schema:
        {
            "is_mme" : false,
            "description": "This is something3",
            "dataPipeline": {
                "feature_group_name": "base2",
                "query_filter": "",
                "arguments": "{'epochs': '1'}"
            },
            "trainingPipeline": {
                    "pipeline_name": "qoe_Pipeline",
                    "pipeline_version": "2",
                    "enable_versioning": true
        }
    '''
    paths = {
        "is_mme": ["is_mme"],
        "description": ["description"],
        "feature_group_name": ["dataPipeline", "feature_group_name"],
        "query_filter" : ["dataPipeline", "query_filter"],
        "arguments" : ["dataPipeline", "arguments"],
        "pipeline_name": ["trainingPipeline", "pipeline_name"],
        "pipeline_version": ["trainingPipeline", "pipeline_version"],
        "enable_versioning": ["trainingPipeline", "enable_versioning"]
    }
    return paths

def prepocessTrainingConfig(trainingConfig):
    if (isinstance(trainingConfig, str)):
        return json.loads(trainingConfig)
    return trainingConfig

def validateTrainingConfig(trainingConfig):
    '''
        One way to Validate TrainingConfig is to see if each Leafpath exists or not
        Any other key:value pair than TrainingConfig Schema is not treated as invalid. 
    '''
    trainingConfig = prepocessTrainingConfig(trainingConfig)
    allPaths = __getLeafPaths()
    try:
        for fieldPath in allPaths.values():
            parse_dict_by_fields(trainingConfig, fieldPath)
        return True
    except Exception as e:
        print("Unable to Validate Error: ", e)
        return False
    
def getField(trainingConfig, fieldname):
    trainingConfig = prepocessTrainingConfig(trainingConfig)
    fieldPath = __getLeafPaths()[fieldname]
    return parse_dict_by_fields(trainingConfig, fieldPath)
    