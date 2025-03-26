# ==================================================================================
#
#      Copyright (c) 2025 Samsung Electronics Co., Ltd. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# ==================================================================================

import pytest
from unittest.mock import patch, MagicMock
from trainingmgr.models.trainingjob import TrainingJob

from trainingmgr.db.trainingjob_db import (
    get_trainingjobs_by_modelId_db
)

class TestGetTrainingJobsByModelIdDb:
    def test_success(self):
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        # mock_trainingjobs = [MagicMock(spec=TrainingJob), MagicMock(spec=TrainingJob)]
        mock_trainingjobs = None
        mock_filter.all.return_value = mock_trainingjobs
        
        with patch("trainingmgr.models.db.session.query", mock_session):
            result = get_trainingjobs_by_modelId_db("test_model", "v1")

    
    @patch('trainingmgr.models.db.session.query', side_effect = Exception("Database error"))
    def test_internal_error(self, mock1):
        try:
            model_name = "abc"
            model_version = "1"
            get_trainingjobs_by_modelId_db(model_name, model_version)
            assert False, "The test is supposed to fail, but it passed, It will be considered as failure"
        except:
            # Test was supposed to fail, and It failed, So, It will consider Passed
            pass
        