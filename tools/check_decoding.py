import sys

asmfile = open('Bronze.asm.txt')
asmlines = asmfile.readlines()
asmfile.close()
trailfile = open('Bronze.trail.txt')
trail = trailfile.readlines()
trailfile.close()
last_op = '*'
last_line = 0

def get_ref_line(addr):
    line_no = 0
    for line in asmlines:
        if not (line.find(addr) == -1):
            return line_no
        else:
            line_no += 1
    return None

def check_line(line):
    global last_op
    global last_line
    print("\n", line, end=' ')
    line = line[17:].strip()
    parts = line.split()
    addr = parts[0]
    ref_line = get_ref_line(addr)
    if (ref_line == None):
        print('Reference not found')
        print(ref_line, asmlines[ref_line])
        return False
    else:
        operator = parts[1].upper()
        if (asmlines[ref_line].find(operator) == -1):
            print('Operator mismatch')
            print(ref_line, asmlines[ref_line])
            return False
        else:
            if (last_op[0] == 'J') or (last_op in ['CHECK_ARG_COUNT', 'GET_CHILD', 'TEST_ATTR']):
                trail_addr = trail[0].split()[-1]
                if (ref_line == last_line + 1):
                    if (trail_addr == addr[:-1]):
                        trail.pop(0)
                        print('Jump from:', last_line, asmlines[last_line], end=' ')
                        print('Jump to:', ref_line, asmlines[ref_line], end=' ')
                else:
                    trail_addr = trail[0].split()[-1]
                    if not (trail_addr == addr[:-1]):
                        print('Trace does not follow trail:', trail_addr)
                        return False
                    else:
                        trail.pop(0)
                        print('Jump from:', last_line, asmlines[last_line], end=' ')
                        print('Jump to:', ref_line, asmlines[ref_line], end=' ')
            elif (last_op[:4] == 'CALL'):
                trail_addr = trail[0].split()[-1]
                if not (trail_addr == addr[:-1]):
                    print('Trace does not follow trail:', trail_addr)
                    return False
                else:
                    trail.pop(0)
                    print('Call from:', last_line, asmlines[last_line], end=' ')
                    print('Call to:', ref_line, asmlines[ref_line], end=' ')
            elif (last_op in ['RET', 'PRINT_RET', 'RET_POPPED', 'RFALSE', 'RTRUE']):
                trail_addr = trail[0].split()[-1]
                if not (trail_addr == addr[:-1]):
                    print('Trace does not follow trail:', trail_addr)
                    return False
                else:
                    trail.pop(0)
                    print('Return from:', last_line, asmlines[last_line], end=' ')
                    print('Return to:', ref_line, asmlines[ref_line], end=' ')
        last_op = operator
        last_line = ref_line
    #cmd = parts[3].strip()
    #print addr, cmd
    print('OK')
    return True

logfile = open('Bronze.log')
for line in logfile:
    if not(line.find('@') == -1):
        if not check_line(line):
            break
logfile.close()
