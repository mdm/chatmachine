rm debug.log
if [ -e data/$1.commands.txt ]
then python chatmachine/vm/zmachine.py data/$1.z5 < data/$1.commands.txt
else python chatmachine/vm/zmachine.py data/$1.z5
fi

