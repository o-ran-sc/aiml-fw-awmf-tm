<!--
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
-->

## Directory struture
```
tm
├──tests
├──trainingmgr
└──setup.py
```

## Prerequisite to run the test cases
> Change the current working directory to home directory
Install training manager itself as python package
``` bash
pip3 install .
```

## Install modelmetricsdk and featurestoresdk as python packages
``` bash
git clone "https://gerrit.o-ran-sc.org/r/aiml-fw/athp/sdk/feature-store" /tmp/fssdk/
git clone "https://gerrit.o-ran-sc.org/r/aiml-fw/athp/sdk/model-storage" /tmp/modelsdk/

pip3 install /tmp/fssdk/.
pip3 install /tmp/modelsdk/.
```

## Install all python dependecy packages
``` bash
pip3 install -r requirements_test.txt
```

## Example to run test cases along with generating test reports.
``` bash
python3 -m pytest -rA . --capture=tee-sys --cov-report term-missing --cov-report xml:coverage.xml   --cov-report html:htmlcov --junitxml test-reports/junit.xml --cov=./trainingmgr/
```
