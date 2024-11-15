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
from trainingmgr.db.trainingjob_db import delete_trainingjob_by_id, create_trainingjob, get_trainingjob
from trainingmgr.common.exceptions_utls import DBException
from trainingmgr.schemas import TrainingJobSchema

trainingJobSchema = TrainingJobSchema()
trainingJobsSchema = TrainingJobSchema(many=True)

def get_training_job(training_job_id: int):
    tj =get_trainingjob(training_job_id)
    return trainingJobSchema.dump(tj)

def get_trainining_jobs():
    print(f'service layer triggers get')
    tjs = get_trainingjob()
    print(f'resp : {tjs}')
    result = trainingJobsSchema.dump(tjs)
    return result

def create_training_job(data):
    create_trainingjob(data)
    

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

