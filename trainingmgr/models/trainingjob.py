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
from sqlalchemy import Integer, ForeignKey, String, DateTime, Column, Boolean
from sqlalchemy.orm import relationship

class TrainingJob(db.Model):
    __tablename__ = "trainingjob_info_table"
    id = Column(Integer, primary_key=True)
    trainingjob_name= Column(String(128), nullable=False)
    run_id = Column(String(1000), nullable=True)
    steps_state_id = Column(Integer, ForeignKey('training_job_status_table.id'), nullable=True)
    creation_time = Column(DateTime(timezone=False), server_default=func.now(),nullable=False)
    updation_time = Column(DateTime(timezone=False),onupdate=func.now() ,nullable=True)
    version = Column(Integer, nullable=True)
    deletion_in_progress = Column(Boolean, nullable=True)
    training_config = Column(String(5000), nullable=False)
    model_url = Column(String(1000), nullable=True)
    notification_url = Column(String(1000), nullable=True)
    model_name = Column(String(128), nullable=True)
    model_info = Column(String(1000), nullable=True)

    #defineing relationships
    steps_state = relationship("TrainingJobStatus", back_populates="trainingjobs")

    def __repr__(self):
        return f'<Trainingjob {self.trainingjob_name}>'