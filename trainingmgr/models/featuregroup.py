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
from . import db

class FeatureGroup(db.Model):
    __tablename__ = "featuregroup_info_table"
    id = db.Column(db.Integer, primary_key=True)
    featuregroup_name = db.Column(db.String(128), nullable=False)
    feature_list = db.Column(db.String(1000), nullable=False)
    datalake_source = db.Column(db.String(20000), nullable=False)
    host = db.Column(db.String(128), nullable=False)
    port = db.Column(db.String(128), nullable=False)
    bucket = db.Column(db.String(1000), nullable=False)
    token = db.Column(db.String(1000), nullable=False)
    db_org = db.Column(db.String(128), nullable=False)
    measurement = db.Column(db.String(1000), nullable=False)
    enable_dme = db.Column(db.Boolean, nullable=False)
    measured_obj_class = db.Column(db.String(20000), nullable=True)
    dme_port = db.Column(db.String(128), nullable=True)
    source_name = db.Column(db.String(20000), nullable=True)

    def __repr__(self):
        return f'<featuregroup {self.featuregroup_name}>'