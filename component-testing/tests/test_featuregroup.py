import pytest
import requests
import time
from http import HTTPStatus
BASE_URL = "http://localhost:32002/ai-ml-model-training/v1/featureGroup"
BASE_URL_SHORT = "http://localhost:32002/featureGroup"
@pytest.mark.parametrize("fg_name", ["base2", "base3", "base4"])
class TestFeatureGroupCRUD:
    """End-to-end CRUD smoke tests for FeatureGroup API with cleanup"""
    def setup_method(self, method):
        """Ensure clean state before each run."""
        self.cleanup_feature_group(method.__name__)
        time.sleep(1)
    def teardown_method(self, method):
        """Clean up after each test, ensuring no leftovers."""
        self.cleanup_feature_group(method.__name__)
        time.sleep(1)
    @staticmethod
    def cleanup_feature_group(name):
        """Delete the feature group if it already exists."""
        try:
            payload = {"featuregroups_list": [{"featureGroup_name": name}]}
            resp = requests.delete(BASE_URL_SHORT, json=payload, timeout=5)
            if resp.status_code == HTTPStatus.OK:
                data = resp.json()
                if data.get("success count", 0) > 0:
                    print(f":broom: Cleaned existing FeatureGroup: {name}")
        except Exception as e:
            print(f":warning: Cleanup failed for {name}: {e}")
    def test_create_feature_group(self, fg_name):
        """Create a new Feature Group and verify response"""
        create_payload = {
            "featuregroup_name": fg_name,
            "feature_list": "pdcpBytesDl,pdcpBytesUl",
            "datalake_source": "InfluxSource",
            "enable_dme": False,
            "host": "my-release-influxdb.default",
            "port": "8086",
            "dme_port": "",
            "bucket": "UEData",
            "token": "OQURDmo86CK31aUKiXaN",
            "source_name": "",
            "measured_obj_class": "",
            "measurement": "liveCell",
            "db_org": "primary"
        }
        resp = requests.post(BASE_URL, json=create_payload)
        if resp.status_code == HTTPStatus.CONFLICT:
            data = resp.json()
            assert "already exist" in data.get("detail", "")
            print(f":warning: FeatureGroup {fg_name} already exists — skipping creation.")
            return
        assert resp.status_code in (HTTPStatus.OK, HTTPStatus.CREATED), \
            f"Unexpected status: {resp.status_code}, body: {resp.text}"
        data = resp.json()
        assert data["featuregroup_name"] == fg_name
        assert "id" in data
        print(f":white_tick: Created FeatureGroup: {fg_name} (ID: {data['id']})")
    def test_get_feature_groups(self, fg_name):
        """Verify the created feature group appears in GET list"""
        resp = requests.get(BASE_URL)
        assert resp.status_code == HTTPStatus.OK, \
            f"Unexpected status: {resp.status_code}, body: {resp.text}"
        data = resp.json()
        groups = data.get("FeatureGroups", [])
        assert any(fg["featuregroup_name"] == fg_name for fg in groups), \
            f"Feature group {fg_name} not found in list"
        print(f":white_tick: Verified GET presence of FeatureGroup: {fg_name}")
    def test_update_feature_group(self, fg_name):
        """Update existing Feature Group and verify success"""
        update_payload = {
            "featuregroup_name": fg_name,
            "feature_list": "pdcpBytesDl,pdcpBytesUl",
            "datalake_source": "InfluxSource",
            "enable_dme": False,
            "host": "my-release-influxdb.default",
            "port": "8086",
            "dme_port": "",
            "bucket": "UEData",
            "token": "OQURDmo86CK31aUKiXaN",
            "source_name": "",
            "measured_obj_class": "",
            "measurement": "liveCell2",
            "db_org": "primary"
        }
        resp = requests.put(f"{BASE_URL_SHORT}/{fg_name}", json=update_payload)
        assert resp.status_code == HTTPStatus.OK, \
            f"Unexpected status: {resp.status_code}, body: {resp.text}"
        data = resp.json()
        assert data.get("result", "").lower().startswith("feature group edited")
        print(f":white_tick: Updated FeatureGroup: {fg_name}")
    def test_duplicate_feature_group_registration(self, fg_name):
        """Attempt to create a duplicate Feature Group to validate 409 Conflict"""
        payload = {
            "featuregroup_name": fg_name,
            "feature_list": "pdcpBytesDl,pdcpBytesUl",
            "datalake_source": "InfluxSource",
            "enable_dme": False,
            "host": "my-release-influxdb.default",
            "port": "8086",
            "dme_port": "",
            "bucket": "UEData",
            "token": "OQURDmo86CK31aUKiXaN",
            "source_name": "",
            "measured_obj_class": "",
            "measurement": "liveCell",
            "db_org": "primary"
        }
        # First create
        requests.post(BASE_URL, json=payload)
        # Duplicate create
        resp = requests.post(BASE_URL, json=payload)
        assert resp.status_code == HTTPStatus.CONFLICT, \
            f"Expected 409 Conflict, got {resp.status_code} ({resp.text})"
        data = resp.json()
        assert "already exist" in data.get("detail", "")
        print(f":white_tick: Verified duplicate FeatureGroup {fg_name} returns 409 Conflict")
    def test_delete_feature_group(self, fg_name):
        """Delete the feature group and verify deletion"""
        payload = {"featuregroups_list": [{"featureGroup_name": fg_name}]}
        resp = requests.delete(BASE_URL_SHORT, json=payload)
        assert resp.status_code == HTTPStatus.OK, \
            f"Unexpected status: {resp.status_code}, body: {resp.text}"
        data = resp.json()
        assert data.get("success count", 0) >= 1
        assert data.get("failure count", 0) == 0
        print(f":white_tick: Deleted FeatureGroup: {fg_name}")










