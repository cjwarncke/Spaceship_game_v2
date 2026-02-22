#!/bin/bash

trap "echo 'Stopping servers...'; kill 0" SIGINT SIGTERM

echo "Starting Space Blasters servers..."

python3 game.py &
python3 login.py &
python3 score.py &
python3 chat.py &

echo "All servers started!"
echo "Press Ctrl+C to stop all servers."

wait
