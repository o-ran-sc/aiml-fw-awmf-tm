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
from trainingmgr.db.pipeline_mgr import PipelineInfo, PipelineMgr
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig


pipelineMgrObj = PipelineMgr()

LOGGER = TrainingMgrConfig().logger
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
    
    
    