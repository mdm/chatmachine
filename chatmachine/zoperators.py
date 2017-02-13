class Operator(object):
    def __init__(self, start, name, code):
        self.start = start
        self.name = name
        self.code = code
        self.operands = []
        self.is_call = False
        self.is_return = False
        self.store = None
        self.branch = None
    
    def load_constant(self, constant):
        self.operands.append(('constant', constant))
    
    def load_variable(self, variable):
        self.operands.append(('variable', variable))
    
    def do_call(self):
        self.is_call = True
        
    def do_return(self):
        self.is_return = True
        
    def store_variable(self, variable):
        self.store = variable
        
    def next(self, address, branch = None):
        self.next = address
        self.branch = branch
    
    def assemble(self, debugging):
        #TODO: ommit operands for 0OPs
        assembled = 'operands = []\n'
        for op_type, op_value in self.operands:
            if op_type == 'constant':
                assembled += 'operands.append(%d)\n' % op_value
            else:
                # variable
                if op_value == 0:
                    assembled += 'operands.append(self.stack.pop())\n'
                elif (op_value < 0x10):
                    assembled += 'operands.append(self.stack.get_local(%d))\n' % (op_value - 1)
                else:
                    #TODO: inline table location
                    assembled += 'operands.append(self.memory.read_word(self.header.get_globals_table_location() + %d))\n' % ((op_value - 0x10) << 1)
                    
        assembled += self.code
        
        if (self.is_call):
            if (self.store == None):
                assembled += 'if not (operands[0] == 0):\n' \
                             '    self.stack.push_call(init_locals, %d, None, len(operands) - 1)\n' % self.next
            else:
            	assembled += 'if (operands[0] == 0):\n'
                if self.store == 0:
                    assembled += '    self.stack.push(0)\n'
                elif (self.store < 0x10):
                    assembled += '    self.stack.set_local(%d, 0)\n' % (self.store - 1)
                else:
                    assembled += '    self.memory.write_word(self.header.get_globals_table_location() + %d, 0)\n' % ((self.store - 0x10) << 1)
                assembled += '    next = %d\n' \
                             'else:\n' \
                             '    self.stack.push_call(init_locals, %d, %d, len(operands) - 1)\n' % (self.next, self.next, self.store)
        else:
            if not (self.store == None):
                if self.store == 0:
                    assembled += 'self.stack.push(result)\n'
                elif (self.store < 0x10):
                    assembled += 'self.stack.set_local(%d, result)\n' % (self.store - 1)
                else:
                    assembled += 'self.memory.write_word(self.header.get_globals_table_location() + %d, result)\n' % ((self.store - 0x10) << 1)
        if (self.branch):
            #TODO: handle branch offset of 2 (no branch)
            assembled += 'if (bool(result) == %s):\n' % str(self.branch[0])
            if (self.branch[1] == 0 or self.branch[1] == 1):
                assembled += '    result = %d\n' \
                          '    return_address, result_variable, _ = self.stack.pop_call()\n' \
                          '    if not (result_variable == None):\n' \
                          '        if (result_variable == 0):\n' \
                          '            self.stack.push(result)\n' \
                          '        elif (result_variable < 0x10):\n' \
                          '            self.stack.set_local(result_variable - 1, result)\n' \
                          '        else:\n' \
                          '            self.memory.write_word(self.header.get_globals_table_location() + ((result_variable - 0x10) << 1), result)\n' \
                          '    next = return_address\n' % self.branch[1]
            else:
                assembled += '    next = %d\n' % ((self.next + self.branch[1] - 2) & 0xffff)
            assembled += 'else:\n' \
                      '    next = %d\n' % self.next
        
        if(self.is_return):
            assembled += 'return_address, result_variable, _ = self.stack.pop_call()\n' \
                         'if not (result_variable == None):\n' \
                         '    if (result_variable == 0):\n' \
                         '        self.stack.push(result)\n' \
                         '    elif (result_variable < 0x10):\n' \
                         '        self.stack.set_local(result_variable - 1, result)\n' \
                         '    else:\n' \
                         '        self.memory.write_word(self.header.get_globals_table_location() + ((result_variable - 0x10) << 1), result)\n' \
                         'next = return_address\n'
        
        continuable = (self.branch == None) and not self.is_call and not self.is_return and not (self.name == 'jump')
        if debugging and continuable:
            assembled += 'next = %d\n' % self.next
            return assembled, False
        else:
            return assembled, continuable
        
    def __str__(self):
        parts = [self.name.upper(), ' ']
        operands = []
        
        if (self.is_call):
            if self.operands[0][0] == 'constant':
                parts.append('%x ' % (self.operands[0][1] << 1))
            else:
                if self.operands[0][1] == 0:
                    parts.append('(SP)+ ')
                elif self.operands[0][1] < 0x10:
                    parts.append('L%02x ' % (self.operands[0][1] - 1))
                else:
                    parts.append('G%02x ' % (self.operands[0][1] - 0x10))
            parts.append('(')
            for op_type, op_value in self.operands[1:]:
                if op_type == 'constant':
                    operands.append('#%02x' % op_value)
                else:
                    if op_value == 0:
                        operands.append('(SP)+')
                    elif op_value < 0x10:
                        operands.append('L%02x' % (op_value - 1))
                    else:
                        operands.append('G%02x' % (op_value - 0x10))
            parts.append(','.join(operands))
            parts.append(')')
        else:
            for op_type, op_value in self.operands:
                if op_type == 'constant':
                    operands.append('#%02x' % op_value)
                else:
                    if op_value == 0:
                        operands.append('(SP)+')
                    elif op_value < 0x10:
                        operands.append('L%02x' % (op_value - 1))
                    else:
                        operands.append('G%02x' % (op_value - 0x10))
            parts.append(','.join(operands))
            
        if not (self.store == None):
            if self.store == 0:
                parts.append(' -> -(SP)')
            elif (self.store < 0x10):
                parts.append(' -> L%02x' % (self.store - 1))
            else:
                parts.append(' -> G%02x' % (self.store - 0x10))
                
        if self.branch:
            parts.append(' [')
            parts.append(str(self.branch[0]).upper())
            parts.append('] ')
            if (self.branch[1] == 0):
                parts.append('RFALSE')
            elif (self.branch[1] == 1):
                parts.append('RTRUE')
            else:
                parts.append('%x' % ((self.next + self.branch[1] - 2) & 0xffff))

        return ''.join(parts)

class DecoderV1(object):
    def __init__(self, memory):
        self.memory = memory
        self.packed_address_shift = 1
        
        self.names = {}
        self.names['2OP'] = {
            0x1: 'je',
            0x2: 'jl',
            0x3: 'jg',
            0x4: 'dec_chk',
            0x5: 'inc_chk',
            0x6: 'jin',
            0x7: 'test',
            0x8: 'or',
            0x9: 'and',
            0xA: 'test_attr',
            0xB: 'set_attr',
            0xC: 'clear_attr',
            0xD: 'store',
            0xE: 'insert_obj',
            0xF: 'loadw',
            0x10: 'loadb',
            0x11: 'get_prop',
            0x12: 'get_prop_addr',
            0x13: 'get_next_prop',
            0x14: 'add',
            0x15: 'sub',
            0x16: 'mul',
            0x17: 'div',
            0x18: 'mod'
        }
        self.names['1OP'] = {
            0x0: 'jz',
            0x1: 'get_sibling',
            0x2: 'get_child',
            0x3: 'get_parent',
            0x4: 'get_prop_len',
            0x5: 'inc',
            0x6: 'dec',
            0x7: 'print_addr',
            0x9: 'remove_obj',
            0xA: 'print_obj',
            0xB: 'ret',
            0xC: 'jump',
            0xD: 'print_paddr',
            0xE: 'load',
            0xF: 'not'
        }
        self.names['0OP'] = {
            0x0: 'rtrue',
            0x1: 'rfalse',
            0x2: 'print',
            0x3: 'print_ret',
            0x4: 'nop',
            0x5: 'save',
            0x6: 'restore',
            0x7: 'restart',
            0x8: 'ret_popped',
            0x9: 'pop',
            0xA: 'quit',
            0xB: 'new_line'
        }
        self.names['VAR'] = {
            0x0: 'call',
            0x1: 'storew',
            0x2: 'storeb',
            0x3: 'put_prop',
            0x4: 'sread',
            0x5: 'print_char',
            0x6: 'print_num',
            0x7: 'random',
            0x8: 'push',
            0x9: 'pull'
        }
        
        self.effects = {}
        self.effects['store'] = ['or', 'and', 'loadw', 'loadb', 'get_prop', 'get_prop_addr', 'get_next_prop', 'add', 'sub', 'mul', 'div', 'mod', 'get_sibling', 'get_child', 'get_parent', 'get_prop_len', 'load', 'not', 'call', 'random']
        self.effects['branch'] = ['je', 'jl', 'jg', 'dec_chk', 'inc_chk', 'jin', 'test', 'test_attr', 'jz', 'get_sibling', 'get_child', 'save', 'restore', ]
        self.effects['call'] = ['call']
        self.effects['return'] = ['ret', 'rtrue', 'rfalse', 'print_ret', 'ret_popped']
        #self.effects['print'] = ['print_addr', 'print_obj', 'print_paddr', 'print', 'print_ret', 'new_line', 'print_char', 'print_num']
        #self.effects['parse'] = ['sread']
        
        self.code = {}
        self.code['add'] = 'result = (operands[0] + operands[1]) & 0xffff\n'
        self.code['and'] = 'result = operands[0] & operands[1]\n'
        #TODO: remove exception below
        self.code['call'] = 'if not (operands[0] == 0):\n' \
                            '    operands[0] <<= %d\n' \
                            '    num_locals = self.memory.read_byte(operands[0])\n' \
                            '    if (len(operands) - 1 > num_locals):\n' \
                            '        raise NotImplementedError, "test more args than locals"\n' \
                            '    init_locals = operands[1:(num_locals + 1)]\n' \
                            '    while len(init_locals) < num_locals:\n' \
                            '        init_locals.append(self.memory.read_word(operands[0] + (len(init_locals) << 1) + 1))\n' \
                            '    next = operands[0] + (len(init_locals) << 1) + 1\n' % self.packed_address_shift
        self.code['clear_attr'] = 'self.object_table.clear_object_attribute(operands[0], operands[1])\n'
        self.code['dec_chk'] = 'if (operands[0] == 0):\n' \
                               '    value = self.stack.pop()\n' \
                               '    value -= 1\n' \
                               '    value = value & 0xffff\n' \
                               '    self.stack.push(value)\n' \
                               'elif (operands[0] < 0x10):\n' \
                               '    value = self.stack.get_local(operands[0] - 1)\n' \
                               '    value -= 1\n' \
                               '    value = value & 0xffff\n' \
                               '    self.stack.set_local(operands[0] - 1, value)\n' \
                               'else:\n' \
                               '    value = self.memory.read_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1))\n' \
                               '    value -= 1\n' \
                               '    value = value & 0xffff\n' \
                               '    self.memory.write_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1), value)\n' \
                               'if (value & 0x8000):\n' \
                               '    value -= 0x10000\n' \
                               'if (operands[1] & 0x8000):\n' \
                               '    operands[1] -= 0x10000\n' \
                               'result = value < operands[1]\n'
        self.code['dec'] = 'if (operands[0] == 0):\n' \
                           '    value = self.stack.pop()\n' \
                           '    self.stack.push((value - 1) & 0xffff)\n' \
                           'elif (operands[0] < 0x10):\n' \
                           '    value = self.stack.get_local(operands[0] - 1)\n' \
                           '    self.stack.set_local(operands[0] - 1, (value - 1) & 0xffff)\n' \
                           'else:\n' \
                           '    value = self.memory.read_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1))\n' \
                           '    self.memory.write_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1), (value - 1) & 0xffff)\n'
        self.code['div'] = 'if (operands[0] & 0x8000):\n' \
                           '    operands[0] -= 0x10000\n' \
                           'if (operands[1] & 0x8000):\n' \
                           '    operands[1] -= 0x10000\n' \
                           'result = int(float(operands[0])/operands[1]) & 0xffff\n' # C-style integer division
        self.code['get_child'] = 'result = self.object_table.get_object_child(operands[0])\n'
        self.code['get_next_prop'] = 'result = self.object_table.get_next_property_number(operands[0], operands[1])\n'
        self.code['get_parent'] = 'result = self.object_table.get_object_parent(operands[0])\n'
        self.code['get_prop'] = 'result = self.object_table.get_property_data(operands[0], operands[1])\n'
        self.code['get_prop_addr'] = 'result = self.object_table.get_property_data_addr(operands[0], operands[1])\n'
        self.code['get_prop_len'] = 'result = self.object_table.get_property_info_backwards(operands[0])[1]\n'
        self.code['get_sibling'] = 'result = self.object_table.get_object_sibling(operands[0])\n'
        self.code['inc'] = 'if (operands[0] == 0):\n' \
                           '    value = self.stack.pop()\n' \
                           '    self.stack.push((value + 1) & 0xffff)\n' \
                           'elif (operands[0] < 0x10):\n' \
                           '    value = self.stack.get_local(operands[0] - 1)\n' \
                           '    self.stack.set_local(operands[0] - 1, (value + 1) & 0xffff)\n' \
                           'else:\n' \
                           '    value = self.memory.read_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1))\n' \
                           '    self.memory.write_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1), (value + 1) & 0xffff)\n'
        self.code['inc_chk'] = 'if (operands[0] == 0):\n' \
                               '    value = self.stack.pop()\n' \
                               '    value += 1\n' \
                               '    value = value & 0xffff\n' \
                               '    self.stack.push(value)\n' \
                               'elif (operands[0] < 0x10):\n' \
                               '    value = self.stack.get_local(operands[0] - 1)\n' \
                               '    value += 1\n' \
                               '    value = value & 0xffff\n' \
                               '    self.stack.set_local(operands[0] - 1, value)\n' \
                               'else:\n' \
                               '    value = self.memory.read_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1))\n' \
                               '    value += 1\n' \
                               '    value = value & 0xffff\n' \
                               '    self.memory.write_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1), value)\n' \
                               'if (value & 0x8000):\n' \
                               '    value -= 0x10000\n' \
                               'if (operands[1] & 0x8000):\n' \
                               '    operands[1] -= 0x10000\n' \
                               'result = value > operands[1]\n'
        self.code['insert_obj'] = 'self.object_table.unlink_object(operands[0])\n' \
                                  'self.object_table.set_object_parent(operands[0], operands[1])\n' \
                                  'sibling = self.object_table.get_object_child(operands[1])\n' \
                                  'self.object_table.set_object_child(operands[1], operands[0])\n' \
                                  'self.object_table.set_object_sibling(operands[0], sibling)\n'
        self.code['je'] = 'result = False\n' \
                          'for operand in operands[1:]:\n' \
                          '    if (operand == operands[0]):\n' \
                          '        result = True\n' \
                          '        break\n'
        self.code['jg'] = 'if (operands[0] & 0x8000):\n' \
                          '    operands[0] -= 0x10000\n' \
                          'if (operands[1] & 0x8000):\n' \
                          '    operands[1] -= 0x10000\n' \
                          'result = (operands[0] > operands[1])\n'
        self.code['jin'] = 'result = self.object_table.get_object_parent(operands[0]) == operands[1]\n'
        self.code['jl'] = 'if (operands[0] & 0x8000):\n' \
                          '    operands[0] -= 0x10000\n' \
                          'if (operands[1] & 0x8000):\n' \
                          '    operands[1] -= 0x10000\n' \
                          'result = (operands[0] < operands[1])\n'
        self.code['jump'] = 'next = (%d + operands[0] - 2) & 0xffff\n'
        self.code['jz'] = 'result = (operands[0] == 0)\n'
        self.code['load'] = 'if (operands[0] == 0):\n' \
                            '    result = self.stack.peek()\n' \
                            'elif (operands[0] < 0x10):\n' \
                            '    result = self.stack.get_local(operands[0] - 1)\n' \
                            'else:\n' \
                            '    result = self.memory.read_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1))\n'
        self.code['loadb'] = 'result = self.memory.read_byte(operands[0] + operands[1])\n'
        self.code['loadw'] = 'result = self.memory.read_word(operands[0] + (operands[1] << 1))\n'
        self.code['mod'] = 'if (operands[0] & 0x8000):\n' \
                           '    operands[0] -= 0x10000\n' \
                           'if (operands[1] & 0x8000):\n' \
                           '    operands[1] -= 0x10000\n' \
                           'result = (operands[0] - operands[1] * int(float(operands[0])/operands[1])) & 0xffff\n' # C-style integer division
        self.code['mul'] = 'result = (operands[0] * operands[1]) & 0xffff\n'
        self.code['new_line'] = 'self.output.write("\\n")\n'
        self.code['nop'] = '# NOP\n'
        self.code['not'] = 'result = (~operands[0]) & 0xffff\n'
        self.code['or'] = 'result = operands[0] | operands[1]\n'
        self.code['pop'] = 'self.stack.pop()\n'
        self.code['print'] = 'self.output.write("%s")\n'
        self.code['print_addr'] = 'self.output.write(self.memory.decode_string(operands[0], "\\n")[0])\n'
        self.code['print_char'] = 'self.output.write(self.memory.decode_zscii(operands[0]))\n'
        self.code['print_num'] = 'if (operands[0] & 0x8000):\n' \
                                 '    operands[0] -= 0x10000\n' \
                                 'self.output.write(str(operands[0]))\n'
        self.code['print_obj'] = 'self.output.write(self.object_table.get_object_short_name(operands[0]))\n'
        self.code['print_paddr'] = 'self.output.write(self.memory.decode_string(operands[0] << %d, "\\n")[0])\n' % self.packed_address_shift
        self.code['print_ret'] = 'self.output.write("%s\\n")\n' \
                                 'result = 1\n'
        self.code['pull'] = 'result = self.stack.pop()\n' \
                            'if (operands[0] == 0):\n' \
                            '    self.stack.push(result)\n' \
                            'elif (operands[0] < 0x10):\n' \
                            '    self.stack.set_local(operands[0] - 1, result)\n' \
                            'else:\n' \
                            '    self.memory.write_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1), result)\n'
        self.code['push'] = 'self.stack.push(operands[0])\n'
        self.code['put_prop'] = 'self.object_table.set_property_data(operands[0], operands[1], operands[2])\n'
        self.code['quit'] = 'self.halt()\n'
        self.code['random'] = 'if (operands[0] & 0x8000):\n' \
                              '    operands[0] -= 0x10000\n' \
                              'if (operands[0] > 0):\n' \
                              '    result = random.randint(1, operands[0])\n' \
                              '    result = 1\n' \
                              'else:\n' \
                              '    if (operands[0] < 0):\n' \
                              '        random.seed(operands[0])\n' \
                              '    else:\n' \
                              '        random.seed(None)\n' \
                              '    result = 0\n'
        self.code['remove_obj'] = 'self.object_table.unlink_object(operands[0])\n'
        self.code['restart'] = 'raise NotImplementedError, "restart"\n'
        self.code['restore'] = 'raise NotImplementedError, "restore"\n'
        self.code['ret'] = 'result = operands[0]\n'
        self.code['ret_popped'] = 'result = self.stack.pop()\n'
        self.code['rfalse'] = 'result = 0\n'
        self.code['rtrue'] = 'result = 1\n'
        self.code['save'] = 'filename = "test.sav"\n' \
                            'self.memory.uncompress(self.memory.compress())\n' \
                            'self.stack.print_all()\n' \
                            'new_stack = self.stack.__class__.deserialize(self.stack.serialize())\n' \
                            'new_stack.print_all()\n' \
                            '\n' \
                            'raise NotImplementedError, "save"\n'
        self.code['set_attr'] = 'self.object_table.set_object_attribute(operands[0], operands[1])\n'
        self.code['sread'] = 'room = self.object_table.get_object_short_name(self.memory.read_word(self.header.get_globals_table_location()))\n' \
                             'score = self.memory.read_word(self.header.get_globals_table_location() + 2)\n' \
                             'turns = self.memory.read_word(self.header.get_globals_table_location() + 4)\n' \
                             'self.output.redraw_status(room, score, turns)\n' \
                             'max_length = self.memory.read_byte(operands[0])\n' \
                             'input = self.input.read()\n' \
                             'self.output.write(input, True)\n' \
                             'input = input[:-1]\n' \
                             'chars = list(input[:max_length].lower())\n' \
                             'pos = 1\n' \
                             'for char in chars:\n' \
                             '    self.memory.write_byte(operands[0] + pos, ord(char))\n' \
                             '    pos += 1\n' \
                             'self.memory.write_byte(operands[0] + pos, 0)\n' \
                             'self.memory.tokenize(operands[0], operands[1])\n'
        self.code['store'] = 'if (operands[0] == 0):\n' \
                             '    self.stack.pop()\n' \
                             '    self.stack.push(operands[1])\n' \
                             'elif (operands[0] < 0x10):\n' \
                             '    self.stack.set_local(operands[0] - 1, operands[1])\n' \
                             'else:\n' \
                             '    self.memory.write_word(self.header.get_globals_table_location() + ((operands[0] - 0x10) << 1), operands[1])\n'
        self.code['storeb'] = 'self.memory.write_byte(operands[0] + operands[1], operands[2])\n'
        self.code['storew'] = 'self.memory.write_word(operands[0] + (operands[1] << 1), operands[2])\n'
        self.code['sub'] = 'result = (operands[0] - operands[1]) & 0xffff\n'
        self.code['test'] = 'result = (operands[0] & operands[1] == operands[1])\n'
        self.code['test_attr'] = 'result = self.object_table.get_object_attribute(operands[0], operands[1])\n'
    
    def decode_branching(self, address):
        byte1 = self.memory.read_byte(address)
        bytes = 1
        
        if (byte1 & 0x80):
            condition = True
        else:
            condition = False
            
        if (byte1 & 0x40):
            offset = byte1 & 0x3f
        else:
            byte2 = self.memory.read_byte(address + 1)
            bytes = 2
            offset = ((byte1 & 0x3f) << 8) + byte2
            if (offset & 0x2000):
                offset -= 0x4000
        return (condition, offset, bytes)
    
    def decode_variable_operator(self, operator, address):
        operand_types = self.memory.read_byte(address + 1)
        operand_types_list = []
        operand_types_list.append((operand_types & 0xc0) >> 6)
        operand_types_list.append((operand_types & 0x30) >> 4)
        operand_types_list.append((operand_types & 0x0c) >> 2)
        operand_types_list.append(operand_types & 0x03)
        return self.decode_variable_operands(operator, address + 2, operand_types_list, 4)
    
    def decode_variable_operands(self, operator, first_operand_address, operand_types, max_operand_count):
        address = first_operand_address
        for operand_type in operand_types:
            if (operand_type == 0x0):  # large constant
                operator.load_constant(self.memory.read_word(address))
                address += 2                    
            elif (operand_type == 0x1): # small constant
                operator.load_constant(self.memory.read_byte(address))
                address += 1
            elif (operand_type == 0x2): # variable
                operator.load_variable(self.memory.read_byte(address))
                address += 1
                
        return address
       
    def decode_instruction(self, address):
        type = self.memory.read_byte(address)
        if (type < 0x20):
            # long      2OP     small constant, small constant
            opcode = type & 0x1F
            name = self.names['2OP'][opcode]
            operator = Operator(address, name, self.code[name])
            operator.load_constant(self.memory.read_byte(address + 1))
            operator.load_constant(self.memory.read_byte(address + 2))
            address += 3
        elif (type < 0x40):
            # long      2OP     small constant, variable
            opcode = type & 0x1F
            name = self.names['2OP'][opcode]
            operator = Operator(address, name, self.code[name])
            operator.load_constant(self.memory.read_byte(address + 1))
            operator.load_variable(self.memory.read_byte(address + 2))
            address += 3
        elif (type < 0x60):
            # long      2OP     variable, small constant
            opcode = type & 0x1F
            name = self.names['2OP'][opcode]
            operator = Operator(address, name, self.code[name])
            operator.load_variable(self.memory.read_byte(address + 1))
            operator.load_constant(self.memory.read_byte(address + 2))
            address += 3
        elif (type < 0x80):
            # long      2OP     variable, variable
            opcode = type & 0x1F
            name = self.names['2OP'][opcode]
            operator = Operator(address, name, self.code[name])
            operator.load_variable(self.memory.read_byte(address + 1))
            operator.load_variable(self.memory.read_byte(address + 2))
            address += 3
        elif (type < 0x90):
            # short     1OP     large constant
            opcode = type & 0xF
            name = self.names['1OP'][opcode]
            if (name == 'jump'):
                operator = Operator(address, name, self.code[name] % (address + 3))
            else:
                operator = Operator(address, name, self.code[name])
            operator.load_constant(self.memory.read_word(address + 1))
            address += 3
        elif (type < 0xA0):
            # short     1OP     small constant
            opcode = type & 0xF
            name = self.names['1OP'][opcode]
            if (name == 'jump'):
                raise NotImplementedError, "'jump' with small constant offset"
            operator = Operator(address, name, self.code[name])
            operator.load_constant(self.memory.read_byte(address + 1))
            address += 2
        elif (type < 0xB0):
            # short     1OP     variable
            opcode = type & 0xF
            name = self.names['1OP'][opcode]
            if (name == 'jump'):
                operator = Operator(address, name, self.code[name] % (address + 2))
            else:
                operator = Operator(address, name, self.code[name])
            operator.load_variable(self.memory.read_byte(address + 1))
            address += 2
        elif (type < 0xC0):
            # short     0OP
            opcode = type & 0xF
            name = self.names['0OP'][opcode]
            if name in ['print', 'print_ret']:
                # these operators are followed by literal z-encoded strings
                # they have neither the 'store' nor the 'branch' effect, so it's ok to decode the string here
                # decode z-string
                string, new_address = self.memory.decode_string(address + 1, '\\n')
                #try:
                operator = Operator(address, name, self.code[name] % string) #TODO: escape double-quotes in string
                #except TypeError:
                #    print '@@', string, hex(address), hex(new_address)
                address = new_address
            else:
                operator = Operator(address, name, self.code[name])
                address += 1
        elif (type < 0xE0):
            # variable  2OP     (operand types in next byte)
            opcode = type & 0x1F
            name = self.names['2OP'][opcode]
            operator = Operator(address, name, self.code[name])
            address = self.decode_variable_operator(operator, address)
        else:
            # variable  VAR     (operand types in next byte(s))
            opcode = type & 0x1F
            name = self.names['VAR'][opcode]
            operator = Operator(address, name, self.code[name])
            address = self.decode_variable_operator(operator, address)
        
        if name in self.effects['store']:
            operator.store_variable(self.memory.read_byte(address))
            address += 1
        
        if name in self.effects['branch']:
            (condition, offset, bytes) = self.decode_branching(address)
            address += bytes
            operator.next(address, (condition, offset))       
        else:
            operator.next(address, None)
        
        if name in self.effects['call']:
            operator.do_call()
        
        if name in self.effects['return']:
            operator.do_return()
        
        return operator
    
    def decode_routine(self, address):
        # (locals, start)
        pass

