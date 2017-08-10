rm -f debug.log
if [ -e data/$1.commands.txt ]
then python3 chatmachine/zmachine.py data/$1.z5 < data/$1.commands.txt
else python3 chatmachine/zmachine.py data/$1.z5
fi

