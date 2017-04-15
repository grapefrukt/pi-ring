# making sure we're in the correct dir
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"; cd ${DIR}

# make sure we kill any previously running instances of our script
sudo pkill -f ringtest.py

# run the thing
sudo python ringtest.py
