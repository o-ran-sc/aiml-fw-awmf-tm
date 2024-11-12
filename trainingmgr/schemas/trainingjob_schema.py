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

from trainingmgr.schemas import ma
from trainingmgr.models import TrainingJob

class TrainingJobSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TrainingJob
        include_relationships = True
        load_instance = True
    
    def preprocessData(self, json_data):
        '''
            Converts the recieved json payload to a schema that can processed by TrainingJob model.
            Input may look like:
                {
                    "trainingjob_name": "check2",
                    "modelName": "",
                    "modelLocation": "",
                    "trainingDataset": "",
                    "validationDataset": "",
                    "trainingConfig": {
                        "is_mme" : "this.state.isMme",
                        "description": "This is something",
                        "dataPipeline": {
                            "featureGroup_name": "base1",
                            "query_filter": "",
                            "arguments": "{'epochs': '1'}"
                        },
                        "trainingPipeline": {
                                "pipeline_name": "qoe_Pipeline",
                                "pipeline_version": "2",
                                "enable_versioning": "false"
                        }
                    }
                }
        '''
        try:
            trainingConfig = json_data["trainingConfig"]
            processed_data = {
                "trainingjob_name" : json_data["trainingjob_name"],
                "model_name": json_data["modelName"], # in R1AP v6.0, model_name is camelCased
                "description": trainingConfig["description"],
                "is_mme": trainingConfig["is_mme"],
                # DataPipeline-Configurations
                "datalake_source": "InfluxSource", # Constant, In future, 'datalake' to be taken from featureGroup
                "feature_group_name": trainingConfig["dataPipeline"]["feature_group_name"],
                "query_filter": trainingConfig["dataPipeline"]["query_filter"],
                "arguments": trainingConfig["dataPipeline"]["arguments"],
                # trainingPipeline-Configurations
                "pipeline_name" : trainingConfig["trainingPipeline"]["pipeline_name"],
                "pipeline_version" : trainingConfig["trainingPipeline"]["pipeline_version"],
                "enable_versioning" : trainingConfig["trainingPipeline"]["enable_versioning"],
                "experiment_name": "Default",  # Constant, This must be removed in the future
            }
            return processed_data
        except Exception as e:
            raise Exception("Error during preprocessing recieved json-data as per TrainingJobSchema| Error : " + str(e))
            
        