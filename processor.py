import sys
import struct
import heap
import stack

class Processor:
    def __init__(self, heap):
	self.heap = heap
	self.header = self.heap.get_header()
	self.pc = self.header.get_initial_pc()
	self.object_table = self.heap.get_object_table()
	self.stack = stack.Stack()
	self.num_locals = 0
	self.num_args = 0
	self.is_running = False
	self.exec_count = 0

    def print_state(self):
	print self.pc
	self.stack.print_me()
	for i in range(256):
	    if (i % 16 == 0): print
	    if (i == 0):
		print 'SSSS',
	    elif (self.num_locals < i < 16):
		print 'NONE',
	    else:
		value = self.get_variable(i)
		print "%04x" % value,

    def get_operands(self, types):
	tmp = []	
	for type in types:
	    if (type == 0): # large constant
		tmp.append(self.heap.read_word(self.pc))
		self.pc += 2
	    elif (type == 1): # small constant
		tmp.append(self.heap.read_byte(self.pc))
		self.pc += 1
	    elif (type == 2): # variable by value
		variable_number = self.heap.read_byte(self.pc)
		self.pc += 1
		print 'getting variable', variable_number
		tmp.append(self.get_variable(variable_number))
	return tmp

    def signed_word(self, word):
	return word - (1 << 16)

    def unsigned_word():
	return word + (1 << 16)
    
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
	    self.heap.write_word(self.header.get_globals_table_location() + 2 * (variable_number - 16), value)
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
	    print 'branch on True'
	else:
	    print 'branch on False'

	if not (offset & 64):
	    offset = ((offset & 0x3f) << 8) + self.heap.read_byte(self.pc)
	    self.pc += 1
	    print 'branch address is 2 bytes:', offset
	else:
	    offset &= 0x3f
	    print 'branch address is 1 bytes:', offset

	if (not condition):
	    if (offset < 2):
		print 'return from branch', offset
		self.ops_return(offset)
	    else:
		self.pc += offset - 2

    def ops_return(self, return_value):
	self.pc, result_variable, self.num_locals, self.num_args = self.stack.pop_frame()
	if not (result_variable == None):
	    self.set_variable(result_variable, return_value)
	    print 'storing in variable', result_variable

    def ops_store(self, value):
	result_variable = self.heap.read_byte(self.pc)
	print 'storing in variable', result_variable
	self.pc += 1
	self.set_variable(result_variable, value)

    def execute_2OP(self, opcode, operands):
	print 'executing 2OP'
	if (opcode == 0x1):
	    print 'je', operands
	    condition = False
	    for operand in operands[1:]:
		if (operand == operands[0]):
		    condition = True
	    self.ops_branch(condition)
	elif (opcode == 0x2):
	    print 'jl', operands
	    self.ops_branch(self.signed_word(operands[0]) < self.signed_word(operands[1]))
	elif (opcode == 0x3):
	    print 'jg', operands
	    self.ops_branch(self.signed_word(operands[0]) > self.signed_word(operands[1]))
	elif (opcode == 0x4):
	    print 'dec_chk', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x5):
	    print 'inc_chk', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x6):
	    print 'jin', operands
	    self.ops_branch(self.object_table.get_object_parent(operands[0]) == operands[1])
	elif (opcode == 0x7):
	    print 'test', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x8):
	    print 'or', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x9):
	    print 'and', operands
	    if (not len(operands) == 2):
		self.is_running = False
		print 'Unkown operator. Halting.'
	    self.ops_store(operands[0] & operands[1])
	elif (opcode == 0xA):
	    print 'test_attr', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xB):
	    print 'set_attr', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xC):
	    print 'clear_attr', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xD):
	    print 'store', operands
	    self.set_variable(operands[0], operands[1])
	elif (opcode == 0xE):
	    print 'insert_obj', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xF):
	    print 'loadw', operands
	    self.ops_store(self.heap.read_word(operands[0] + 2 * operands[1]))
	elif (opcode == 0x10):
	    print 'loadb', operands
	    self.ops_store(self.heap.read_word(operands[0] + operands[1]))
	elif (opcode == 0x11):
	    print 'get_prop', operands
	    self.ops_store(self.object_table.get_property(operands[0], operands[1]))
	elif (opcode == 0x12):
	    print 'get_prop_addr', operands
	    self.ops_store(self.object_table.get_property_addr(operands[0], operands[1]))
	elif (opcode == 0x13):
	    print 'get_next_prop', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x14):
	    print 'add', operands
	    self.ops_store((operands[0] + operands[1]) % (1 << 16))
	elif (opcode == 0x15):
	    print 'sub', operands
	    self.ops_store((operands[0] - operands[1]) % (1 << 16))
	elif (opcode == 0x16):
	    print 'mul', operands
	    self.ops_store(int((operands[0] * operands[1]) % (1 << 16)))
	elif (opcode == 0x17):
	    print 'div', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x18):
	    print 'mod', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x19):
	    print 'call_2s', operands
	    self.ops_call(operands, True)
	elif (opcode == 0x1A):
	    print 'call_2n', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x1B):
	    print 'set_colour', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x1C):
	    print 'throw', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	else:
	    self.is_running = False
	    print 'Unkown operator. Halting.'

    def execute_1OP(self, opcode, operands):
	print 'executing 1OP'
	if (opcode == 0x0):
	    print 'jz', operands
	    self.ops_branch(operands[0] == 0)
	elif (opcode == 0x1):
	    print 'get_sibling', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x2):
	    print 'get_child', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x3):
	    print 'get_parent', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x4):
	    print 'get_prop_len', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x5):
	    print 'inc', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x6):
	    print 'dec', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x7):
	    print 'print_addr', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x8):
	    print 'call_1s', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x9):
	    print 'remove_obj', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xA):
	    print 'print_obj', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xB):
	    print 'ret', operands
	    self.ops_return(operands[0])
	elif (opcode == 0xC):
	    print 'jump', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xD):
	    print 'print_paddr', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xE):
	    print 'load', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xF):
	    version = self.header.get_z_version()
	    if (version < 5):
		print 'not', operands
	    else:
		print 'call_1n', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	else:
	    self.is_running = False
	    print 'Unkown operator. Halting.'

    def execute_0OP(self, opcode):
	print 'executing 0OP'
	if (opcode == 0x0):
	    print 'rtrue'
	    self.ops_return(1)
	elif (opcode == 0x1):
	    print 'rfalse'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x2):
	    print 'print'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x3):
	    print 'print_ret'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x4):
	    print 'nop'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x5):
	    version = self.header.get_z_version()
	    if (version == 1):
		print 'save'
	    elif (version < 5):
		print 'save'
	    else:
		print 'ILLEGAL'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x6):
	    version = self.header.get_z_version()
	    if (version == 1):
		print 'restore'
	    elif (version < 5):
		print 'restore'
	    else:
		print 'ILLEGAL'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x7):
	    print 'restart'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x8):
	    print 'ret_popped'
	    self.ops_return(self.get_variable(0))
	elif (opcode == 0x9):
	    version = self.header.get_z_version()
	    if (version < 5):
		print 'pop'
	    else:
		print 'catch'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xA):
	    print 'quit'
	    self.is_running = False
	elif (opcode == 0xB):
	    print 'new_line'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xC):
	    version = self.header.get_z_version()
	    if (version ==  3):
		print 'show_status'
	    else:
		print 'ILLEGAL'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xD):
	    print 'verify'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xE):
	    print '*extended*'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xF):
	    print 'piracy'
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	else:
	    self.is_running = False
	    print 'Unkown operator. Halting.'

    def execute_VAR(self, opcode, operands):
	print 'executing VAR'
	if (opcode == 0x0):
	    print 'call_vs', operands
	    self.ops_call(operands, True)
	    print self.num_locals, self.num_args
	elif (opcode == 0x1):
	    print 'storew', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x2):
	    print 'storeb', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x3):
	    print 'put_prop', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x4):
	    version = self.header.get_z_version()
	    if (version < 4):
		print 'sread', operands
	    elif (version == 4):
		print 'sread', operands
	    else:
		print 'aread', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x5):
	    print 'print_char', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x6):
	    print 'print_num', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x7):
	    print 'random', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x8):
	    print 'push', operands
	    self.set_variable(0, operands[0])
	elif (opcode == 0x9):
	    print 'pull', operands
	    self.set_variable(operands[0], self.get_variable(0))
	elif (opcode == 0xA):
	    print 'split_window', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xB):
	    print 'set_window', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xC):
	    print 'call_vs2', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xD):
	    print 'erase_window', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xE):
	    print 'erase_line', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xF):
	    print 'set_cursor', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x10):
	    print 'get_cursor', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x11):
	    print 'set_text_style', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x12):
	    print 'buffer_mode', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x13):
	    print 'output_stream', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x14):
	    print 'input_stream', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x15):
	    print 'sound_effect', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x16):
	    print 'read_char', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x17):
	    print 'scan_table', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x18):
	    print 'not', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x19):
	    print 'call_vn', operands
	    self.ops_call(operands, False)
	    print self.num_locals, self.num_args
	elif (opcode == 0x1A):
	    print 'call_vn2', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x1B):
	    print 'tokenise', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x1C):
	    print 'encode_text', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x1D):
	    print 'copy_table', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x1E):
	    print 'print_table', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x1F):
	    print 'check_arg_count', operands, self.num_args
	    self.ops_branch(operands[0] <= self.num_args)
	else:
	    self.is_running = False
	    print 'Unkown operator. Halting.'

    def execute_EXT(self, opcode, operands):
	print 'executing EXT'
	if (opcode == 0x0):
	    print 'save', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x1):
	    print 'restore', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x2):
	    print 'log_shift', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x3):
	    print 'art_shift', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x4):
	    print 'set_font', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0x9):
	    print 'save_undo', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xA):
	    print 'restore_undo', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xB):
	    print 'print_unicode', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	elif (opcode == 0xC):
	    print 'check_unicode', operands
	    self.is_running = False
	    print 'NOT IMPLEMENTED. Halting.'
	else:
	    self.is_running = False
	    print 'Unkown operator. Halting.'

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
	if (opcode & 32):
	    force_2OP = False
	else:
	    print 'forcing 2OP.'
	    force_2OP = True
	opcode &= 0x1F # lower 5 bits give operator type
	print "actual opcode 0x%02x" % opcode
	operands = self.get_operands(types)
	#bit 5 gives operand count
	#0 == 2 operands, 1 == var. # of operands
	if (force_2OP):
	    self.execute_2OP(opcode, operands)
	else:
	    self.execute_VAR(opcode, operands)
	#for ops call_vs2 and call_vn2 a second byte of operand types is given

    def decode_short(self, opcode):
	print 'short form'
	#bits 5 and 4 give operand type:
	types = [(opcode & 0x30) >> 4]
	print 'operand types', types
	#00 == large const (word), 01 == small const (byte), 10 == variable (byte), 11 == omitted
	#0 or 1 operands	
	opcode &= 0xF # lower 4 bits give operator type
	print "actual opcode 0x%02x" % opcode
	if (types[0] == 3):
	    self.execute_0OP(opcode)
	else:
	    operands = self.get_operands(types)
	    self.execute_1OP(opcode, operands)

    def decode_extended(self):
	print 'extended form'
	#always var. # of operands
	#opcode in next byte
	#next next byte gives 4 operand types, from left to right
	#11 omitts all subsequent operands
	self.execute_EXT(opcode, operands)

    def decode_long(self, opcode):
	print 'long form'
	#bits 6 and 5 give operand types
	types = [1, 1]
	if (opcode & 64):
	    types[0] = 2
	if (opcode & 32):
	    types[1] = 2
	print 'operand types', types
	opcode &= 0x1F # lower 5 bits give operator type
	print "actual opcode 0x%02x" % opcode
	operands = self.get_operands(types)
	self.execute_2OP(opcode, operands)

    def run(self):
	# fetch-and-execute loop
	self.is_running = True

	while (self.is_running):
		opcode = self.heap.read_byte(self.pc)
		self.pc += 1
		self.exec_count += 1
		print '\nOpcode:', opcode, self.exec_count
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
