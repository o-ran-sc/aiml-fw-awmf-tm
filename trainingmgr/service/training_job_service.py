# ==================================================================================
#
#       Copyright (c) 2024 Samsung Electronics Co., Ltd. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ==================================================================================
import json
from threading import Lock
from flask_api import status
from flask import jsonify
from trainingmgr.common.trainingmgr_operations import data_extraction_start, notification_rapp
from trainingmgr.db.model_db import get_model_by_modelId
from trainingmgr.db.trainingjob_db import change_state_to_failed, delete_trainingjob_by_id, create_trainingjob, get_trainingjob,\
change_steps_state, change_field_value, get_field_value, change_steps_state_df, changeartifact, get_trainingjobs_by_model_id_db
from trainingmgr.common.exceptions_utls import DBException, TMException
from trainingmgr.common.trainingConfig_parser import getField, setField
from trainingmgr.handler.async_handler import DATAEXTRACTION_JOBS_CACHE
from trainingmgr.schemas import TrainingJobSchema
from trainingmgr.common.trainingmgr_util import check_key_in_dictionary, get_one_word_status, get_step_in_progress_state
from trainingmgr.constants import Steps, States
from trainingmgr.service.pipeline_service import terminate_training_service
from trainingmgr.service.featuregroup_service import  get_featuregroup_by_name, get_featuregroup_from_inputDataType
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.constants import Steps, States
from sqlalchemy.orm.exc import NoResultFound

trainingJobSchema = TrainingJobSchema()
trainingJobsSchema = TrainingJobSchema(many=True)
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
LOCK = Lock()
MIMETYPE_JSON = "application/json"
LOGGER = TrainingMgrConfig().logger

def get_training_job(training_job_id: int):
    try:
        tj =get_trainingjob(training_job_id)
        return tj
    except DBException as err:
        raise TMException(f"get_training_job by id failed with exception : {str(err)}")

def get_trainining_jobs():
    try:
        tjs = get_trainingjob()
        return tjs
    except DBException as err:
        raise TMException(f"get_training_jobs failed with exception : {str(err)}")

def create_training_job(trainingjob, registered_model_dict):
    try:
        # First-of all we need to resolve featureGroupname from inputDatatype
        training_config = trainingjob.training_config
        feature_group_name = getField(training_config, "feature_group_name")
        if feature_group_name == "":
            # User has not provided feature_group_name, then it MUST be deduced from Registered InputDataType
            feature_group_name = get_featuregroup_from_inputDataType(registered_model_dict['modelInformation']['inputDataType'])
            trainingjob.training_config = json.dumps(setField(training_config, "feature_group_name", feature_group_name))
            LOGGER.debug("Training Config after FeatureGroup deduction --> " + trainingjob.training_config)

        modelId = trainingjob.modelId
        modelinfo = get_model_by_modelId(modelId.modelname, modelId.modelversion)

        if modelinfo != None:
            trainingjob.model_id = modelinfo.id
            trainingjob.modelId = modelinfo

        create_trainingjob(trainingjob)
        
        LOGGER.debug("trainingjob id is: "+str(trainingjob.id))
        
        return training(trainingjob)
    except DBException as err:
        raise TMException(f"create_training_job failed with exception : {str(err)}")
    

def delete_training_job(training_job_id : int):
    """
    This function handles the service to delete the training job resource by id.
    
    Args:
        training_job_id (int): id of training job.
    
    Returns:
        bool: boolean to represent if the trainingjob is deleted.
    
    Raises:
        DBException: If there error during operation. 

    """
    try:
        # Signal Deletion in Progress
        tj = get_trainingjob(training_job_id)
        if tj is None:
            return False
        change_field_value(training_job_id, "deletion_in_progress", True)
        steps_state =  json.loads(tj.steps_state.states)
        overall_status = get_one_word_status(steps_state)
        
        if overall_status == States.IN_PROGRESS.name:
            step_in_progress_state = get_step_in_progress_state(steps_state)
            if step_in_progress_state == Steps.DATA_EXTRACTION:
                pass
                # TODO: Remove the job from DATAEXTRACTION_JOBS_CACHE to signal not to check its status
                # with LOCK:
                #     DATAEXTRACTION_JOBS_CACHE.pop(trainingjob_name)
            elif (step_in_progress_state == Steps.TRAINING or (step_in_progress_state == Steps.DATA_EXTRACTION_AND_TRAINING and tj.run_id is not None)):
                # Signal the Kf-Adapter to terminate the 
                response = terminate_training_service(tj.run_id)
                LOGGER.debug("Deletion-Response : " + response.text)

        isDeleted = delete_trainingjob_by_id(id=training_job_id)
        if isDeleted:
            return True
        else:
            return False
    except NoResultFound :
        return False
    except Exception as err :
        raise DBException(f"delete_trainining_job failed with exception : {str(err)}")


def get_steps_state(trainingjob_id):
    try:    
        trainingjob = get_trainingjob(trainingjob_id)
        return trainingjob.steps_state.states
    except Exception as err:
        raise DBException(f"get failed to get the status with exception : {str(err)}") 

def change_status_tj(trainingjob_id, step:str, state:str):
    try:
        change_steps_state(trainingjob_id, step, state)
    except DBException as err:
        raise TMException(f"change status of tj failed with exception : {str(err)}")
    
def change_status_tj_dif(trainingjob_id, step:str, state:str):
    try:
        change_steps_state_df(trainingjob_id, step, state)
    except DBException as err:
        raise TMException(f"change status of tj dif failed with exception : {str(err)}")


def change_update_field_value(trainingjob_id, field, value):
    try:
        change_field_value(trainingjob_id, field, value)
    except Exception as err:
        raise TMException(f"failed to update the filed with exception : {str(err)}")
    
def update_artifact_version(trainingjob_id, artifact_version : str, level : str):
    try: 
        major, minor , patch= map(int, artifact_version.split('.'))
        if level =="major":
            major += 1
        elif level =="minor":
            minor +=1
        elif level =="patch":
            patch +=1
        else :
            raise ValueError("Invalid level passed. choose major or minor")
        
        new_artifact_version = f'{major}.{minor}.{patch}'
        
        changeartifact(trainingjob_id, new_artifact_version)
        return f'{major}.{minor}.{patch}'
    except Exception as err:
        raise TMException(f"failed to update_artifact_version with exception : {str(err)}")
    
def training(trainingjob):
    """
    Rest end point to start training job.
    It calls data extraction module for data extraction and other training steps

    Args in function:
        training_job_id: str
            id of trainingjob.

    Args in json:
        not required json

    Returns:
        json:
            training_job_id: str
                name of trainingjob
            result: str
                route of data extraction module for getting data extraction status of
                given training_job_id .
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """

    LOGGER.debug("Request for training trainingjob id %s ", trainingjob.id)
    try:

        training_job_id = trainingjob.id
        featuregroup_name = getField(trainingjob.training_config, "feature_group_name")
        featuregroup= get_featuregroup_by_name(featuregroup_name)
        LOGGER.debug("featuregroup name is: "+featuregroup.featuregroup_name)
        feature_list_string = featuregroup.feature_list
        influxdb_info_dic={}
        influxdb_info_dic["host"]=featuregroup.host
        influxdb_info_dic["port"]=featuregroup.port
        influxdb_info_dic["bucket"]=featuregroup.bucket
        influxdb_info_dic["token"]=featuregroup.token
        influxdb_info_dic["db_org"] = featuregroup.db_org
        influxdb_info_dic["source_name"]= featuregroup.source_name
        _measurement = featuregroup.measurement
        query_filter = getField(trainingjob.training_config, "query_filter")
        datalake_source = {featuregroup.datalake_source: {}} # Datalake source should be taken from FeatureGroup (not TrainingJob)
        LOGGER.debug('Starting Data Extraction...')
        de_response = data_extraction_start(TRAININGMGR_CONFIG_OBJ, training_job_id,
                                        feature_list_string, query_filter, datalake_source,
                                        _measurement, influxdb_info_dic, featuregroup.featuregroup_name)
        if (de_response.status_code == status.HTTP_200_OK ):
            LOGGER.debug("Response from data extraction for " + \
                    str(training_job_id) + " : " + json.dumps(de_response.json()))
            change_status_tj(trainingjob.id,
                                Steps.DATA_EXTRACTION.name,
                                States.IN_PROGRESS.name)
            notification_rapp(trainingjob.id)
            with LOCK:
                DATAEXTRACTION_JOBS_CACHE[trainingjob.id] = "Scheduled"
        elif( de_response.headers['content-type'] == MIMETYPE_JSON ) :
            errMsg = "Data extraction responded with error code."
            LOGGER.error(errMsg)
            json_data = de_response.json()
            LOGGER.debug(str(json_data))
            change_state_to_failed(training_job_id)
            if check_key_in_dictionary(["result"], json_data):
                return jsonify({
                    "message": json.dumps({"Failed":errMsg + json_data["result"]})
                }), 500
            else:
                return jsonify({
                    "message": errMsg
                }), 500
        else:
                return jsonify({
                    "message": "failed data extraction"
                }), 500
    except TMException as err:
        change_state_to_failed(training_job_id)
        if "No row was found when one was required" in str(err):
            return jsonify({
                    'message': f"No featuregroup found with featuregroup name {featuregroup_name}"
                }), 404 
    except Exception as e:
        LOGGER.debug("Error is training, job id: " + str(training_job_id)+" " + str(e)) 
        change_state_to_failed(training_job_id)
        return jsonify({
            'message': str(e)
        }), 500  
        
    response =  jsonify(trainingJobSchema.dump(trainingjob))
    response.headers['Location'] = "ai-ml-model-training/v1/training-jobs/" + str(training_job_id)
    return response, 201

    
def fetch_pipelinename_and_version(type, training_config):
    try:
        if type =="training":
         return getField(training_config, "training_pipeline_name"), getField(training_config, "training_pipeline_version")
        else :
            return getField(training_config, "retraining_pipeline_name"), getField(training_config, "retraining_pipeline_version")
    except Exception as err:
        raise TMException(f"cant fetch training or retraining pipeline name or version from trainingconfig {training_config}| Error: " + str(err))
    

def fetch_trainingjob_infos_from_model_id(model_name, model_version):
    try:
        trainingjob_infos = get_trainingjobs_by_model_id_db(model_name, model_version)
        return trainingjob_infos
    except Exception as err:
        raise TMException(f"Can't fetch trainingjob_infos from model_name {model_name} and model_version {model_version}| Error: " + str(err))
    
    
def update_model_metrics_service(trainingjob_id, model_metrics):
    try:
        model_metrics_str = json.dumps(model_metrics)
        change_field_value(trainingjob_id, "model_metrics", model_metrics_str)
    except Exception as err:
        raise TMException(f"Can't Update model_metrics for trainingjob_id {trainingjob_id}| Error: " + str(err))
    
def get_model_metrics_service(trainingjob_id):
    try:
        model_metrics_str = get_field_value(trainingjob_id, "model_metrics")
        return json.loads(model_metrics_str)
    except Exception as err:
        raise TMException(f"Can't get_model_metrics_service for trainingjob_id {trainingjob_id}| Error: " + str(err))