nohup python /app/matrix.py &
nohup python /app/estimation.py &
nohup python /app/translation.py &
tail -f /app/eval.log
