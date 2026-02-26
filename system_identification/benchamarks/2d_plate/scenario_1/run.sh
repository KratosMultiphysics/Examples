#!/bin/bash

cd damaged_system
# Check if MainKratos.py exists
if [ ! -f "MainKratos.py" ]; then
  echo "MainKratos.py not found!"
  exit 1
fi

# Run MainKratos.py with Python and output the log to a file with tee
python MainKratos.py | tee ../Optimization_Results/log.txt 

cd ../system_identification

# delete log.txt and abs_error.csv before running the code
rm -r Optimization_Results/
mkdir Optimization_Results

# Check if MainKratos.py exists
if [ ! -f "MainKratos.py" ]; then
  echo "MainKratos.py not found!"
  exit 1
fi

sleep 1
# Run MainKratos.py with Python and output the log to a file with tee
python MainKratos.py | tee Optimization_Results/log.txt