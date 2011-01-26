in_file = open('EXTs.txt', 'rb')
out_file = open('EXTs_new.txt', 'wb')
optype = 'ext'

blocks = []
opcodes = []

for line in in_file.readlines():
    if not (line.find('opcode') == -1):
        blocks.append([])
        opcodes.append(line.split()[-1][:-2])
    blocks[-1].append(line)
    
for block in blocks:
    op = block[2].split("'")[1]
    out_file.write('    def execute_%s_%s(self, head, operands):\n' % (optype, op))
    for line in block[1:]:
        out_file.write(line[4:])
    out_file.write('\n')

out_file.write('\n')

for block in blocks:
    op = block[2].split("'")[1]
    out_file.write(block[0])
    out_file.write('            execute_%s_%s(head, operands)\n' % (optype, op))
    
out_file.write('\n\n')

for opcode, block in zip(opcodes, blocks):
    op = block[2].split("'")[1]
    out_file.write('%s: execute_%s_%s, ' % (opcode, optype, op))
    
out_file.write('\n')
