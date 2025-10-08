# ==================================================================================
#
#       Copyright (c) 2025 Gyuri Park <inglifestora@naver.com> All Rights Reserved.
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
from pydantic import BaseModel
from typing import Optional

class FeatureGroupIntent(BaseModel):
    featuregroup_name: str
    feature_list: str
    datalake_source: str
    enable_dme: bool
    host: str
    port: str
    bucket: str
    token: str
    measurement: str
    db_org: str
    dme_port: Optional[str] = None
    source_name: Optional[str] = None
    measured_obj_class: Optional[str] = None


class ModelRegistrationIntent(BaseModel):
    model_name: str
    model_version: str
    description: str
    author: str
    owner: Optional[str] = ""
    input_data_type: str
    output_data_type: str
    model_location: Optional[str] = None