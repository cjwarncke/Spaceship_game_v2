#!/bin/bash


echo "Starting Space Blasters servers..."

python game.py &
GAME_PID=$!

python login.py &
LOGIN_PID=$!

python score.py &
SCORE_PID=$!

python chat.py &
CHAT_PID=$!

echo "All servers started!"
echo "Press Ctrl+C to stop all servers."

trap "echo 'Stopping servers...'; kill $GAME_PID $LOGIN_PID $SCORE_PID $CHAT_PID" SIGINT SIGTERM

wait
