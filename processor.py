import sys
import struct
import heap
import stack

class Processor:
    def __init__(self, heap):
	self.heap = heap
	self.header = self.heap.get_header()
	self.pc = self.header.get_initial_pc()
	self.stack = stack.Stack()
	self.num_locals = 0
	self.num_args = 0
	self.is_running = False

    def get_operands(self, types, signed = False):
	tmp = []	
	for type in types:
	    if (type == 0):
		tmp.append(self.heap.read_word(self.pc, signed))
		self.pc += 2
	    elif (type == 1):
		#TODO: check if signed bytes are needed
		tmp.append(self.heap.read_byte(self.pc))
		self.pc += 1
	    elif (type == 2):
		variable_number = self.heap.read_byte(self.pc)
		self.pc += 1
		tmp.append(self.get_variable(variable_number))
	return tmp
    
    def unpack_address(self, address):
	if (self.header.get_z_version() < 4): return address * 2
	elif (self.header.get_z_version() < 6): return address * 4
	elif (self.header.get_z_version() == 8): return address * 8
	else: return 0 #TODO: unsupported version error

    def get_variable(self, variable_number):
	if (variable_number == 0):
	    return self.stack.pop()
	elif (variable_number < 16):
	    return self.stack.get_value(variable_number - 1)
	elif (variable_number < 256):
	    return self.heap.read_word(self.header.get_globals_table_location() + 2 * (variable_number - 16))
	else:
	    print 'Illegal variable:', variable_number
	    return 0

    def set_variable(self, variable_number, value):
	if (variable_number == 0):
	    self.stack.push(value)
	elif (variable_number < 16):
	    self.stack.set_value(variable_number - 1, value)
	elif (variable_number < 256):
	    self.heap.write_word(self.header.get_globals_table_location() + 2 * (variable_number - 16))
	else:
	    print 'Illegal variable:', variable_number
	    return 0

    def ops_call(self, operands, store_result):
	address = self.unpack_address(operands[0])
	print address
	if (address == 0):
	    print 'call to address 0 not implemented.'
	else:
	    if (store_result):
		result_variable = self.heap.read_byte(self.pc)
		self.pc += 1
	    else:
		result_variable = None
	    self.stack.push_frame(self.pc, result_variable, self.num_locals, self.num_args)
	    #TODO: push num_locals to avoid referencing non-existing local?
	    self.pc = address
	    self.num_args = len(operands) - 1
	    self.num_locals = self.heap.read_byte(self.pc)
	    self.pc += 1
	    for i in range(self.num_locals):
		if (self.header.get_z_version < 5):
		    self.stack.push(self.heap.read_word(self.pc))
		    self.pc += 2
		else:
		    self.stack.push(0)
	    operands = operands[1:self.num_locals + 1]
	    for i in range(len(operands)):
		self.set_variable(i + 1, operands[i])

    def ops_branch(self, condition):
	offset = self.heap.read_byte(self.pc)
	self.pc += 1
	if (offset & 128):
	    condition = not condition
	if not (offset & 64):
	    offset = ((offset & 0x3f) << 8) + self.heap.read_byte(self.pc)
	    self.pc += 1
	else:
	    offset &= 0x3f
	if (not condition):
	    if (offset < 2):
		ops_return(offset)
	    else:
		self.pc += offset -2

    def ops_return(self, return_value):
	self.pc, result_variable, self.num_locals, self.num_args = self.stack.pop_frame()
	if not (result_variable == None):
	    self.set_variable(result_variable, return_value)

    def ops_store(self, value):
	result_variable = self.heap.read_byte(self.pc)
	self.pc += 1
	self.set_variable(result_variable, value)

    def decode_variable(self, opcode):
	print 'variable form'
	#next byte gives 4 operand types, from left to right
	#11 omitts all subsequent operands
	types = []
	mask = 192
	mask_pos = 3
	packed_types = self.heap.read_byte(self.pc)
	self.pc += 1
	while (mask > 0):
	    tmp = (packed_types & mask) >> (2 * mask_pos)
	    if (tmp == 3): break
	    types.append(tmp)
	    mask >>= 2
	    mask_pos -= 1
	print "operand types 0x%02x" % packed_types, types
	#bit 5 gives operand count
	#0 == 2 operands, 1 == var. # of operands
	if (not (opcode & 32) and (len(types) != 2)): print 'Illegal number of operands.'
	opcode &= 0x1F # lower 5 bits give operator type
	print "actual opcode 0x%02x" % opcode

	if (opcode == 0x0):
	    print 'call_vs', types
	    self.ops_call(self.get_operands(types), True)
	    print self.num_locals, self.num_args
	elif (opcode == 0x15):
	    print 'sub', types
	    operands = self.get_operands(types, True)
	    self.ops_store(operands[0] - operands[1])
	elif (opcode == 0x19):
	    print 'call_vn', types
	    self.ops_call(self.get_operands(types), False)
	    print self.num_locals, self.num_args
	elif (opcode == 0x1F):
	    print 'check_arg_count', types
	    operands = self.get_operands(types)
	    print operands, self.num_args
	    self.ops_branch(operands[0] <= self.num_args)
	else:
	    self.is_running = False
	    print 'Unkown operator. Halting.'
	#for ops call_vs2 and call_vn2 a second byte of operand types is given

    def decode_short(self, opcode):
	print 'short form'
	#bits 4 and 5 give operand type:
	#00 == large const (word), 01 == small const (byte), 10 == variable (byte), 11 == omitted
	#0 or 1 operands	
	#opcode in bits 0-3
	self.is_running = False
	print 'Unkown operator. Halting'

    def decode_extended(self):
	print 'extended form'
	#always var. # of operands
	#opcode in next byte
	#next next byte gives 4 operand types, from left to right
	#11 omitts all subsequent operands
	self.is_running = False
	print 'Unkown operator. Halting'

    def decode_long(self, opcode):
	print 'long form'
	#bits 6 and 5 give operand types
	types = [1, 1]
	if (opcode & 0x20):
	    types[0] = 2
	if (opcode & 0x10):
	    types[1] = 2
	opcode &= 0x1F # lower 5 bits give operator type
	print "actual opcode 0x%02x" % opcode
	if (opcode == 0x1):
	    print 'je', types
	    operands = self.get_operands(types, True)
	    self.ops_branch(operands[0] == operands[1])
	elif (opcode == 0x2):
	    print 'jl', types
	    operands = self.get_operands(types, True)
	    self.ops_branch(operands[0] < operands[1])
	elif (opcode == 0x3):
	    print 'jg', types
	    operands = self.get_operands(types, True)
	    print operands
	    self.ops_branch(operands[0] > operands[1])
	elif (opcode == 0x12):
	    print 'get_prop_addr', types
	    operands = self.get_operands(types)
	    print operands
	else:
	    self.is_running = False
	    print 'Unkown operator. Halting'

    def run(self):
	# fetch-and-execute loop
	self.is_running = True

	while (self.is_running):
		opcode = self.heap.read_byte(self.pc)
		self.pc += 1
		print '\nOpcode:', opcode
		if ((opcode & 192) == 192):
		    self.decode_variable(opcode)
		elif ((opcode & 192) == 128):
		    self.decode_short(opcode)
		elif (opcode == 0xBE):
		    self.decode_extended()
		else:
		    self.decode_long(opcode)
		#decode
		#exec


heap = heap.Heap(sys.argv[1])
print heap
cpu = Processor(heap)
cpu.run()

print 'Goodbye'
