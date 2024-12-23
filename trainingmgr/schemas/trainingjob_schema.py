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

import re
from trainingmgr.schemas import ma
from trainingmgr.models import TrainingJob
from trainingmgr.models.trainingjob import ModelID
import json
from marshmallow import pre_load, post_dump, fields, validates, ValidationError

PATTERN = re.compile(r"\w+")

class ModelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ModelID
        load_instance = True
        
    @post_dump
    def replace_null_with_empty_string(self, data, **kwargs):
        for key, value in data.items():
            if value is None:
                data[key]=""
        return data

class TrainingJobSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TrainingJob
        load_instance = True
        exclude = ("creation_time", "deletion_in_progress", "updation_time","run_id")
    
    modelId = ma.Nested(ModelSchema)

    # consumer_rapp_id = fields.String(allow_none = True, dump_default="")

    @pre_load
    def processModelId(self, data, **kwargs):
        modelname = data['modelId']['modelname']
        modelversion = data['modelId']['modelversion']

        modeldict = dict(modelname=modelname, modelversion=modelversion)
        data['modelId'] = modeldict
        return data
    
    @post_dump(pass_many=True)
    def trainingConfigtoDict(self, data, many, **kwargs):
        if many:
            for index in range(len(data)):
                data[index]["training_config"] = json.loads(data[index]["training_config"])
        else:
            data["training_config"] = json.loads(data["training_config"])   
        
        return data
    
    @post_dump
    def replace_null_with_empty_string(self, data, **kwargs):
        for key, value in data.items():
            if value is None:
                data[key]=""
        return data
        