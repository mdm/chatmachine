#import heap

#_2OP = 0
#_1OP = 1
#_0OP = 2
#_VAR = 3
#_EXT = 4

class Head:
    def __init__(self, code, pc):
	self.code = code
	self.pc = pc
	self.optype = ''
	self.opcode = 0
	self.operand_types = []
	self.operand_values = []
        self.decode()
    
    def __str__(self):
	string_rep = '(' + self.optype + ':' + str(self.opcode) + ') '
	for type, value in self.get_operands():
	    if (type == 0):
		string_rep += "#%04x, " % value
	    elif (type == 1):
		string_rep += "#%02x, " % value
	    elif (type == 2):
		if (value == 0):
		    string_rep += '(SP)+, '
		elif (value < 0x10):
		    string_rep += "L%02x, " % (value - 1)
		elif (value <= 0xff):
		    string_rep += "G%02x, " % (value - 0x10)
        if not (self.optype == '0OP'):
            string_rep = string_rep[:-2] + ' '
        return string_rep

    def get_optype(self):
	return self.optype

    def get_opcode(self):
	return self.opcode

    def get_operands(self):
	return zip(self.operand_types, self.operand_values)

    def get_new_pc(self):
        return self.pc

    ### helper functions ###

    def decode(self):
	# TODO: automatically decode and find another way to pass back new_pc
	first_byte = self.code.read_byte(self.pc)
        self.pc += 1
	if ((first_byte & 192) == 192):
	    self.decode_variable(first_byte)
	elif ((first_byte & 192) == 128):
	    self.decode_short(first_byte)
	elif (first_byte == 0xBE):
	    self.decode_extended()
	else:
	    self.decode_long(first_byte)

    def get_operand_values(self, types):
        tmp = []        
        for type in types:
            if (type == 0): # large constant
                tmp.append(self.code.read_word(self.pc))
                self.pc += 2
            else: # small constant (1), or variable (2)
                tmp.append(self.code.read_byte(self.pc))
                self.pc += 1
        return tmp

    def decode_variable(self, first_byte):
        #logger.debug('variable form')

        if (first_byte & 0b00100000): # checking bit 5 for optype
            self.optype = 'VAR'
        else:
            self.optype = '2OP'

        self.opcode = first_byte & 0b00011111 # lower 5 bits give opcode
	
        # next byte gives 4 operand types, from left to right
        # 0b11 omitts all subsequent operands
        self.operand_types = []
        mask = 0b11000000
        mask_pos = 3
        packed_types = self.code.read_byte(self.pc)
        self.pc += 1
        while (mask > 0):
            tmp = (packed_types & mask) >> (2 * mask_pos)
            if (tmp == 3): break
            self.operand_types.append(tmp)
            mask >>= 2
            mask_pos -= 1

        # for ops call_vs2 and call_vn2 a second byte of operand types is given
        if (self.optype == 'VAR') and (self.opcode in [0x1A, 0xC]):
            mask = 0b11000000
            mask_pos = 3
            packed_types = self.code.read_byte(self.pc)
            self.pc += 1
            while (mask > 0):
                tmp = (packed_types & mask) >> (2 * mask_pos)
                if (tmp == 3): break
                self.operand_types.append(tmp)
                mask >>= 2
                mask_pos -= 1
            
        self.operand_values = self.get_operand_values(self.operand_types)

    def decode_short(self, first_byte):
        #logger.debug('short form')

        #bits 5 and 4 give operand type:
        self.operand_types = [(first_byte & 0b00110000) >> 4]

        if (self.operand_types[0] == 0b11):
            self.optype = '0OP'
	    self.operand_types = []
        else:
            self.optype = '1OP'

        self.opcode = first_byte & 0b00001111 # lower 4 bits give operator type
        self.operand_values = self.get_operand_values(self.operand_types)

    def decode_extended(self, first_byte):
        logger.debug('extended form')
        #always var. # of operands
        #opcode in next byte
        #next next byte gives 4 operand types, from left to right
        #11 omitts all subsequent operands
        self.execute_EXT(opcode, operands)

    def decode_long(self, first_byte):
        #logger.debug('long form')
	
	self.optype = '2OP'

        self.opcode = first_byte & 0b00011111 # lower 5 bits give operator type

        # bits 6 and 5 give operand types
        self.operand_types = [1, 1]
        if (first_byte & 0b01000000):
            self.operand_types[0] = 2
        if (first_byte & 0b00100000):
            self.operand_types[1] = 2

	self.operand_values = self.get_operand_values(self.operand_types)


class Tail:
    def __init__(self, head, is_storing, is_branching, has_string):
        self.pc = head.get_new_pc()
        self.code = head.code
        self.is_storing = is_storing
        self.is_branching = is_branching
        self.has_string = has_string
        self.result_var = None
        self.branch_on_false = False
        self.branch_offset = None
        self.decode()
        # TODO: init tail from head

    def __str__(self):
        string_rep = ''
        if (self.is_storing):
            string_rep += '-> '
            if (self.result_var == 0):
                string_rep += '-(SP) '
            elif (self.result_var < 0x10):
                string_rep += "L%02x " % (self.result_var - 1)
            elif (self.result_var <= 0xff):
                string_rep += "G%02x " % (self.result_var - 0x10)
        if (self.is_branching):
            if self.branch_on_false:
                string_rep += '[FALSE] '
            else:
                string_rep += '[TRUE] '
            is_offset, offset = self.get_branch_offset(not self.branch_on_false)
            if is_offset:
                string_rep += "%x" % (self.pc + offset)
            else:
                if offset:
                    string_rep += 'RTRUE'
                else:
                    string_rep += 'RFALSE'
        if (self.has_string):
            pass
        return string_rep

    def get_result_var(self):
        return self.result_var

    def get_branch_offset(self, condition):
        if not (self.branch_on_false == condition):
            if (0 <= self.branch_offset < 2):
                return (False, self.branch_offset)
            else:
                return (True, self.branch_offset - 2)
	    return (is_offset, self.branch_offset)
        else:
            return (True, 0)

    def get_string(self):
        #TODO: implement correctly`
        pass

    def get_new_pc(self):
        return self.pc

    ### helper functions ###

    def decode(self):
        if self.is_storing:
            self.result_var = self.code.read_byte(self.pc)
            self.pc += 1
        if self.is_branching:
            self.branch_offset = self.decode_branching()
        if self.has_string:
            pass # TODO: decode string here or in processor?
	return self.pc

    def decode_branching(self):
        offset = self.code.read_byte(self.pc)
        self.pc += 1
        if (offset & 0b10000000):
            self.branch_on_false = False
        else:
            self.branch_on_false = True

        if (offset & 0b01000000):
            offset &= 0b00111111
        else:
            offset = ((offset & 0b00111111) << 8) + self.code.read_byte(self.pc)
            if (offset > 0x1fff):
                offset -= (1 << 14)
            self.pc += 1
        return offset

