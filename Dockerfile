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
#Base Image
FROM python:3.8

# location in the container
ENV TA_DIR /home/app/
WORKDIR ${TA_DIR}
# Install dependencies
RUN apt-get update && apt-get install -y \
    python3-pip
RUN apt-get install -y apt-utils

# Copy sources into the container
COPY . .

RUN git clone "https://gerrit.o-ran-sc.org/r/aiml-fw/athp/sdk/feature-store"
RUN git clone "https://gerrit.o-ran-sc.org/r/aiml-fw/athp/sdk/model-storage"
RUN mkdir -p /SDK/featurestoresdk_main/
RUN mkdir -p /SDK/modelmetricssdk_main/
RUN cp -R feature-store/. /SDK/featurestoresdk_main/.
RUN cp -R model-storage/. /SDK/modelmetricssdk_main/.
RUN pip3 install /SDK/featurestoresdk_main/.
RUN pip3 install /SDK/modelmetricssdk_main/.
RUN pip3 install .
RUN pip3 install -r requirements.txt

#Expose the ports
EXPOSE 5050

