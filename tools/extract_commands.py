import sys

basename = sys.argv[1]

transcript = open(basename + '.log')
lines = transcript.readlines()
transcript.close()

commands = open(basename + '.commands', 'wb')
for line in lines:
    if len(line) > 0 and line[0] == '>':
        commands.write(line[1:])
commands.close()

