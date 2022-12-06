import pytest

from trainingmgr.common.tmgr_logger import TMLogger

def pytest_configure():
    pytest.logger = TMLogger("tests/common/conf_log.yaml").logger

