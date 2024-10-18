#!/bin/bash

echo "Checking for Database"
while [[ $(kubectl get pods tm-db-postgresql-0 -n traininghost -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True" ]]; do echo "waiting for training manager db pod" && sleep 1; done
echo "Installed tm-db"

# Updates the database
flask db upgrade

# Starts the flask application
exec python3 ./trainingmgr/trainingmgr_main.py