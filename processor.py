import sys
import struct
import logging
from string import whitespace

import zoperator
import memory
import stack
import streams
import zstring

logging.basicConfig(filename='Bronze.log', filemode='wb', level=logging.DEBUG)
logger = logging.getLogger('processor')

class Processor:
    def __init__(self, memory, stack, out_screen, out_transcript, out_memory, out_command, in_keyboard, in_file, debug = False):
        self.memory = memory

        self.debug = debug
        self.breakpoints = []

        self.header = self.memory.get_header()
        self.pc = self.header.get_initial_pc()
        self.object_table = self.memory.get_object_table()
        self.dictionary = self.memory.get_dictionary()

        self.stack = stack

        self.output = {}
        self.output['screen'] = out_screen
        self.output['screen'].select()
        self.output['transcript'] = out_transcript
        self.output['memory'] = out_memory
        self.output['command'] = out_command
        self.input = {}
        self.input['keyboard'] = in_keyboard
        self.input['file'] = in_file
        self.selected_input = 'keyboard'
        self.arg_count = 0
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
     
    def resolve_vars(self, operands):
	"""
	Replaces variable numbers with their values.
	"""
	values = []
        for type, value in operands:
            if (type == 2):
                values.append(self.get_variable(value))
                logger.debug("resolved var. %d to #%04x" % (value, values[-1]))
            else:
                values.append(value)
        return values

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
        if (version < 4): unpacked = address * 2
        elif (version < 6): unpacked = address * 4
        elif (version == 8): unpacked = address * 8
        logger.debug("unpacked address: %x" % unpacked)
        return unpacked

    def get_variable(self, variable_number):
        if (variable_number == 0):
            return self.stack.pop()
        elif (variable_number < 16):
            return self.stack.get_local(variable_number - 1)
        elif (variable_number < 256):
            return self.memory.read_word(self.header.get_globals_table_location() + 2 * (variable_number - 16))
        else:
            logger.error('Illegal variable: ' + str(variable_number))
            self.is_running = False
            return 0

    def set_variable(self, variable_number, value):
        if (variable_number == 0):
            self.stack.push(value)
        elif (variable_number < 16):
            self.stack.set_local(variable_number - 1, value)
        elif (variable_number < 256):
            self.memory.write_word(self.header.get_globals_table_location() + 2 * (variable_number - 16), value)
        else:
            logger.error('Illegal variable: ' + str(variable_number))
            self.is_running = False
            return 0

    def call_helper(self, tail, operands):
        return_address = tail.get_new_pc()
        result_variable = tail.get_result_var()
        new_pc = self.unpack_address(operands[0])
        operands = operands[1:]
        if (new_pc == 0):
            logger.error('call to address 0 not implemented.')
            self.is_running = False
        else:
            self.stack.push_call(return_address, result_variable, self.arg_count)
            self.arg_count = len(operands)
            num_locals = self.memory.read_byte(new_pc)
            #print 'locals:', num_locals
            new_pc += 1
            self.stack.set_num_locals(num_locals)
            if (self.header.get_z_version < 5):
                for i in range(num_locals):
                    self.stack.set_local(i, self.heap.read_word(new_pc))
                    new_pc += 2
            operands = operands[:num_locals]
            for i in range(len(operands)):
                self.stack.set_local(i, operands[i])
        return new_pc

    def return_helper(self, return_value):
        new_pc, result_variable, self.arg_count = self.stack.pop_call()
        if not (result_variable == None):
            self.set_variable(result_variable, return_value)
            logger.debug("storing %d in variable %d" % (return_value, result_variable))
        return new_pc

    def store_helper(self, tail, value):
        self.set_variable(tail.get_result_var(), value)
        return tail.get_new_pc()

    def branch_helper(self, tail, condition):
        is_offset, offset = tail.get_branch_offset(condition)
        if is_offset:
            return tail.get_new_pc() + offset
        else:
            return self.return_helper(offset)

    def output_helper(self, string, is_echo = False):
        version = self.header.get_z_version()
        if (version < 3):
            self.output['screen'].selected = True

        if self.output['memory'].selected:
            self.output['memory'].write(string)
        else:
            if self.output['screen'].selected and not is_echo:
                self.output['screen'].write(string)
            if self.output['transcript'].selected:
                self.output['transcript'].write(string)
            if self.output['command'].selected and is_echo:
                self.output['command'].write(string)

    def parse_helper(self, parse_buffer, input, dictionary):
        version = self.header.get_z_version()
        max_words = self.heap.read_byte(parse_buffer)
        separators = dictionary.get_word_separators()
        words = []
        word = ''
        index = 0
        start = 0
        for char in input.lower():
            if (char in whitespace) and not (word == ''):
                words.append((start, word))
                word = ''
                start = index + 1
            elif char in separators:
                words.append((start, word))
                words.append((index, char))
                word = ''
                start = index + 1
            else:
                word += char
            index += 1
        words.append((start, word))
        print words
        words = words[:max_words]
        self.heap.write_byte(parse_buffer + 1, len(words))
        parse_buffer += 2
        for start, word in words[:max_words]:
            encoded = zstring.ZString()
            encoded.encode(word)
            small = 1
            big = dictionary.get_num_entries()
            while small <= big:
                avg = (small + big) / 2
                pivot = dictionary.get_encoded_text(avg)
                for a, b in zip(pivot, encoded.pack_words()):
                    a = a & 0x7fff
                    b = b & 0x7fff
                    if not (a == b):
                        break  # for

                if (a == b):
                    break  # while
                elif (a < b):
                    small = avg + 1
                else:
                    big = avg - 1
            if (a == b):
                self.heap.write_word(parse_buffer, dictionary.get_entry_addr(avg))
            else:
                self.heap.write_word(parse_buffer, 0)
            # write number of letters in word and start position
            self.heap.write_byte(parse_buffer + 2, len(word))
            if (version < 5):
                self.heap.write_byte(parse_buffer + 3, start + 1)
            else:
                self.heap.write_byte(parse_buffer + 3, start + 2)
            parse_buffer += 4

    def op2str(self, pc, name, head, tail):
            return ("@%04x: " % pc) + name + ' ' + str(head) + str(tail)

    def execute_2OP(self, head):
        logger.debug('executing 2OP')
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        if (opcode == 0x1):
            tail = zoperator.Tail(head, False, True, False)
            logger.debug(self.op2str(self.pc, 'je', head, tail))
            condition = False
            for operand in operands[1:]:
                if (operand == operands[0]):
                    condition = True
            self.pc = self.branch_helper(tail, condition)
        elif (opcode == 0x2):
            tail = zoperator.Tail(head, False, True, False)
            logger.debug(self.op2str(self.pc, 'jl', head, tail))
            self.pc = self.branch_helper(tail, self.signed_word(operands[0]) < self.signed_word(operands[1]))
        elif (opcode == 0x3):
            tail = zoperator.Tail(head, False, True, False)
            logger.debug(self.op2str(self.pc, 'jg', head, tail))
            self.pc = self.branch_helper(tail, self.signed_word(operands[0]) > self.signed_word(operands[1]))
        elif (opcode == 0x4):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('dec_chk ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x5):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('inc_chk ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x6):
            tail = zoperator.Tail(head, False, True, False)
            logger.debug(self.op2str(self.pc, 'jin', head, tail))
            #print self.object_table.get_object_parent(operands[0]), operands[1]
            self.pc = self.branch_helper(tail, self.object_table.get_object_parent(operands[0]) == operands[1])
        elif (opcode == 0x7):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('test ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x8):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'or', head, tail))
            if (not len(operands) == 2):
                self.is_running = False
                print 'Unkown operator. Halting.'
            self.pc = self.store_helper(tail, operands[0] | operands[1])
        elif (opcode == 0x9):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'and', head, tail))
            if (not len(operands) == 2): #TODO: remove this block ???
                self.is_running = False
                print 'Unkown operator. Halting.'
            self.pc = self.store_helper(tail, operands[0] & operands[1])
        elif (opcode == 0xA):
            tail = zoperator.Tail(head, False, True, False)
            logger.debug(self.op2str(self.pc, 'test_attr', head, tail))
            self.pc = self.branch_helper(tail, self.object_table.get_object_attribute(operands[0], operands[1]))
            #print self.object_table.get_object_attribute(operands[0], 15), operands[0], operands[1]
        elif (opcode == 0xB):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'set_attr', head, tail))
            #print operands[0], operands[1]
            #print self.object_table.get_object_attribute(operands[0], operands[1])
            self.object_table.set_object_attribute(operands[0], operands[1])
            self.pc = tail.get_new_pc()
            #print self.object_table.get_object_attribute(operands[0], operands[1])
        elif (opcode == 0xC):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('clear_attr ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xD):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'store', head, tail))
            self.set_variable(operands[0], operands[1])
            self.pc = tail.get_new_pc()
        elif (opcode == 0xE):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('insert_obj ' + str(operands))
            self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)
            print '[insert_obj %d %d]' % (operands[0], operands[1])

            parent = self.object_table.get_object_parent(operands[0])
            self.object_table.set_object_parent(operands[0], 0)

            if (parent > 0):
                sibling = self.object_table.get_object_sibling(operands[0])
                self.object_table.set_object_sibling(operands[0], 0)
                parent_child = self.object_table.get_object_child(parent)
                if (parent_child == operands[0]):
                    self.object_table.set_object_child(parent, sibling)
                else:
                    other_sibling = parent_child
                    next = self.object_table.get_object_sibling(other_sibling)
                    while (next > 0) and not (next == operands[0]):
                        other_sibling = next
                        next = self.object_table.get_object_sibling(other_sibling)
                    if (next == 0):
                        print 'ERROR: Malformed object tree.'
                        self.is_running = False
                    else:
                        self.object_table.set_object_sibling(other_sibling, sibling)

            new_sibling = self.object_table.get_object_child(operands[1])
            self.object_table.set_object_sibling(operands[0], new_sibling)
            self.object_table.set_object_parent(operands[0], operands[1])
            self.object_table.set_object_child(operands[1], operands[0])

            self.pc = tail.get_new_pc()
            self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)
        elif (opcode == 0xF):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'loadw', head, tail))
            self.pc = self.store_helper(tail, self.memory.read_word(operands[0] + 2 * operands[1]))
        elif (opcode == 0x10):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'loadb', head, tail))
            self.pc = self.store_helper(tail, self.memory.read_byte(operands[0] + operands[1]))
        elif (opcode == 0x11):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'get_prop', head, tail))
            self.pc = self.store_helper(tail, self.object_table.get_property_data(operands[0], operands[1]))
            #print "%04x" % self.get_variable(255)
        elif (opcode == 0x12):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'get_prop_addr', head, tail))
            logger.debug('get_prop_addr ' + str(operands))
            #prop_addr = self.object_table.get_property_addr(operands[0], operands[1])
            #print "%04x" % prop_addr
            #print self.object_table.get_property_number(prop_addr)
            #print "%04x" % self.object_table.get_property(operands[0], operands[1])
            self.pc = self.store_helper(tail, self.object_table.get_property_data_addr(operands[0], operands[1]))
        elif (opcode == 0x13):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('get_next_prop ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x14):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'add', head, tail))
            self.pc = self.store_helper(tail, (operands[0] + operands[1]) % (1 << 16))
            #print "%04x" % self.stack.peek()
        elif (opcode == 0x15):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'sub', head, tail))
            self.pc = self.store_helper(tail, (operands[0] - operands[1]) % (1 << 16))
            #TODO: check if implemented properly (x + (-y))
        elif (opcode == 0x16):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'mul', head, tail))
            self.pc = self.store_helper(tail, int((operands[0] * operands[1]) % (1 << 16)))
            #print self.stack.peek()
        elif (opcode == 0x17):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'div', head, tail))
            self.pc = self.store_helper(tail, self.unsigned_word(self.signed_word(operands[0]) / self.signed_word(operands[1])))
        elif (opcode == 0x18):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('mod ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x19):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'call_2s', head, tail))
            self.pc = self.call_helper(tail, operands)
        elif (opcode == 0x1A):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'call_2n', head, tail))
            self.pc = self.call_helper(tail, operands)
        elif (opcode == 0x1B):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('set_colour ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1C):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('throw ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute_1OP(self, head):
        logger.debug('executing 1OP')
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        if (opcode == 0x0):
            tail = zoperator.Tail(head, False, True, False)
            logger.debug(self.op2str(self.pc, 'jz', head, tail))
            self.pc = self.branch_helper(tail, operands[0] == 0)
        elif (opcode == 0x1):
            tail = zoperator.Tail(head, True, True, False)
            logger.debug(self.op2str(self.pc, 'get_sibling', head, tail))
            sibling = self.object_table.get_object_sibling(operands[0])
            self.store_helper(tail, sibling)
            self.pc = self.branch_helper(tail, not sibling == 0)
        elif (opcode == 0x2):
            tail = zoperator.Tail(head, True, True, False)
            logger.debug(self.op2str(self.pc, 'get_child', head, tail))
            child = self.object_table.get_object_child(operands[0])
            self.store_helper(tail, child)
            self.pc = self.branch_helper(tail, not child == 0)
            #print operands[0], child, "%x" % self.pc
        elif (opcode == 0x3):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'get_parent', head, tail))
            parent = self.object_table.get_object_parent(operands[0])
            #print parent
            self.pc = self.store_helper(tail, parent)
        elif (opcode == 0x4):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'get_prop_len', head, tail))
            number, size = self.object_table.get_property_info_backwards(operands[0])
            self.pc = self.store_helper(tail, size)
        elif (opcode == 0x5):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'inc', head, tail))
            self.set_variable(operands[0], self.unsigned_word(self.signed_word(self.get_variable(operands[0])) + 1))
            self.pc = tail.get_new_pc()
        elif (opcode == 0x6):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'dec', head, tail))
            self.set_variable(operands[0], self.unsigned_word(self.signed_word(self.get_variable(operands[0])) - 1))
            self.pc = tail.get_new_pc()
        elif (opcode == 0x7):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'print_addr', head, tail))
            addr = operands[0]
            self.pc, string = self.heap.read_string(addr)
            self.output_helper(string)
            self.pc = tail.get_new_pc()
        elif (opcode == 0x8):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'call_1s', head, tail))
            self.pc = self.call_helper(tail, operands)
        elif (opcode == 0x9):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('remove_obj ' + str(operands))
            self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)
            print '[remove_obj %d]' % operands[0]

            parent = self.object_table.get_object_parent(operands[0])
            sibling = self.object_table.get_object_sibling(operands[0])
            child = self.object_table.get_object_child(operands[0])
            parent_child = self.object_table.get_object_child(parent)

            print '***', operands[0]
            print '***', parent, sibling, child

            print '##', parent_child
            while (self.object_table.get_object_sibling(parent_child)):
                parent_child = self.object_table.get_object_sibling(parent_child)
                print '##', parent_child

            self.object_table.set_object_parent(operands[0], 0)

            if (parent > 0):
                sibling = self.object_table.get_object_sibling(operands[0])
                self.object_table.set_object_sibling(operands[0], 0)
                parent_child = self.object_table.get_object_child(parent)
                if (parent_child == operands[0]):
                    self.object_table.set_object_child(parent, sibling)
                else:
                    other_sibling = parent_child
                    next = self.object_table.get_object_sibling(other_sibling)
                    while (next > 0) and not (next == operands[0]):
                        other_sibling = next
                        next = self.object_table.get_object_sibling(other_sibling)
                    if (next == 0):
                        print 'ERROR: Malformed object tree.'
                        self.is_running = False
                    else:
                        self.object_table.set_object_sibling(other_sibling, sibling)

            self.pc = tail.get_new_pc()
            self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)
        elif (opcode == 0xA):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('print_obj ' + str(operands))
            self.output_helper(self.object_table.get_object_short_name(operands[0]))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xB):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'ret', head, tail))
            self.pc = self.return_helper(operands[0])
        elif (opcode == 0xC):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'jump', head, tail))
            self.pc = tail.get_new_pc() + self.signed_word(operands[0]) - 2
            #print self.signed_word(operands[0])
            #print "%04x" % self.pc
        elif (opcode == 0xD):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'print_paddr', head, tail))
            addr = self.unpack_address(operands[0])
            self.pc, string = self.memory.read_string(addr)
            self.output_helper(str(string))
            self.pc = tail.get_new_pc()
        elif (opcode == 0xE):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('load ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xF):
            version = self.header.get_z_version()
            if (version < 5):
                tail = zoperator.Tail(head, True, False, False)
                logger.debug(self.op2str(self.pc, 'not', head, tail))
                self.is_running = False
                print 'NOT IMPLEMENTED. Halting.'
            else:
                tail = zoperator.Tail(head, False, False, False)
                logger.debug(self.op2str(self.pc, 'call_1n', head, tail))
                self.pc = self.call_helper(tail, operands)
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute_0OP(self, head):
        logger.debug('executing 0OP')
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        if (opcode == 0x0):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'rtrue', head, tail))
            self.pc = self.return_helper(1)
        elif (opcode == 0x1):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'rfalse', head, tail))
            self.pc = self.return_helper(0)
        elif (opcode == 0x2):
            tail = zoperator.Tail(head, False, False, True)
            logger.debug(self.op2str(self.pc, 'print', head, tail))
            self.pc, string = self.memory.read_string(tail.get_new_pc())
            self.output_helper(str(string))
            #TODO: include string and length handling with tail
        elif (opcode == 0x3):
            tail = zoperator.Tail(head, False, False, True)
            logger.debug(self.op2str(self.pc, 'print_ret', head, tail))
            self.pc, string = self.heap.read_string(tail.get_new_pc())
            self.output_helper(string)
            self.pc = self.return_helper(1)
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x4):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('nop')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x5):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
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
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
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
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('restart')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x8):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'ret_popped', head, tail))
            self.pc = self.return_helper(self.get_variable(0))
        elif (opcode == 0x9):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            version = self.header.get_z_version()
            if (version < 5):
                logger.debug('pop')
            else:
                logger.debug('catch')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xA):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('quit')
            self.is_running = False
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xB):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'new_line', head, tail))
            self.output_helper("\n")
            self.pc = tail.get_new_pc()
        elif (opcode == 0xC):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            version = self.header.get_z_version()
            if (version ==  3):
                logger.debug('show_status')
            else:
                print 'ILLEGAL'
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xD):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('verify')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xE):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            print '*extended*'
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xF):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('piracy')
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute_VAR(self, head):
        logger.debug('executing VAR')
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        if (opcode == 0x0):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'call_vs', head, tail))
            self.pc = self.call_helper(tail, operands)
            logger.debug("locals %d, args %d" % (self.stack.get_num_locals(), self.arg_count))
            #print "%x" % self.pc
        elif (opcode == 0x1):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'storew', head, tail))
            self.memory.write_word(operands[0] + 2 * operands[1], operands[2])
            self.pc = tail.get_new_pc()
        elif (opcode == 0x2):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'storeb', head, tail))
            if(operands[2] > 255):
                self.is_running = False
                logger.error('Trying to store word')
            self.memory.write_byte(operands[0] + operands[1], operands[2])
            self.pc = tail.get_new_pc()
        elif (opcode == 0x3):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'put_prop', head, tail))
            self.object_table.set_property_addr(operands[0], operands[1], operands[2])
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x4):
            version = self.header.get_z_version()
            if (version < 4):
                tail = zoperator.Tail(head, False, False, False)
                logger.debug(self.op2str(self.pc, 'sread', head, tail))
                #TODO: redisplay status line
                self.is_running = False
                print 'NOT IMPLEMENTED. Halting.'
                #TODO: read until CR
            elif (version == 4):
                tail = zoperator.Tail(head, False, False, False)
                logger.debug(self.op2str(self.pc, 'sread', head, tail))
                #TODO: read until CR
                self.is_running = False
                print 'NOT IMPLEMENTED. Halting.'
            else:
                tail = zoperator.Tail(head, True, False, False)
                logger.debug(self.op2str(self.pc, 'aread', head, tail))
                #TODO: read until CR or any other terminating character
                max_len = self.heap.read_byte(operands[0])
                input = self.input[self.selected_input].read(max_len, 0, '')
                self.heap.write_byte(operands[0] + 1, len(input) - 1)
                addr = operands[0] + 2
                for char in input[:-1]:
                    self.heap.write_byte(addr, ord(char))
                    addr += 1
                if not (operands[1] == 0):
                    self.parse_helper(operands[1], input[:-1], self.dictionary)
                self.pc = self.store_helper(tail, ord(input[-1]))
        elif (opcode == 0x5):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'print_char', head, tail))
            self.output_helper(chr(operands[0]))
            self.pc = tail.get_new_pc()
        elif (opcode == 0x6):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'print_num', head, tail))
            self.output_helper(str(self.signed_word(operands[0])))
            self.pc = tail.get_new_pc()
        elif (opcode == 0x7):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'random', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x8):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'push', head, tail))
            self.set_variable(0, operands[0])
            self.pc = tail.get_new_pc()
        elif (opcode == 0x9):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'pull', head, tail))
            self.set_variable(operands[0], self.get_variable(0))
            self.pc = tail.get_new_pc()
        elif (opcode == 0xA):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'split_window', head, tail))
            self.output['screen'].screen.split_window(operands[0])
            self.pc = tail.get_new_pc()
        elif (opcode == 0xB):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'set_window', head, tail))
            self.output['screen'].screen.set_window(operands[0])
            self.pc = tail.get_new_pc()
        elif (opcode == 0xC):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'call_vs2', head, tail))
            self.pc = self.call_helper(tail, operands)
        elif (opcode == 0xD):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'erase_window', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xE):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'erase_line', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xF):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'set_cursor', head, tail))
            logger.debug('set_cursor ' + str(operands))
            self.output['screen'].screen.set_cursor(operands[0], operands[1])
            self.pc = tail.get_new_pc()
        elif (opcode == 0x10):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'get_cursor', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x11):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'set_text_style', head, tail))
            self.output['screen'].screen.set_text_style(operands[0])
            self.pc = tail.get_new_pc()
        elif (opcode == 0x12):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'buffer_mode', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x13):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'output_stream', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x14):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'input_stream', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x15):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'sound_effect', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x16):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'read_char', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x17):
            tail = zoperator.Tail(head, True, True, False)
            logger.debug(self.op2str(self.pc, 'scan_table', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x18):
            tail = zoperator.Tail(head, True, False, False)
            logger.debug(self.op2str(self.pc, 'not', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x19):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'call_vn', head, tail))
            self.pc = self.call_helper(tail, operands)
            logger.debug("locals %d, args %d" % (self.stack.get_num_locals(), self.arg_count))
        elif (opcode == 0x1A):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'call_vn2', head, tail))
            self.pc = self.call_helper(tail, operands)
            logger.debug("locals %d, args %d" % (self.stack.get_num_locals(), self.arg_count))
        elif (opcode == 0x1B):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'tokenise', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1C):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'encode_text', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1D):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'copy_table', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1E):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, 'print_table', head, tail))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1F):
            tail = zoperator.Tail(head, False, True, False)
            logger.debug(self.op2str(self.pc, 'check_arg_count', head, tail))
            logger.debug("arg count: %d" % self.arg_count)
            self.pc = self.branch_helper(tail, operands[0] <= self.arg_count)
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute_EXT(self, head):
        logger.debug('executing EXT')
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        if (opcode == 0x0):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('save ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x1):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('restore ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x2):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('log_shift ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x3):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('art_shift ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x4):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('set_font ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0x9):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('save_undo ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xA):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('restore_undo ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xB):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('print_unicode ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        elif (opcode == 0xC):
            tail = zoperator.Tail(head, False, False, False)
            logger.debug(self.op2str(self.pc, '', head, tail))
            logger.debug('check_unicode ' + str(operands))
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        else:
            self.is_running = False
            print 'Unkown operator. Halting.'

    def execute(self):
        head = zoperator.Head(self.memory, self.pc)
        #TODO: use ints for optype
        if (head.get_optype() == '2OP'):
            self.execute_2OP(head)
        elif (head.get_optype() == '1OP'):
            self.execute_1OP(head)
        elif (head.get_optype() == '0OP'):
            self.execute_0OP(head)
        elif (head.get_optype() == 'VAR'):
            self.execute_VAR(head)
        elif (head.get_optype() == 'EXT'):
            self.execute_EXT(head)
        self.exec_count += 1

    def run(self):
        # fetch-and-execute loop
        self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)

        if self.debug:
            while (True):
                cmd = raw_input('Debugger@0x%x: ' % self.pc).upper().split()
                if (len(cmd) > 0):
                    if (cmd[0] == 'QUIT'):
                        break
                    elif (cmd[0] == 'RUN'):
                        self.is_running = True
                        while (self.is_running):
                            if self.pc in self.breakpoints:
                                self.is_running = False
                                print 'Breaking at 0x%x' % self.pc
                            else:
                                self.execute()
                    elif (cmd[0] == 'STEP'):
                            self.execute()
                    elif (cmd[0] == 'BREAK'):
                        if (len(cmd) > 1):
                            breakpoint =  int(cmd[1], 16)
                            self.breakpoints.append(breakpoint)
                        print 'Breakpoints:'
                        for breakpoint in sorted(self.breakpoints):
                            print '%x' % breakpoint
                    elif (cmd[0] == 'UNBREAK'):
                        if (len(cmd) > 1):
                            breakpoint =  int(cmd[1], 16)
                            self.breakpoints.remove(breakpoint)
                        print 'Breakpoints:'
                        for breakpoint in sorted(self.breakpoints):
                            print '%x' % breakpoint
                    elif (cmd[0] == 'PRINT'):
                        print cmd[1]
                        if (cmd[1][0] == 'L'):
                            variable_number = int(cmd[1][1:], 16) 
                            
                            print 'Local variable %x: 0x%04x' % (variable_number, self.get_variable(1 + variable_number))
                        elif (cmd[1][0] == 'G'):
                            variable_number =  int(cmd[1][1:], 16) 
                            print 'Global variable %x: 0x%04x' % (variable_number, self.get_variable(16 + variable_number))
                        elif (cmd[1] == 'SP'):
                            print 'Stack:'
                            self.stack.print_current()
                            if (self.stack.get_size() > 0):
                                print 'Top of stack: 0x%04x' % self.stack.peek()
                        else:
                            addr = int(cmd[1], 16)
                            print 'Memory at %x: %04x' % (addr, self.heap.read_word(addr))
                    elif (cmd[0] == 'TRACE'):
                        pass
                    elif (cmd[0] == 'UNTRACE'):
                        pass
                    elif (cmd[0] == 'RESET'):
                        self.pc = self.header.get_initial_pc()
                    else:
                        print 'Unknown debugger command', cmd
                else:
                    print 'Unknown debugger command', cmd
        else:
            self.is_running = True
            while (self.is_running):
                self.execute()

    def reset(self):
        pass


