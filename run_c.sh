cd szm
if [ -e ../data/$1.commands.txt ]
then pycallgraph zmachine.py ../data/$1.z5 < ../data/$1.commands.txt
else python -m cProfile -s cumulative szm/zmachine.py data/$1.z5
fi

