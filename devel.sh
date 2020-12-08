#/bin/bash

function quit {
    echo "Killing HAMLPy watcher"
    kill -9 $HAMLPY_PID
}

trap "quit" SIGINT

echo "Executing HAMLPy watcher"
poetry run hamlpy-watcher ./templates/haml/ ./templates/html --attr-wrapper \" &
HAMLPY_PID=$!

echo "Executing application"
FLASK_APP=flaskapp.py FLASK_ENV=development poetry run flask run -h 0 -p 5000
