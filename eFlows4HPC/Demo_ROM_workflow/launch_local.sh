COMPUTING_UNITS=1
# runcompss --lang=python --python_interpreter=python3 -g -t Workflow.py $PWD $COMPUTING_UNITS
#python3 Serial.py $PWD 1
python3 Serial.py $PWD 1 | tee output.out
