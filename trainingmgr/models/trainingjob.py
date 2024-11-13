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
from sqlalchemy.orm import relationship
from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint
import json

class ModelID(db.Model):
    __tablename__ = 'model'
    id = db.Column(db.Integer, primary_key=True)
    modelname = db.Column(db.String(128), nullable=False)
    modelversion = db.Column(db.String(128), nullable=False)
    artifactversion = db.Column(db.String(128), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("modelname", "modelversion", name="unique model"),
    )

    trainingJob = relationship("TrainingJob", backref='model')


class TrainingJob(db.Model):
    __tablename__ = "trainingjob_info_table"
    # Meta
    id = db.Column(db.Integer, primary_key=True)
    trainingjob_name= db.Column(db.String(128), nullable=False)
    run_id = db.Column(db.String(1000), nullable=True)
    steps_state = db.Column(db.String(1000), nullable=True)
    creation_time = db.Column(db.DateTime(timezone=False), server_default=func.now(),nullable=False)
    updation_time = db.Column(db.DateTime(timezone=False),onupdate=func.now() ,nullable=True)
    version = db.Column(db.Integer, nullable=True)
    deletion_in_progress = db.Column(db.Boolean, nullable=True)
    #  TrainingConfig
    is_mme = db.Column(db.Boolean, nullable=True)
    description = db.Column(db.String(2000), nullable=False)
    ## DataPipeline-Configurations
    datalake_source = db.Column(db.String(2000), nullable=False)
    feature_group_name = db.Column(db.String(128), nullable=False)
    query_filter = db.Column(db.String(2000), nullable=False)
    arguments = db.Column(db.String(2000), nullable=False)
    ## TrainingPipeline-Configurations
    pipeline_name= db.Column(db.String(128), nullable=False)
    pipeline_version = db.Column(db.String(128), nullable=False)
    experiment_name = db.Column(db.String(128), nullable=False)
    enable_versioning = db.Column(db.Boolean, nullable=False)
    # After-training
    model_url = db.Column(db.String(1000), nullable=True)
    notification_url = db.Column(db.String(1000), nullable=True)
    model_id = db.Column(db.Integer, nullable=False)
    model_info = db.Column(db.String(1000), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["model_id"],
            ["model.id"]
        ),
    )
    

    # modelID = relationship("ModelID", back_populates="trainingjob_info_table")

    # # Serialize and Deserialize training_config to/from JSON
    # @property
    # def training_config_data(self):
    #     return json.loads(self.training_config)

    # @training_config_data.setter
    # def training_config_data(self, value):
    #     self.training_config = json.dumps(value)
    def __repr__(self):
        return f'<Trainingjob {self.trainingjob_name}>'