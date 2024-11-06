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

from sqlalchemy import Integer, String, Column, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import db

class TrainingJobStatus(db.Model):
    __tablename__ = 'training_job_status_table'
   
    id = Column(Integer, primary_key=True)
    states = Column(String, nullable=False)
    creation_time = Column(DateTime(timezone=False), server_default=func.now(),nullable=False)
    updation_time = Column(DateTime(timezone=False),onupdate=func.now() ,nullable=True)

    # Establish a relationship to TrainingJob
    trainingjobs = relationship("TrainingJob", back_populates="steps_state")