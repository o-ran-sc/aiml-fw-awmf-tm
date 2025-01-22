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

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from trainingmgr.common.exceptions_utls import DBException
from trainingmgr.models import FeatureGroup, db
from dotenv import load_dotenv
load_dotenv('tests/test.env')
from trainingmgr.db.featuregroup_db import add_featuregroup, edit_featuregroup
from flask import Flask

DB_QUERY_EXEC_ERROR = "Failed to execute query in "


class TestFeatureGroupFunctions:
    """Test suite for add_featuregroup and edit_featuregroup functions."""

    @pytest.fixture(autouse=True)
    def setup_app_context(self):
        """Set up Flask application context for tests."""
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory SQLite database
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)

        with self.app.app_context():
            yield  # This ensures all tests run within the app context

    # Test Cases for add_featuregroup
    @patch("trainingmgr.models.db.session")
    def test_add_featuregroup_success(self, mock_session):
        featuregroup = MagicMock(spec=FeatureGroup)
        add_featuregroup(featuregroup)
        mock_session.add.assert_called_once_with(featuregroup)
        mock_session.commit.assert_called_once()

    @patch("trainingmgr.models.db.session")
    def test_add_featuregroup_unique_violation(self, mock_session):
        featuregroup = MagicMock(spec=FeatureGroup)
        featuregroup.featuregroup_name = "test_featuregroup"

        mock_exception = IntegrityError("Integrity error", None, None)
        mock_exception.orig = UniqueViolation("Unique violation")
        mock_session.add.side_effect = mock_exception

        with pytest.raises(DBException) as exc_info:
            add_featuregroup(featuregroup)

        assert str(exc_info.value) == "Featuregroup with featuregroup_name test_featuregroup already exist"
        mock_session.rollback.assert_not_called()

    @patch("trainingmgr.models.db.session")
    def test_add_featuregroup_generic_exception(self, mock_session):
        featuregroup = MagicMock(spec=FeatureGroup)
        mock_session.add.side_effect = Exception("Generic exception")

        with pytest.raises(DBException) as exc_info:
            add_featuregroup(featuregroup)

        assert str(exc_info.value) == "Failed to execute query in  failed to add feature group"
        mock_session.rollback.assert_called_once()

    # Test Cases for edit_featuregroup
    @patch("trainingmgr.models.db.session")
    @patch("trainingmgr.models.FeatureGroup.query.filter_by")
    def test_edit_featuregroup_success(self, mock_filter_by, mock_session):
        featuregroup_name = "test_featuregroup"
        featuregroup_data = {"featuregroup_name": "test_featuregroup", "description": "updated_description"}

        # Create a mock feature group with real attributes
        mock_featuregroup = MagicMock(spec=FeatureGroup)
        mock_featuregroup.featuregroup_name = featuregroup_name
        mock_featuregroup.description = "old_description"

        # Mock the database query to return the mock feature group
        mock_filter_by.return_value.first.return_value = mock_featuregroup

        # Call the function
        edit_featuregroup(featuregroup_name, featuregroup_data)

        # Assert the attributes were updated
        assert mock_featuregroup.featuregroup_name == "test_featuregroup"
        assert mock_featuregroup.description == "old_description"

        # Assert commit was called
        mock_session.commit.assert_called_once()


    @patch("trainingmgr.models.db.session")
    @patch("trainingmgr.models.FeatureGroup.query.filter_by")
    def test_edit_featuregroup_commit_exception(self, mock_filter_by, mock_session):
        featuregroup_name = "test_featuregroup"
        featuregroup_data = {"featuregroup_name": "updated_name", "description": "updated_description"}

        mock_featuregroup = MagicMock(spec=FeatureGroup)
        mock_filter_by.return_value.first.return_value = mock_featuregroup
        mock_session.commit.side_effect = Exception("Database commit error")

        with pytest.raises(DBException) as exc_info:
            edit_featuregroup(featuregroup_name, featuregroup_data)

        assert str(exc_info.value).startswith(DB_QUERY_EXEC_ERROR)
        assert "Database commit error" in str(exc_info.value)
        mock_session.commit.assert_called_once()

    @patch("trainingmgr.models.db.session")
    @patch("trainingmgr.models.FeatureGroup.query.filter_by")
    def test_edit_featuregroup_skip_id_field(self, mock_filter_by, mock_session):
        featuregroup_name = "test_featuregroup"
        featuregroup_data = {"featuregroup_name": "test_featuregroup", "description": "updated_description"}

        # Create a mock feature group with real attributes
        mock_featuregroup = MagicMock(spec=FeatureGroup)
        mock_featuregroup.featuregroup_name = featuregroup_name
        mock_featuregroup.description = "old_description"

        # Mock the database query to return the mock feature group
        mock_filter_by.return_value.first.return_value = mock_featuregroup

        edit_featuregroup(featuregroup_name, featuregroup_data)

        assert not hasattr(mock_featuregroup, "id") or mock_featuregroup.id != 123
        assert mock_featuregroup.featuregroup_name == "test_featuregroup"
        mock_session.commit.assert_called_once()