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
# ==============================================================================
from . import db
from datetime import datetime
from sqlalchemy.sql import func

class TrainingJob(db.Model):
    __tablename__ = "trainingjob_info_table"
    id = db.Column(db.Integer, primary_key=True)
    trainingjob_name= db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    feature_group_name = db.Column(db.String(128), nullable=False)
    pipeline_name= db.Column(db.String(128), nullable=False)
    experiment_name = db.Column(db.String(128), nullable=False)
    arguments = db.Column(db.String(2000), nullable=False)
    query_filter = db.Column(db.String(2000), nullable=False)
    creation_time = db.Column(db.DateTime(timezone=False), server_default=func.now(),nullable=False)
    run_id = db.Column(db.String(1000), nullable=False)
    steps_state = db.Column(db.String(1000), nullable=False)
    updation_time = db.Column(db.DateTime(timezone=False),onupdate=func.now() ,nullable=False)
    version = db.Column(db.Integer, nullable=False)
    enable_versioning = db.Column(db.Boolean, nullable=False)
    pipeline_version = db.Column(db.String(128), nullable=False)
    datalake_source = db.Column(db.String(2000), nullable=False)
    model_url = db.Column(db.String(1000), nullable=False)
    notification_url = db.Column(db.String(1000), nullable=False)
    deletion_in_progress = db.Column(db.Boolean, nullable=False)
    is_mme = db.Column(db.Boolean, nullable=True)
    model_name = db.Column(db.String(128), nullable=True)
    model_info = db.Column(db.String(1000), nullable=True)

    def __repr__(self):
        return f'<Trainingjob {self.trainingjob_name}>'