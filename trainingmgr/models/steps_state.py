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

from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from . import db, TrainingJob  

class JobState(db.Model):
    __tablename__ = 'job_states'
   
    id = db.Column(Integer, primary_key=True)
    job_id = db.Column(Integer, ForeignKey('trainingjob_info_table.id'), nullable=False)  # Foreign key to TrainingJob table
    states = db.Column(JSON, nullable=False)  # JSON field to store step states
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Establish a relationship to TrainingJob
    job = relationship("TrainingJob", backref="job_states")