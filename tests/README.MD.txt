#Current working directory
tm

Directory struture
tm
|__tests
|__trainingmgr
|setup.py


#Prerequisite to run the test cases
Install training manager as python package
pip3 install .

Example to run test cases.

# Generate test report
sudo python3 -m pytest -rA . --capture=tee-sys --cov-report term-missing --cov-report xml:coverage.xml   --cov-report html:htmlcov --junitxml test-reports/junit.xml --cov=./
