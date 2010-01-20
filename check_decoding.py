import sys

def get_ref_line(addr):
    for line in asmlines:
        if not (line.find(addr) == -1):
            return line

def check_line(line):
    line = line[17:].strip()
    parts = line.split()
    addr = parts[0]
    ref_line = get_ref_line(addr)
    if (ref_line == None):
        print line
        print ref_line
    operator = parts[1].upper()
    if (ref_line.find(operator) == -1):
        print line
        print ref_line
    #cmd = parts[3].strip()
    #print addr, cmd

asmfile = open('Bronze.asm.txt')
asmlines = asmfile.readlines()
logfile = open('Bronze.log')
for line in logfile:
    if not(line.find('@') == -1):
        check_line(line)
