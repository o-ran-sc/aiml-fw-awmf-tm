# Base Image
FROM python:3.10-slim AS builder


# Location in the container
WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-pip apt-utils git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy sources into the container
COPY . .

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Clone SDK repositories and install SDKs
RUN git clone --depth 1 "https://gerrit.o-ran-sc.org/r/aiml-fw/athp/sdk/feature-store" /SDK/featurestoresdk_main && \
    git clone --depth 1 "https://gerrit.o-ran-sc.org/r/aiml-fw/athp/sdk/model-storage" /SDK/modelmetricssdk_main && \
    pip3 install --no-cache-dir /SDK/featurestoresdk_main/. && \
    pip3 install --no-cache-dir /SDK/modelmetricssdk_main/. && \
    rm -rf /SDK

# Final stage
FROM python:3.10-slim

# Location in the container
ENV TA_DIR=/app
WORKDIR ${TA_DIR}

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy the application code
COPY --from=builder ${TA_DIR} ${TA_DIR}

RUN pip3 install --no-cache-dir .

# Expose the ports
EXPOSE 5050

# COPY model-storage /SDK/featurestoresdk_main
WORKDIR ${TA_DIR}/trainingmgr

# Start the application
CMD ["python3", "trainingmgr_main.py"]
