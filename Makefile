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
# Makefile for building the Docker image and running the microservice

# Variables
IMAGE_NAME := aiml-fw-tm:dev
CONTAINER_NAME := aiml-fw-tm-container
PORT := 5050

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME) .

build-optimize:
	docker build -f Dockerfile.optimize -t $(IMAGE_NAME_OPT) .

# Run the Docker container
run:
	docker run --rm --name $(CONTAINER_NAME) -p $(PORT):$(PORT) $(IMAGE_NAME)

publish:
	docker push $(IMAGE_NAME)

# Stop and remove the running container
stop:
	docker stop $(CONTAINER_NAME) && docker rm $(CONTAINER_NAME)

# Clean up the Docker image
clean:
	docker rmi $(IMAGE_NAME)

# Run docker for debugging
debug:
	docker run -it --rm --entrypoint /bin/bash --name $(CONTAINER_NAME) -p $(PORT):$(PORT) $(IMAGE_NAME) 

# Default target
default: build run

# Help message
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build         Build the Docker image."
	@echo "  run           Run the Docker container."
	@echo "  stop          Stop and remove the running container."
	@echo "  clean         Clean up the Docker image."
	@echo "  debug         Run docker for debugging."
	@echo "  default       Build and run the Docker container."
	@echo "  help          Show this help message."
