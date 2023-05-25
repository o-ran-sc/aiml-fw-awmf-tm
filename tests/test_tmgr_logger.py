# ==================================================================================
#
#       Copyright (c) 2023 Samsung Electronics Co., Ltd. All Rights Reserved.
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

from trainingmgr.common.tmgr_logger import TMLogger

class Test_tmgr_logger:
    def setup_method(self):
        self.logger = TMLogger("tests/common/conf_log.yaml")

    def test_init_fail(self):
        logger = TMLogger("tests/common/conf_log.yam")
        assert vars(logger) == {}
        assert 'logger' in vars(self.logger).keys()
        assert 'log_level' in vars(self.logger).keys()

    def test_get_logger(self):
        assert self.logger.get_logger.name == 'trainingmgr.common.tmgr_logger'

    def test_get_log_level(self):
        assert self.logger.get_log_level == 'DEBUG'