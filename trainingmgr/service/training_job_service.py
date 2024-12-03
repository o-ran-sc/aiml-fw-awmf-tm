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
from trainingmgr.db.trainingjob_db import delete_trainingjob_by_id, create_trainingjob, get_trainingjob, get_trainingjob_by_modelId_db, \
change_steps_state
from trainingmgr.common.exceptions_utls import DBException, TMException
from trainingmgr.schemas import TrainingJobSchema
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States

trainingJobSchema = TrainingJobSchema()
trainingJobsSchema = TrainingJobSchema(many=True)

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

def create_training_job(trainingjob):
    try:
        create_trainingjob(trainingjob)
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
        #TODO: cancel training job from kubeflow training
        return delete_trainingjob_by_id(id=training_job_id)
    except Exception as err :
        raise DBException(f"delete_trainining_job failed with exception : {str(err)}")
    
def get_trainingjob_by_modelId(model_id):
    try:
        trainingjob = get_trainingjob_by_modelId_db(model_id)
        return trainingjob

    except Exception as err:
        raise DBException(f"get_trainingjob_by_modelId failed with exception : {str(err)}")
    
def get_steps_state(trainingjob_id):
    try:    
        trainingjob = get_trainingjob(trainingjob_id)
        return trainingjob.steps_state.states
    except Exception as err:
        raise DBException(f"get failed to get the status with exception : {str(err)}") 

def change_status_tj(trainingjob, step:str, state:str):
    try:
        change_steps_state(trainingjob, step, state)
    except DBException as err:
        raise TMException(f"change status of tj failed with exception : {str(err)}")
    
def get_data_extraction_in_progress_trainingjobs():
    result = {}
    try:
        trainingjobs = get_trainingjob()
        for trainingjob in trainingjobs:
            status = json.loads(trainingjob.steps_state.states)
            if status[Steps.DATA_EXTRACTION.name] == States.IN_PROGRESS.name:
                result[trainingjob] = "Scheduled"
    except Exception as err:
        raise DBException("get_data_extraction_in_progress_trainingjobs," + str(err))
    return result
