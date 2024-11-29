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
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.db.pipeline_mgr import PipelineMgr
from trainingmgr.models.pipeline_info import PipelineInfo
from werkzeug.utils import secure_filename
import os

pipelineMgrObj = PipelineMgr()

LOGGER = TrainingMgrConfig().logger

def get_all_pipelines():
    allPipelines = pipelineMgrObj.get_all_pipelines()
    return allPipelines

def get_single_pipeline(pipeline_name):
    allPipelines = pipelineMgrObj.get_all_pipelines()
    for pipeline_info in allPipelines.get('pipelines', []):
        if pipeline_info['display_name'] == pipeline_name:
            
            return PipelineInfo(
                pipeline_id=pipeline_info['pipeline_id'],
                display_name=pipeline_info['display_name'],
                description=pipeline_info['description'],
                created_at=pipeline_info['created_at']
            ).to_dict()
    
    LOGGER.warning(f"Pipeline '{pipeline_name}' not found")
    return None

def get_all_pipeline_versions(pipeline_name):
    # First, Check if pipeline exist or not
    pipeline_info = get_single_pipeline(pipeline_name)
    if pipeline_info is not None:
        versions_dict = pipelineMgrObj.get_all_pipeline_versions(pipeline_name)
        return versions_dict['versions_list']
    else:
        return None
    
def upload_pipeline_service(pipeline_name, uploaded_file, description):
    uploaded_file_path = "/tmp/" + secure_filename(uploaded_file.filename)
    uploaded_file.save(uploaded_file_path)
    LOGGER.debug("File uploaded :%s", uploaded_file_path)
    try:
        pipelineMgrObj.upload_pipeline_file(pipeline_name, uploaded_file_path, description)
    except Exception as err:
        raise err
    finally:
        # Since, the file was saved, The file MUST be deleted no matter what is status
        if uploaded_file_path and os.path.isfile(uploaded_file_path):
            LOGGER.debug("Deleting %s", uploaded_file_path)
            if uploaded_file_path != None:
                os.remove(uploaded_file_path)