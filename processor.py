import sys
import struct
import logging

import heap
import stack
import stream
import zstring

logging.basicConfig(filename='Bronze.log', filemode='wb', level=logging.DEBUG)
logger = logging.getLogger('processor')

class Processor:
    def __init__(self, heap):
        self.heap = heap
        self.header = self.heap.get_header()
        self.pc = self.header.get_initial_pc()
        self.object_table = self.heap.get_object_table()
        self.stack = stack.Stack()
        self.output = stream.OutputStream()
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
                logger.debug('getting variable ' + str(variable_number))
                tmp.append(self.get_variable(variable_number))
        return tmp

    def signed_word(self, word):
        if (word > 0x7FFF):
            return word - (1 << 16)
        else:
            return word

    def unsigned_word(self, word):
        if (word < 0):
            return word + (1 << 16)
        else:
            return word
    
    def unpack_address(self, address):
        version = self.header.get_z_version()
        logger.debug('unpacking address')
        if (version < 4): return address * 2
        elif (version < 6): return address * 4
        elif (version == 8): return address * 8
        else: return 0 #TODO: unsupported version error

    def get_variable(self, variable_number):
        if (variable_number == 0):
            return self.stack.pop()
        elif (variable_number < 16):
            return self.stack.get_value(variable_number - 1)
        elif (variable_number < 256):
            return self.heap.read_word(self.header.get_globals_table_location() + 2 * (variable_number - 16))
        else:
            logger.error('Illegal variable: ' + str(variable_number))
            return 0

    def set_variable(self, variable_number, value):
        if (variable_number == 0):
            self.stack.push(value)
        elif (variable_number < 16):
            self.stack.set_value(variable_number - 1, value)
        elif (variable_number < 256):
            self.heap.write_word(self.header.get_globals_table_location() + 2 * (variable_number - 16), value)
        else:
            logger.error('Illegal variable: ' + str(variable_number))
            return 0

    def ops_call(self, operands, store_result):
        address = self.unpack_address(operands[0])
        logger.debug(address)
        if (address == 0):
            logger.error('call to address 0 not implemented.')
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
            logger.debug('branch on True')
        else:
            logger.debug('branch on False')

        if not (offset & 64):
            offset = ((offset & 0x3f) << 8) + self.heap.read_byte(self.pc)
            self.pc += 1
            logger.debug('branch address is 2 bytes: ' + str(offset))
        else:
            offset &= 0x3f
            logger.debug('branch address is 1 bytes: ' +  str(offset))

        if (not condition):
            if (offset < 2):
                logger.debug('return from branch ' +  str(offset))
                self.ops_return(offset)
            else:
                self.pc += offset - 2

    def ops_return(self, return_value):
        self.pc, result_variable, self.num_locals, self.num_args = self.stack.pop_frame()
        if not (result_variable == None):
            self.set_variable(result_variable, return_value)
            logger.debug("storing %d in variable %d" % (return_value, result_variable))

    def ops_store(self, value):
        result_variable = self.heap.read_byte(self.pc)
        logger.debug("storing %d in variable %d" % (value, result_variable))
        self.pc += 1
        self.set_variable(result_variable, value)

    def execute_2OP(self, opcode, operands):
        logger.debug('executing 2OP')
        if (opcode == 0x1):
            logger.debug('je ' + str(operands))
            condition = False
            for operand in operands[1:]:
                if (operand == operands[0]):
                    condition = True
            self.ops_branch(condition)
        elif (opcode == 0x2):
            logger.debug('jl ' + str(operands))
            self.ops_branch(self.signed_word(operands[0]) < self.signed_word(operands[1]))
        elif (opcode == 0x3):
            logger.debug('jg ' + str(operands))
            self.ops_branch(self.signed_word(operands[0]) > self.signed_word(operands[1]))
        elif (opcode == 0x4):
            logger.debug('dec_chk ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x5):
            logger.debug('inc_chk ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x6):
            logger.debug('jin ' + str(operands))
            self.ops_branch(self.object_table.get_object_parent(operands[0]) == operands[1])
        elif (opcode == 0x7):
            logger.debug('test ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x8):
            logger.debug('or ' + str(operands))
            if (not len(operands) == 2):
                self.is_running = False
                print 'Unkown operator. Halting.'
            self.ops_store(operands[0] | operands[1])
        elif (opcode == 0x9):
            logger.debug('and ' + str(operands))
            if (not len(operands) == 2):
                self.is_running = False
                print 'Unkown operator. Halting.'
            self.ops_store(operands[0] & operands[1])
        elif (opcode == 0xA):
            logger.debug('test_attr ' + str(operands))
            self.ops_branch(self.object_table.get_object_attribute(operands[0], operands[1]))
        elif (opcode == 0xB):
            logger.debug('set_attr ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xC):
            logger.debug('clear_attr ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xD):
            logger.debug('store ' + str(operands))
            self.set_variable(operands[0], operands[1])
        elif (opcode == 0xE):
            logger.debug('insert_obj ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xF):
            logger.debug('loadw ' + str(operands))
            self.ops_store(self.heap.read_word(operands[0] + 2 * operands[1]))
        elif (opcode == 0x10):
            logger.debug('loadb ' + str(operands))
            self.ops_store(self.heap.read_word(operands[0] + operands[1]))
        elif (opcode == 0x11):
            logger.debug('get_prop ' + str(operands))
            self.ops_store(self.object_table.get_property(operands[0], operands[1]))
        elif (opcode == 0x12):
            logger.debug('get_prop_addr ' + str(operands))
            self.ops_store(self.object_table.get_property_addr(operands[0], operands[1]))
        elif (opcode == 0x13):
            logger.debug('get_next_prop ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x14):
            logger.debug('add ' + str(operands))
            self.ops_store((operands[0] + operands[1]) % (1 << 16))
        elif (opcode == 0x15):
            logger.debug('sub ' + str(operands))
            self.ops_store((operands[0] - operands[1]) % (1 << 16))
        elif (opcode == 0x16):
            logger.debug('mul ' + str(operands))
            self.ops_store(int((operands[0] * operands[1]) % (1 << 16)))
        elif (opcode == 0x17):
            logger.debug('div ' + str(operands))
            self.ops_store(self.unsigned_word(self.signed_word(operands[0]) / self.signed_word(operands[1])))
        elif (opcode == 0x18):
            logger.debug('mod ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x19):
            logger.debug('call_2s ' + str(operands))
            self.ops_call(operands, True)
        elif (opcode == 0x1A):
            logger.debug('call_2n ' + str(operands))
            self.ops_call(operands, False)
        elif (opcode == 0x1B):
            logger.debug('set_colour ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1C):
            logger.debug('throw ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute_1OP(self, opcode, operands):
        logger.debug('executing 1OP')
        if (opcode == 0x0):
            logger.debug('jz ' + str(operands))
            self.ops_branch(operands[0] == 0)
        elif (opcode == 0x1):
            logger.debug('get_sibling ' + str(operands))
            sibling = self.object_table.get_object_sibling(operands[0])
            self.ops_store(sibling)
            self.ops_branch(not sibling == 0)
        elif (opcode == 0x2):
            logger.debug('get_child ' + str(operands))
            child = self.object_table.get_object_child(operands[0])
            self.ops_store(child)
            self.ops_branch(not child == 0)
        elif (opcode == 0x3):
            logger.debug('get_parent ' + str(operands))
            parent = self.object_table.get_object_parent(operands[0])
            self.ops_store(parent)
        elif (opcode == 0x4):
            logger.debug('get_prop_len ' + str(operands))
            length = self.object_table.get_property_length(operands[0])[1]
            self.ops_store(length)
        elif (opcode == 0x5):
            logger.debug('inc ' + str(operands))
            self.set_variable(operands[0], self.unsigned_word(self.signed_word(self.get_variable(operands[0])) + 1))
        elif (opcode == 0x6):
            logger.debug('dec ' + str(operands))
            self.set_variable(operands[0], self.unsigned_word(self.signed_word(self.get_variable(operands[0])) - 1))
        elif (opcode == 0x7):
            logger.debug('print_addr ' + str(operands))
            addr = operands[0]
            string = zstring.ZString()
            while(string.add(self.heap.read_word(addr))):
                addr += 2
            self.output.show(string)
        elif (opcode == 0x8):
            logger.debug('call_1s ' + str(operands))
            self.ops_call(operands, True)
        elif (opcode == 0x9):
            logger.debug('remove_obj ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xA):
            logger.debug('print_obj ' + str(operands))
            self.output.show(self.object_table.get_object_short_name(operands[0]))
        elif (opcode == 0xB):
            logger.debug('ret ' + str(operands))
            self.ops_return(operands[0])
        elif (opcode == 0xC):
            logger.debug('jump ' + str(operands))
            self.pc += self.signed_word(operands[0]) - 2
        elif (opcode == 0xD):
            logger.debug('print_paddr ' + str(operands))
            addr = self.unpack_address(operands[0])
            string = zstring.ZString()
            while(string.add(self.heap.read_word(addr))):
                addr += 2
            self.output.show(string)
        elif (opcode == 0xE):
            logger.debug('load ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xF):
            version = self.header.get_z_version()
            if (version < 5):
                logger.debug('not ' + str(operands))
                self.is_running = False
                print 'NOT IMPLEMENTED. Halting.'
            else:
                logger.debug('call_1n ' + str(operands))
                self.ops_call(operands, False)
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute_0OP(self, opcode):
        logger.debug('executing 0OP')
        if (opcode == 0x0):
            logger.debug('rtrue')
            self.ops_return(1)
        elif (opcode == 0x1):
            logger.debug('rfalse')
            self.ops_return(0)
        elif (opcode == 0x2):
            logger.debug('print')
            addr = self.pc
            string = zstring.ZString()
            while(string.add(self.heap.read_word(addr))):
                addr += 2
            self.pc = addr + 2
            self.output.show(string)
        elif (opcode == 0x3):
            logger.debug('print_ret')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x4):
            logger.debug('nop')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x5):
            version = self.header.get_z_version()
            if (version == 1):
                logger.debug('save')
            elif (version < 5):
                logger.debug('save')
            else:
                print 'ILLEGAL'
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x6):
            version = self.header.get_z_version()
            if (version == 1):
                logger.debug('restore')
            elif (version < 5):
                logger.debug('restore')
            else:
                print 'ILLEGAL'
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x7):
            logger.debug('restart')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x8):
            logger.debug('ret_popped')
            self.ops_return(self.get_variable(0))
        elif (opcode == 0x9):
            version = self.header.get_z_version()
            if (version < 5):
                logger.debug('pop')
            else:
                logger.debug('catch')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xA):
            logger.debug('quit')
            self.is_running = False
        elif (opcode == 0xB):
            logger.debug('new_line')
            self.output.new_line()
        elif (opcode == 0xC):
            version = self.header.get_z_version()
            if (version ==  3):
                logger.debug('show_status')
            else:
                print 'ILLEGAL'
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xD):
            logger.debug('verify')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xE):
            print '*extended*'
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xF):
            logger.debug('piracy')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute_VAR(self, opcode, operands):
        logger.debug('executing VAR')
        if (opcode == 0x0):
            logger.debug('call_vs ' + str(operands))
            self.ops_call(operands, True)
            logger.debug("locals %d, args %d" % (self.num_locals, self.num_args))
        elif (opcode == 0x1):
            logger.debug('storew ' + str(operands))
            self.heap.write_word(operands[0] + 2 * operands[1], operands[2])
        elif (opcode == 0x2):
            logger.debug('storeb ' + str(operands))
            if(operands[2] > 255):
                print 'ERROR: Trying to store word'
            self.heap.write_byte(operands[0] + operands[1], operands[2])
        elif (opcode == 0x3):
            logger.debug('put_prop ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x4):
            version = self.header.get_z_version()
            if (version < 4):
                logger.debug('sread ' + str(operands))
            elif (version == 4):
                logger.debug('sread ' + str(operands))
            else:
                logger.debug('aread ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x5):
            logger.debug('print_char ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x6):
            logger.debug('print_num ' + str(operands))
            self.output.show(self.signed_word(operands[0]))
        elif (opcode == 0x7):
            logger.debug('random ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x8):
            logger.debug('push ' + str(operands))
            self.set_variable(0, operands[0])
        elif (opcode == 0x9):
            logger.debug('pull ' + str(operands))
            self.set_variable(operands[0], self.get_variable(0))
        elif (opcode == 0xA):
            logger.debug('split_window ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xB):
            logger.debug('set_window ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xC):
            logger.debug('call_vs2 ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xD):
            logger.debug('erase_window ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xE):
            logger.debug('erase_line ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xF):
            logger.debug('set_cursor ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x10):
            logger.debug('get_cursor ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x11):
            logger.debug('set_text_style ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x12):
            logger.debug('buffer_mode ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x13):
            logger.debug('output_stream ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x14):
            logger.debug('input_stream ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x15):
            logger.debug('sound_effect ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x16):
            logger.debug('read_char ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x17):
            logger.debug('scan_table ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x18):
            logger.debug('not ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x19):
            logger.debug('call_vn ' + str(operands))
            self.ops_call(operands, False)
            logger.debug("locals %d, args %d" % (self.num_locals, self.num_args))
        elif (opcode == 0x1A):
            logger.debug('call_vn2 ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1B):
            logger.debug('tokenise ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1C):
            logger.debug('encode_text ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1D):
            logger.debug('copy_table ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1E):
            logger.debug('print_table ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1F):
            logger.debug("check_arg_count %s %d" % (operands, self.num_args))
            self.ops_branch(operands[0] <= self.num_args)
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute_EXT(self, opcode, operands):
        logger.debug('executing EXT')
        if (opcode == 0x0):
            logger.debug('save ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1):
            logger.debug('restore ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x2):
            logger.debug('log_shift ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x3):
            logger.debug('art_shift ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x4):
            logger.debug('set_font ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x9):
            logger.debug('save_undo ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xA):
            logger.debug('restore_undo ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xB):
            logger.debug('print_unicode ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xC):
            logger.debug('check_unicode ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def decode_variable(self, opcode):
        logger.debug('variable form')
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
        logger.debug(("operand types 0x%02x" % packed_types) + str(types))
        if (opcode & 32):
            force_2OP = False
        else:
            logger.debug('forcing 2OP.')
            force_2OP = True
        opcode &= 0x1F # lower 5 bits give operator type
        logger.debug("actual opcode 0x%02x" % opcode)
        operands = self.get_operands(types)
        #bit 5 gives operand count
        #0 == 2 operands, 1 == var. # of operands
        if (force_2OP):
            self.execute_2OP(opcode, operands)
        else:
            self.execute_VAR(opcode, operands)
        #for ops call_vs2 and call_vn2 a second byte of operand types is given

    def decode_short(self, opcode):
        logger.debug('short form')
        #bits 5 and 4 give operand type:
        types = [(opcode & 0x30) >> 4]
        logger.debug('operand types ' + str(types))
        #00 == large const (word), 01 == small const (byte), 10 == variable (byte), 11 == omitted
        #0 or 1 operands        
        opcode &= 0xF # lower 4 bits give operator type
        logger.debug("actual opcode 0x%02x" % opcode)
        if (types[0] == 3):
            self.execute_0OP(opcode)
        else:
            operands = self.get_operands(types)
            self.execute_1OP(opcode, operands)

    def decode_extended(self):
        logger.debug('extended form')
        #always var. # of operands
        #opcode in next byte
        #next next byte gives 4 operand types, from left to right
        #11 omitts all subsequent operands
        self.execute_EXT(opcode, operands)

    def decode_long(self, opcode):
        logger.debug('long form')
        #bits 6 and 5 give operand types
        types = [1, 1]
        if (opcode & 64):
            types[0] = 2
        if (opcode & 32):
            types[1] = 2
        logger.debug('operand types ' + str(types))
        opcode &= 0x1F # lower 5 bits give operator type
        logger.debug("actual opcode 0x%02x" % opcode)
        operands = self.get_operands(types)
        self.execute_2OP(opcode, operands)

    def run(self):
        # fetch-and-execute loop
        self.is_running = True

        while (self.is_running):
                opcode = self.heap.read_byte(self.pc)
                self.pc += 1
                self.exec_count += 1
                logger.debug("\nOpcode: %d, %d" % (opcode, self.exec_count))
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
cpu = Processor(heap)
cpu.run()

print 'Goodbye'
