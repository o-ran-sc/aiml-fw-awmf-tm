# ==================================================================================
#
#       Copyright (c) 2022 Samsung Electronics Co., Ltd. All Rights Reserved.
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

from setuptools import setup, find_packages

setup(
    name="trainingmgr",
    version="0.1",
    packages=find_packages(exclude=["tests.*", "tests"]),
    author='SANDEEP KUMAR JAISAWAL',
    author_email='s.jaisawal@samsung.com',
    description="AIMLFW Training manager",
    url="https://gerrit.o-ran-sc.org/r/admin/repos/aiml-fw/awmf/tm,general",
    keywords="AIMLWF TM",
    license="Apache 2.0",
)