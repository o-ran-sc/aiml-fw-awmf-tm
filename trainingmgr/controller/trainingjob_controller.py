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
from flask import Blueprint, jsonify, request
from trainingmgr.service.training_job_service import delete_training_job, create_training_job, get_training_job, get_trainining_jobs

training_job_controller = Blueprint('training_job_controller', __name__)

@training_job_controller.route('/training-jobs/<int:training_job_id>', methods=['DELETE'])
def delete_trainingjob(training_job_id):
    print(f'delete training job : {training_job_id}')
    try:
        if delete_training_job(str(training_job_id)):
            print(f'training job with {training_job_id} is deleted successfully.')
            return '', 204
        else:
            print(f'training job with {training_job_id} does not exist.')
            return jsonify({
                'message': 'training job with given id is not found'
            }), 500 
         
    except Exception as e:
        return jsonify({
            'message': str(e)
        }), 500
    
@training_job_controller.route('/training-jobs', methods=['POST'])
def create_trainingjob():
    data = request.get_json()
    create_training_job(data)
    print(f'create traiing job: {data}')
    return '', 200

@training_job_controller.route('/training-jobs/', methods=['GET'])
def get_trainingjobs():
    print(f'get the trainingjobs')
    resp = get_trainining_jobs()
    return jsonify(resp), 200

@training_job_controller.route('/training-jobs/<int:training_job_id>', methods=['GET'])
def get_trainingjob(training_job_id):
    print(f'get the trainingjob correspoinding to id: {training_job_id}')
    return jsonify(get_training_job(training_job_id)), 200
