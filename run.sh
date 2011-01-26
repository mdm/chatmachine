if [ -e data/$1.commands.txt ]
then python szm/zmachine.py data/$1.z5 < data/$1.commands.txt
else python szm/zmachine.py data/$1.z5
fi

