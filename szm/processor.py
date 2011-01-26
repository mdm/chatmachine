import sys
import struct
from string import whitespace
import random

import zoperator
import memory
import stack
import streams
import zstring


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
        self.op_total = 0
        
        self.lut_2op = {0x1: self.execute_2op_je, 0x2: self.execute_2op_jl, 0x3: self.execute_2op_jg, 0x4: self.execute_2op_dec_chk, 0x5: self.execute_2op_inc_chk, 0x6: self.execute_2op_jin, 0x7: self.execute_2op_test, 0x8: self.execute_2op_or, 0x9: self.execute_2op_and, 0xA: self.execute_2op_test_attr, 0xB: self.execute_2op_set_attr, 0xC: self.execute_2op_clear_attr, 0xD: self.execute_2op_store, 0xE: self.execute_2op_insert_obj, 0xF: self.execute_2op_loadw, 0x10: self.execute_2op_loadb, 0x11: self.execute_2op_get_prop, 0x12: self.execute_2op_get_prop_addr, 0x13: self.execute_2op_get_next_prop, 0x14: self.execute_2op_add, 0x15: self.execute_2op_sub, 0x16: self.execute_2op_mul, 0x17: self.execute_2op_div, 0x18: self.execute_2op_mod, 0x19: self.execute_2op_call_2s, 0x1A: self.execute_2op_call_2n, 0x1B: self.execute_2op_set_colour, 0x1C: self.execute_2op_throw}
        
        self.lut_1op = {0x0: execute_1op_jz, 0x1: execute_1op_get_sibling, 0x2: execute_1op_get_child, 0x3: execute_1op_get_parent, 0x4: execute_1op_get_prop_len, 0x5: execute_1op_inc, 0x6: execute_1op_dec, 0x7: execute_1op_print_addr, 0x8: execute_1op_call_1s, 0x9: execute_1op_remove_obj, 0xA: execute_1op_print_obj, 0xB: execute_1op_ret, 0xC: execute_1op_jump, 0xD: execute_1op_print_paddr, 0xE: execute_1op_load, 0xF: execute_1op_not_or_call_1n}
        
        self.lut_0op = {0x0: execute_0op_rtrue, 0x1: execute_0op_rfalse, 0x2: execute_0op_print, 0x3: execute_0op_print_ret, 0x4: execute_0op_nop, 0x5: execute_0op_save, 0x6: execute_0op_restore, 0x7: execute_0op_restart, 0x8: execute_0op_ret_popped, 0x9: execute_0op_pop_or_catch, 0xA: execute_0op_quit, 0xB: execute_0op_new_line, 0xC: execute_0op_show_status, 0xD: execute_0op_verify, 0xE: execute_0op_, 0xF: execute_0op_piracy}
        
        self.lut_var = {0x0: execute_var_call_vs, 0x1: execute_var_storew, 0x2: execute_var_storeb, 0x3: execute_var_put_prop, 0x4: execute_var_sread_or_aread, 0x5: execute_var_print_char, 0x6: execute_var_print_num, 0x7: execute_var_random, 0x8: execute_var_push, 0x9: execute_var_pull, 0xA: execute_var_split_window, 0xB: execute_var_set_window, 0xC: execute_var_call_vs2, 0xD: execute_var_erase_window, 0xE: execute_var_erase_line, 0xF: execute_var_set_cursor, 0x10: execute_var_get_cursor, 0x11: execute_var_set_text_style, 0x12: execute_var_buffer_mode, 0x13: execute_var_output_stream, 0x14: execute_var_input_stream, 0x15: execute_var_sound_effect, 0x16: execute_var_read_char, 0x17: execute_var_scan_table, 0x18: execute_var_not, 0x19: execute_var_call_vn, 0x1A: execute_var_call_vn2, 0x1B: execute_var_tokenise, 0x1C: execute_var_encode_text, 0x1D: execute_var_copy_table, 0x1E: execute_var_print_table, 0x1F: execute_var_check_arg_count}
        
        self.lut_ext = {0x0: execute_ext_save, 0x1: execute_ext_restore, 0x2: execute_ext_log_shift, 0x3: execute_ext_art_shift, 0x4: execute_ext_set_font, 0x9: execute_ext_save_undo, 0xA: execute_ext_restore_undo, 0xB: execute_ext_print_unicode, 0xC: execute_ext_check_unicode}

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
                #logger.debug("resolved var. %02x to #%04x" % (value, values[-1]))
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
        return unpacked

    def get_variable(self, variable_number):
        if (variable_number == 0):
            return self.stack.pop()
        elif (variable_number < 16):
            return self.stack.get_local(variable_number - 1)
        elif (variable_number < 256):
            return self.memory.read_word(self.header.get_globals_table_location() + 2 * (variable_number - 16))
        else:
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
            self.is_running = False
            return 0

    def call_helper(self, tail, operands):
        return_address = tail.get_new_pc()
        result_variable = tail.get_result_var()
        new_pc = self.unpack_address(operands[0])
        operands = operands[1:]
        if (new_pc == 0):
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
        max_words = self.memory.read_byte(parse_buffer)
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
        self.memory.write_byte(parse_buffer + 1, len(words))
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
                self.memory.write_word(parse_buffer, dictionary.get_entry_addr(avg))
            else:
                self.memory.write_word(parse_buffer, 0)
            # write number of letters in word and start position
            self.memory.write_byte(parse_buffer + 2, len(word))
            if (version < 5):
                self.memory.write_byte(parse_buffer + 3, start + 1)
            else:
                self.memory.write_byte(parse_buffer + 3, start + 2)
            parse_buffer += 4

    def op2str(self, pc, name, head, tail):
            #return ("@%04x: " % pc) + name + ' ' + str(head) + str(tail)
            return ''

    def execute_2op_je(self, head, operands):
        tail = zoperator.Tail(head, False, True, False)
        condition = False
        for operand in operands[1:]:
            if (operand == operands[0]):
                condition = True
        self.pc = self.branch_helper(tail, condition)
    
    def execute_2op_jl(self, head, operands):
        tail = zoperator.Tail(head, False, True, False)
        self.pc = self.branch_helper(tail, self.signed_word(operands[0]) < self.signed_word(operands[1]))
    
    def execute_2op_jg(self, head, operands):
        tail = zoperator.Tail(head, False, True, False)
        self.pc = self.branch_helper(tail, self.signed_word(operands[0]) > self.signed_word(operands[1]))
    
    def execute_2op_dec_chk(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'dec_chk', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_2op_inc_chk(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'inc_chk', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_2op_jin(self, head, operands):
        tail = zoperator.Tail(head, False, True, False)
        #print self.object_table.get_object_parent(operands[0]), operands[1]
        self.pc = self.branch_helper(tail, self.object_table.get_object_parent(operands[0]) == operands[1])

    def execute_2op_test(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'test', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_2op_or(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        if (not len(operands) == 2):
            self.is_running = False
            print 'Unkown operator. Halting.'
        self.pc = self.store_helper(tail, operands[0] | operands[1])

    def execute_2op_and(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        if (not len(operands) == 2): #TODO: remove this block ???
            self.is_running = False
            print 'Unkown operator. Halting.'
        self.pc = self.store_helper(tail, operands[0] & operands[1])

    def execute_2op_test_attr(self, head, operands):
        tail = zoperator.Tail(head, False, True, False)
        self.pc = self.branch_helper(tail, self.object_table.get_object_attribute(operands[0], operands[1]))
        #print self.object_table.get_object_attribute(operands[0], 15), operands[0], operands[1]

    def execute_2op_set_attr(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #print operands[0], operands[1]
        #print self.object_table.get_object_attribute(operands[0], operands[1])
        self.object_table.set_object_attribute(operands[0], operands[1])
        self.pc = tail.get_new_pc()
        #print self.object_table.get_object_attribute(operands[0], operands[1])

    def execute_2op_clear_attr(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        self.object_table.clear_object_attribute(operands[0], operands[1])
        self.pc = tail.get_new_pc()

    def execute_2op_store(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        self.set_variable(operands[0], operands[1])
        self.pc = tail.get_new_pc()

    def execute_2op_insert_obj(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)
        #print '[insert_obj %d %d]' % (operands[0], operands[1])
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
        #self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)

    def execute_2op_loadw(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        self.pc = self.store_helper(tail, self.memory.read_word(operands[0] + 2 * operands[1]))

    def execute_2op_loadb(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        self.pc = self.store_helper(tail, self.memory.read_byte(operands[0] + operands[1]))

    def execute_2op_get_prop(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        self.pc = self.store_helper(tail, self.object_table.get_property_data(operands[0], operands[1]))
        #print "%04x" % self.get_variable(255)

    def execute_2op_get_prop_addr(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        #prop_addr = self.object_table.get_property_addr(operands[0], operands[1])
        #print "%04x" % prop_addr
        #print self.object_table.get_property_number(prop_addr)
        #print "%04x" % self.object_table.get_property(operands[0], operands[1])
        self.pc = self.store_helper(tail, self.object_table.get_property_data_addr(operands[0], operands[1]))

    def execute_2op_get_next_prop(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'get_next_prop', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_2op_add(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        self.pc = self.store_helper(tail, (operands[0] + operands[1]) % (1 << 16))
        #print "%04x" % self.stack.peek()

    def execute_2op_sub(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        self.pc = self.store_helper(tail, (operands[0] - operands[1]) % (1 << 16))
        #TODO: check if implemented properly (x + (-y))

    def execute_2op_mul(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        self.pc = self.store_helper(tail, int((operands[0] * operands[1]) % (1 << 16)))
        #print self.stack.peek()

    def execute_2op_div(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        self.pc = self.store_helper(tail, self.unsigned_word(self.signed_word(operands[0]) / self.signed_word(operands[1])))

    def execute_2op_mod(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'mod', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_2op_call_2s(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        self.pc = self.call_helper(tail, operands)

    def execute_2op_call_2n(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        self.pc = self.call_helper(tail, operands)

    def execute_2op_set_colour(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        self.output['screen'].screen.set_colour(operands[0], operands[1])
        self.pc = tail.get_new_pc()

    def execute_2op_throw(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'throw', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_1op_jz(self, head, operands):
        tail = zoperator.Tail(head, False, True, False)
        #logger.debug(self.op2str(self.pc, 'jz', head, tail))
        self.pc = self.branch_helper(tail, operands[0] == 0)

    def execute_1op_get_sibling(self, head, operands):
        tail = zoperator.Tail(head, True, True, False)
        #logger.debug(self.op2str(self.pc, 'get_sibling', head, tail))
        sibling = self.object_table.get_object_sibling(operands[0])
        self.store_helper(tail, sibling)
        self.pc = self.branch_helper(tail, not sibling == 0)

    def execute_1op_get_child(self, head, operands):
        tail = zoperator.Tail(head, True, True, False)
        #logger.debug(self.op2str(self.pc, 'get_child', head, tail))
        child = self.object_table.get_object_child(operands[0])
        self.store_helper(tail, child)
        self.pc = self.branch_helper(tail, not child == 0)
        #print operands[0], child, "%x" % self.pc

    def execute_1op_get_parent(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        #logger.debug(self.op2str(self.pc, 'get_parent', head, tail))
        parent = self.object_table.get_object_parent(operands[0])
        #print parent
        self.pc = self.store_helper(tail, parent)

    def execute_1op_get_prop_len(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        #logger.debug(self.op2str(self.pc, 'get_prop_len', head, tail))
        number, size = self.object_table.get_property_info_backwards(operands[0])
        self.pc = self.store_helper(tail, size)

    def execute_1op_inc(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'inc', head, tail))
        self.set_variable(operands[0], self.unsigned_word(self.signed_word(self.get_variable(operands[0])) + 1))
        self.pc = tail.get_new_pc()

    def execute_1op_dec(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'dec', head, tail))
        self.set_variable(operands[0], self.unsigned_word(self.signed_word(self.get_variable(operands[0])) - 1))
        self.pc = tail.get_new_pc()

    def execute_1op_print_addr(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'print_addr', head, tail))
        addr = operands[0]
        string = self.heap.read_string(addr)[1]
        self.output_helper(string)
        self.pc = tail.get_new_pc()

    def execute_1op_call_1s(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        #logger.debug(self.op2str(self.pc, 'call_1s', head, tail))
        self.pc = self.call_helper(tail, operands)

    def execute_1op_remove_obj(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'remove_obj', head, tail))
        #self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)
        #print '[remove_obj %d]' % operands[0]
        parent = self.object_table.get_object_parent(operands[0])
        sibling = self.object_table.get_object_sibling(operands[0])
        child = self.object_table.get_object_child(operands[0])
        parent_child = self.object_table.get_object_child(parent)
        #print '***', operands[0]
        #print '***', parent, sibling, child
        #print '##', parent_child
        while (self.object_table.get_object_sibling(parent_child)):
            parent_child = self.object_table.get_object_sibling(parent_child)
            #print '##', parent_child
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
        #self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)

    def execute_1op_print_obj(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'print_obj', head, tail)
        self.output_helper(self.object_table.get_object_short_name(operands[0]))
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_1op_ret(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'ret', head, tail))
        self.pc = self.return_helper(operands[0])

    def execute_1op_jump(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'jump', head, tail))
        self.pc = tail.get_new_pc() + self.signed_word(operands[0]) - 2
        #print self.signed_word(operands[0])
        #print "%04x" % self.pc

    def execute_1op_print_paddr(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'print_paddr', head, tail))
        addr = self.unpack_address(operands[0])
        string = self.memory.read_string(addr)[1]
        self.output_helper(string)
        self.pc = tail.get_new_pc()

    def execute_1op_load(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'load', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_1op_not_or_call_1n(self, head, operands):
        version = self.header.get_z_version()
        #identifier: 'not_or_call_1n'
        if (version < 5):
            tail = zoperator.Tail(head, True, False, False)
            print self.op2str(self.pc, 'not', head, tail)
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        else:
            tail = zoperator.Tail(head, False, False, False)
            #logger.debug(self.op2str(self.pc, 'call_1n', head, tail))
            self.pc = self.call_helper(tail, operands)
    
    def execute_0op_rtrue(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'rtrue', head, tail))
        self.pc = self.return_helper(1)

    def execute_0op_rfalse(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'rfalse', head, tail))
        self.pc = self.return_helper(0)

    def execute_0op_print(self, head, operands):
        tail = zoperator.Tail(head, False, False, True)
        #logger.debug(self.op2str(self.pc, 'print', head, tail))
        self.pc, string = self.memory.read_string(tail.get_new_pc())
        self.output_helper(string)
        #TODO: include string and length handling with tail

    def execute_0op_print_ret(self, head, operands):
        tail = zoperator.Tail(head, False, False, True)
        #logger.debug(self.op2str(self.pc, 'print_ret', head, tail))
        self.pc, string = self.heap.read_string(tail.get_new_pc())
        self.output_helper(string)
        self.pc = self.return_helper(1)

    def execute_0op_nop(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'nop', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_save(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'save', head, tail)
        version = self.header.get_z_version()
        if (version == 1):
            pass
        elif (version < 5):
            pass
        else:
            print 'ILLEGAL'
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_restore(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'restore', head, tail)
        version = self.header.get_z_version()
        if (version == 1):
            pass
        elif (version < 5):
            pass
        else:
            print 'ILLEGAL'
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_restart(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'restart', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_ret_popped(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'ret_popped', head, tail))
        self.pc = self.return_helper(self.get_variable(0))

    def execute_0op_pop_or_catch(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #identifier: 'pop_or_catch'
        version = self.header.get_z_version()
        if (version < 5):
            print self.op2str(self.pc, 'pop', head, tail)
        else:
            print self.op2str(self.pc, 'catch', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_quit(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'quit', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_new_line(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'new_line', head, tail))
        self.output_helper("\n")
        self.pc = tail.get_new_pc()

    def execute_0op_show_status(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'show_status', head, tail)
        version = self.header.get_z_version()
        if (version ==  3):
            pass
        else:
            print 'ILLEGAL'
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_verify(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'verify', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, '', head, tail)
        print '*extended*'
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_0op_piracy(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'piracy', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'
    
    def execute_var_call_vs(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        #logger.debug(self.op2str(self.pc, 'call_vs', head, tail))
        self.pc = self.call_helper(tail, operands)
        #logger.debug("locals %d, args %d" % (self.stack.get_num_locals(), self.arg_count))
        #print "%x" % self.pc

    def execute_var_storew(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'storew', head, tail))
        self.memory.write_word(operands[0] + 2 * operands[1], operands[2])
        self.pc = tail.get_new_pc()

    def execute_var_storeb(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'storeb', head, tail))
        if(operands[2] > 255):
            self.is_running = False
            logger.error('Trying to store word')
        self.memory.write_byte(operands[0] + operands[1], operands[2])
        self.pc = tail.get_new_pc()

    def execute_var_put_prop(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'put_prop', head, tail)
        self.object_table.set_property_data(operands[0], operands[1], operands[2])

    def execute_var_sread_or_aread(self, head, operands):
        version = self.header.get_z_version()
        #identifier: 'sread_or_aread'
        if (version < 4):
            tail = zoperator.Tail(head, False, False, False)
            print self.op2str(self.pc, 'sread', head, tail)
            #TODO: redisplay status line
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
            #TODO: read until CR
        elif (version == 4):
            tail = zoperator.Tail(head, False, False, False)
            print self.op2str(self.pc, 'sread', head, tail)
            #TODO: read until CR
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        else:
            tail = zoperator.Tail(head, True, False, False)
            #logger.debug(self.op2str(self.pc, 'aread', head, tail))
            #TODO: read until CR or any other terminating character
            max_len = self.memory.read_byte(operands[0])
            input = self.input[self.selected_input].read(max_len, 0, '')
            self.memory.write_byte(operands[0] + 1, len(input) - 1)
            addr = operands[0] + 2
            for char in input[:-1]:
                self.memory.write_byte(addr, ord(char))
                addr += 1
            if not (operands[1] == 0):
                self.parse_helper(operands[1], input[:-1], self.dictionary)
            self.pc = self.store_helper(tail, ord(input[-1]))

    def execute_var_print_char(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'print_char', head, tail))
        self.output_helper(chr(operands[0]))
        self.pc = tail.get_new_pc()

    def execute_var_print_num(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'print_num', head, tail))
        self.output_helper(str(self.signed_word(operands[0])))
        self.pc = tail.get_new_pc()

    def execute_var_random(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        #logger.debug(self.op2str(self.pc, 'random', head, tail))
        if (operands[0] > 0):
            self.store_helper(tail, random.randint(1, operands[0]))                
        elif (operands[0] < 0):
            random.seed(operands[0])
            self.store_helper(tail, 0)
        else:
            random.seed()
            self.store_helper(tail, 0)
        self.pc = tail.get_new_pc()

    def execute_var_push(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'push', head, tail))
        self.set_variable(0, operands[0])
        self.pc = tail.get_new_pc()

    def execute_var_pull(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'pull', head, tail))
        self.set_variable(operands[0], self.get_variable(0))
        self.pc = tail.get_new_pc()

    def execute_var_split_window(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'split_window', head, tail))
        self.output['screen'].screen.split_window(operands[0])
        self.pc = tail.get_new_pc()

    def execute_var_set_window(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'set_window', head, tail))
        self.output['screen'].screen.set_window(operands[0])
        self.pc = tail.get_new_pc()

    def execute_var_call_vs2(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        #logger.debug(self.op2str(self.pc, 'call_vs2', head, tail))
        self.pc = self.call_helper(tail, operands)

    def execute_var_erase_window(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'erase_window', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_erase_line(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'erase_line', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_set_cursor(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'set_cursor', head, tail))
        self.output['screen'].screen.set_cursor(operands[0], operands[1])
        self.pc = tail.get_new_pc()

    def execute_var_get_cursor(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'get_cursor', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_set_text_style(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'set_text_style', head, tail))
        self.output['screen'].screen.set_text_style(operands[0])
        self.pc = tail.get_new_pc()

    def execute_var_buffer_mode(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'buffer_mode', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_output_stream(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'output_stream', head, tail)
        #print self.op2str(self.pc, 'output_stream', head, tail)
        operands[0] = self.signed_word(operands[0])
        if (operands[0] > 0):
            if (operands[0] == 1):
                self.output['screen'].select()
            if (operands[0] == 2):
                self.output['transcript'].select()               
            if (operands[0] == 3):
                self.output['memory'].select(operands[1])   
            if (operands[0] == 4):
                self.output['command'].select()
        elif (operands[0] < 0):
            if (operands[0] == -1):
                self.output['screen'].deselect()
            if (operands[0] == -2):
                self.output['transcript'].deselect()               
            if (operands[0] == -3):
                self.output['memory'].deselect()   
            if (operands[0] == -4):
                self.output['command'].deselect()
        else:
            self.is_running = False
            print 'NOT IMPLEMENTED. Halting.'
        self.pc = tail.get_new_pc()

    def execute_var_input_stream(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'input_stream', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_sound_effect(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'sound_effect', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_read_char(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        print self.op2str(self.pc, 'read_char', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_scan_table(self, head, operands):
        tail = zoperator.Tail(head, True, True, False)
        print self.op2str(self.pc, 'scan_table', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_not(self, head, operands):
        tail = zoperator.Tail(head, True, False, False)
        #logger.debug(self.op2str(self.pc, 'not', head, tail))
        self.pc = self.store_helper(tail, (~operands[0]) & 0xffff)

    def execute_var_call_vn(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'call_vn', head, tail))
        self.pc = self.call_helper(tail, operands)
        #logger.debug("locals %d, args %d" % (self.stack.get_num_locals(), self.arg_count))

    def execute_var_call_vn2(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        #logger.debug(self.op2str(self.pc, 'call_vn2', head, tail))
        self.pc = self.call_helper(tail, operands)
        #logger.debug("locals %d, args %d" % (self.stack.get_num_locals(), self.arg_count))

    def execute_var_tokenise(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'tokenise', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_encode_text(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'encode_text', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_copy_table(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'copy_table', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_print_table(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'print_table', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_var_check_arg_count(self, head, operands):
        tail = zoperator.Tail(head, False, True, False)
        #logger.debug(self.op2str(self.pc, 'check_arg_count', head, tail))
        #logger.debug("arg count: %d" % self.arg_count)
        self.pc = self.branch_helper(tail, operands[0] <= self.arg_count)

    def execute_ext_save(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'save', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_ext_restore(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'restore', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_ext_log_shift(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'log_shift', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_ext_art_shift(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'art_shift', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_ext_set_font(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'set_font', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_ext_save_undo(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'save_undo', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_ext_restore_undo(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'restore_undo', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_ext_print_unicode(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'print_unicode', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'

    def execute_ext_check_unicode(self, head, operands):
        tail = zoperator.Tail(head, False, False, False)
        print self.op2str(self.pc, 'check_unicode', head, tail)
        self.is_running = False
        print 'NOT IMPLEMENTED. Halting.'
    
    def execute_2OP(self, head):
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        self.lut_2op[opcode](head, operands)

    def execute_1OP(self, head):
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        self.lut_1op[opcode](head, operands)

    def execute_0OP(self, head):
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        self.lut_0op[opcode](head, operands)

    def execute_VAR(self, head):
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        self.lut_var[opcode](head, operands)

    def execute_EXT(self, head):
        opcode = head.get_opcode()
        operands = self.resolve_vars(head.get_operands())
        self.lut_ext[opcode](head, operands)

    def execute(self):
        head = zoperator.Head(self.memory, self.pc)
        #TODO: use ints for optype
        if (head.get_optype() == 2):
            self.execute_2OP(head)
        elif (head.get_optype() == 1):
            self.execute_1OP(head)
        elif (head.get_optype() == 0):
            self.execute_0OP(head)
        elif (head.get_optype() == 3):
            self.execute_VAR(head)
        elif (head.get_optype() == 4):
            self.execute_EXT(head)
        self.op_total += 1

    def run(self):
        # fetch-and-execute loop
        #self.object_table.dump_dot_file('objects_%d.dot' % self.pc, 232)

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
            print self.op_total

    def reset(self):
        pass


