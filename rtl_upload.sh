#! /bin/bash

realpath "$0"
echo $base_dir
#cd /home/example/icad_rtl_uploader
python3 ${1}rtl_uploader.py ${1} ${2} ${3} ${4}
status=$?

# Exit with 0 status, even if there is an error.
if [ $status -ne 0 ]; then
    echo "Error with python script, exit status: $status"
    exit 0
else
    exit 0
fi