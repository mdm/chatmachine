import re

logfile = open('debug.log')
loglines = logfile.readlines()
logfile.close()

for line in loglines:
    match = re.match('DEBUG:root:(.*):', line)
    print(match.group(1))
