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
from trainingmgr.models.trainingjob import ModelID

from marshmallow import pre_load

class ModelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ModelID
        load_instance = True
class TrainingJobSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TrainingJob
        load_instance = True
    
    modelId = ma.Nested(ModelSchema)
    
    @pre_load
    def processModelId(self, data, **kwargs):
        modelname = data.get('modelId').get('modelname')
        print(f'{modelname} and data: {data}')
        modelname = data['modelId']['modelname']
        modelversion = data['modelId']['modelversion']

        modeldict = dict(modelname=modelname, modelversion=modelversion)
        data['modelId'] = modeldict
        return data
         
        