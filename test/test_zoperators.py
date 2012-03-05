import unittest

import chatmachine.vm.memory
import chatmachine.vm.stack
import chatmachine.vm.streams
import chatmachine.vm.processor


class MockOutputStreamV1(chatmachine.vm.streams.OutputStream):
    def write(self, string):
        self.string = string


class TestOperatorV1(unittest.TestCase):
    def setUp(self):
        self.memory = chatmachine.vm.memory.MemoryV1('data/zork1-5.z5')
        self.stack = chatmachine.vm.stack.Stack()
        self.input = chatmachine.vm.streams.KeyboardInputStreamV1()
        self.output = MockOutputStreamV1()

        self.processor = chatmachine.vm.processor.ProcessorV1(self.memory, self.stack, self.input, self.output)
        
    def test_add_both_positive_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 1000 - 0xb4)
        self.stack.locals.append([42 ,42 ,42])
        
        instruction = self.processor.decoder.decode_instruction(0x4725)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4725)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next, 0x4729)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.locals[-1][2], 1000)
        
    def test_add_both_positive_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0x8000 - 0xb4 + 0xa0)
        self.stack.locals.append([42 ,42 ,42])
        
        instruction = self.processor.decoder.decode_instruction(0x4725)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4725)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next, 0x4729)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.locals[-1][2], 0x80a0)
        
    def test_add_first_negative_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xffff - 0xb4)
        self.stack.locals.append([42 ,42 ,42])
        
        instruction = self.processor.decoder.decode_instruction(0x4725)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4725)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next, 0x4729)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.locals[-1][2], 0xffff)
        
    def test_add_first_negative_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xffff)
        self.stack.locals.append([42 ,42 ,42])
        
        instruction = self.processor.decoder.decode_instruction(0x4725)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4725)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next, 0x4729)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.locals[-1][2], 0xb3)
        
    def test_add_second_negative_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xb4)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xffff - 0xb4)
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4729)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4729)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next, 0x472d)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.locals[-1][3], 0xffff)
        
    def test_add_second_negative_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xb4)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xffff - 0xb3)
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4729)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4729)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next, 0x472d)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.locals[-1][3], 0)
        
    def test_add_both_negative_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xfffe)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xffff)
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4729)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4729)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next, 0x472d)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.locals[-1][3], 0xfffd)
        
    def test_add_both_negative_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0x8000)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xffff)
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4729)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4729)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next, 0x472d)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.locals[-1][3], 0x7fff)
        
    def test_and(self):
        self.stack.push(0xff00)
        instruction = self.processor.decoder.decode_instruction(0x63a2)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63a2)
        self.assertEqual(instruction.name, 'and')
        self.assertEqual(instruction.next, 0x63a8)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.pop(), 0x700)
        
    def test_call_less_arguments_than_locals(self):
        instruction = self.processor.decoder.decode_instruction(0x47ad)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x47ad)
        self.assertEqual(instruction.name, 'call')
        self.assertEqual(next, 0x470d)
        self.assertEqual(len(self.stack.locals[-1]), 3)
        init_locals = [0x2cd0, 0xffff, 0]
        for actual, desired in zip(self.stack.locals[-1], init_locals):
            self.assertEqual(actual, desired)
        return_address, result_variable, arg_count = self.stack.pop_call()
        self.assertEqual(return_address, 0x47b6)
        self.assertEqual(result_variable, 0)
        self.assertEqual(arg_count, 2)
        
    def test_call_arguments_match_locals(self):
        self.stack.stack.append([0x855a >> 1])
        instruction = self.processor.decoder.decode_instruction(0x5f0f)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f0f)
        self.assertEqual(instruction.name, 'call')
        self.assertEqual(next, 0x855d)
        self.assertEqual(len(self.stack.locals[-1]), 1)
        init_locals = [3]
        for actual, desired in zip(self.stack.locals[-1], init_locals):
            self.assertEqual(actual, desired)
        return_address, result_variable, arg_count = self.stack.pop_call()
        self.assertEqual(return_address, 0x5f14)
        self.assertEqual(result_variable, 0)
        self.assertEqual(arg_count, 1)
        
    def test_call_more_arguments_than_locals(self):
        self.fail() #0x4a04, 0x4a56, -> 0x57f4
        
    def test_clear_attr(self):
        self.fail()

    def test_dec_chk_stack(self):
        self.fail()
        
    def test_dec_chk_local(self):
        self.fail()
        
    def test_dec_chk_global(self):
        self.fail()
        
    def test_div_both_positive(self):
        self.fail()
        
    def test_div_first_negative(self):
        self.fail()
        
    def test_div_second_negative(self):
        self.fail()
        
    def test_div_both_negative(self):
        self.fail()
        
    def test_get_child(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        instruction = self.processor.decoder.decode_instruction(0x5f2c)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f2c)
        self.assertEqual(instruction.name, 'get_child')
        self.assertEqual(instruction.next, 0x5f30)
        self.assertEqual(next, 0x5f30)
        self.assertEqual(self.stack.pop(), 252)
        
    def test_get_parent(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x26 << 1), 252)
        instruction = self.processor.decoder.decode_instruction(0x5eeb)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5eeb)
        self.assertEqual(instruction.name, 'get_parent')
        self.assertEqual(instruction.next, 0x5eee)
        self.assertEqual(self.stack.pop(), 35)
        self.assertEqual(next, None)
    
    def test_get_prop_default(self):
        self.stack.locals[-1] = [42, 42, 42]
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        self.memory.write_word(0x54, 0xffff)
        instruction = self.processor.decoder.decode_instruction(0x5f1a)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f1a)
        self.assertEqual(instruction.name, 'get_prop')
        self.assertEqual(instruction.next, 0x5f1e)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.get_local(2), 0xffff)
        
    def test_get_prop_value(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        instruction = self.processor.decoder.decode_instruction(0x5f0b)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f0b)
        self.assertEqual(instruction.name, 'get_prop')
        self.assertEqual(instruction.next, 0x5f0f)
        self.assertEqual(next, None)
        self.assertEqual(self.stack.pop(), 0x42ad)
        
    def test_get_prop_addr_existing(self):
        self.fail()
            
    def test_get_prop_addr_missing(self):
        self.fail()
            
    def test_get_prop_len(self):
        self.fail()
            
    def test_get_sibling(self):
        self.stack.locals[-1] = [42, 42, 42, 252]
        instruction = self.processor.decoder.decode_instruction(0x6057)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6057)
        self.assertEqual(instruction.name, 'get_sibling')
        self.assertEqual(instruction.next, 0x605b)
        self.assertEqual(self.stack.get_local(3), 199)
        self.assertEqual(next, 0x605b)
        
    def test_inc_stack(self):
        self.fail()
        
    def test_inc_local(self):
        self.fail()
        
    def test_inc_global(self):
        self.fail()
        
    def test_inc_chk_stack(self):
        self.fail()
        
    def test_inc_chk_local_true(self):
        self.stack.locals.append([999])
        
        instruction = self.processor.decoder.decode_instruction(0x63ba)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63ba)
        self.assertEqual(instruction.name, 'inc_chk')
        self.assertEqual(instruction.next, 0x63be)
        self.assertEqual(self.stack.get_local(0), 1000)
        self.assertEqual(next, 0x63be)
        
    def test_inc_chk_global(self):
        self.fail()
        
    def test_insert_obj_first_child(self):
        self.fail()
        
    def test_insert_obj_third_child(self):
        self.fail()
        
    def test_je_false_on_false(self):
        self.stack.locals.append([42 ,42 ,0, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x472d)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x472d)
        self.assertEqual(instruction.name, 'je')
        self.assertEqual(instruction.next, 0x4731)
        self.assertEqual(next, 0x4747)
        
    def test_je_true_on_false(self):
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x472d)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x472d)
        self.assertEqual(instruction.name, 'je')
        self.assertEqual(instruction.next, 0x4731)
        self.assertEqual(next, 0x4731)
    
    def test_jg_both_negative(self):
        self.fail() #46d0
    
    def test_jg_both_positive(self):
        self.stack.locals.append([42 ,42 , 1, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4c95)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4c95)
        self.assertEqual(instruction.name, 'jg')
        self.assertEqual(instruction.next, 0x4c99)
        self.assertEqual(next, 0x4c99)
        
    def test_jg_positive_and_negative(self):
        self.stack.locals.append([42 ,42 , 0xffff, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4c95)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4c95)
        self.assertEqual(instruction.name, 'jg')
        self.assertEqual(instruction.next, 0x4c99)
        self.assertEqual(next, 0x4c99)
        
    def test_jin(self):
        self.stack.push_call([35], 1000, 0, 0)
        instruction = self.processor.decoder.decode_instruction(0x6113)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6113)
        self.assertEqual(instruction.name, 'jin')
        self.assertEqual(instruction.next, 0x6117)
        self.assertEqual(next, 1000)
        self.assertEqual(self.stack.pop(), 0)
        
    def test_jl_both_negative(self):
        self.fail()
            
    def test_jl_both_positive(self):
        self.fail()
            
    def test_jl_positive_and_negative(self):
        self.fail()
            
    def test_jump_positive_offset(self):
        self.fail()
            
    def test_jump_negative_offset(self):
        instruction = self.processor.decoder.decode_instruction(0x4755)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4755)
        self.assertEqual(instruction.name, 'jump')
        self.assertEqual(instruction.next, 0x4758)
        self.assertEqual(next, 0x472d)
        
    def test_jz_false_on_true(self):
        self.stack.locals.append([42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4735)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4735)
        self.assertEqual(instruction.name, 'jz')
        self.assertEqual(instruction.next, 0x4738)
        self.assertEqual(next, 0x4738)
        
    def test_jz_true_on_true(self):
        self.stack.locals.append([42, 0])
        
        instruction = self.processor.decoder.decode_instruction(0x4735)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4735)
        self.assertEqual(instruction.name, 'jz')
        self.assertEqual(instruction.next, 0x4738)
        self.assertEqual(next, 0x473c)

    def test_loadb_stack(self):
        self.stack.locals.append([42])
        self.memory.write_byte(42, 100)
        
        instruction = self.processor.decoder.decode_instruction(0x63c1)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63c1)
        self.assertEqual(instruction.name, 'loadb')
        self.assertEqual(instruction.next, 0x63c5)
        self.assertEqual(self.stack.pop(), 100)
        
    def test_loadb_local(self):
        self.stack.locals.append([38, 42, 42, 42, 42])
        self.memory.write_byte(42, 100)
        
        instruction = self.processor.decoder.decode_instruction(0x4c8d)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4c8d)
        self.assertEqual(instruction.name, 'loadb')
        self.assertEqual(instruction.next, 0x4c91)
        self.assertEqual(self.stack.get_local(4), 100)
        
    def test_loadb_global(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x34 << 1), 41)
        self.memory.write_byte(42, 100)
        
        instruction = self.processor.decoder.decode_instruction(0x4aa0)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4aa0)
        self.assertEqual(instruction.name, 'loadb')
        self.assertEqual(instruction.next, 0x4aa4)
        self.assertEqual(self.memory.read_word(self.processor.header.get_globals_table_location() + (0x0b << 1)), 100)
        
    def test_loadw_stack(self):
        self.stack.locals.append([42, 42, 42, 96])
        self.memory.write_word(96 + 2 * 2, 1000)
        
        instruction = self.processor.decoder.decode_instruction(0x4747)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4747)
        self.assertEqual(instruction.name, 'loadw')
        self.assertEqual(instruction.next, 0x474b)
        self.assertEqual(self.stack.pop(), 1000)
        
    def test_loadw_local(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x34 << 1), 42)
        self.stack.locals.append([0, 42])
        self.memory.write_word(42, 1000)
        
        instruction = self.processor.decoder.decode_instruction(0x4ac4)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4ac4)
        self.assertEqual(instruction.name, 'loadw')
        self.assertEqual(instruction.next, 0x4ac8)
        self.assertEqual(self.stack.get_local(1), 1000)
    
    def test_mul_both_negative(self):
        self.fail()
        
    def test_mul_both_positive_with_overflow(self):
        self.fail()
        
    def test_mul_positive_and_negative(self):
        self.fail()
        
    def test_new_line(self):
        instruction = self.processor.decoder.decode_instruction(0x63cb)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63cb)
        self.assertEqual(instruction.name, 'new_line')
        self.assertEqual(instruction.next, 0x63cc)
        self.assertEqual(next, None)
        string = '\n'
        self.assertEqual(self.output.string, string)
        
    def test_print(self):
        instruction = self.processor.decoder.decode_instruction(0x6329)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6329)
        self.assertEqual(instruction.name, 'print')
        self.assertEqual(instruction.next, 0x639e)
        self.assertEqual(next, None)
        string = 'ZORK: The Great Underground Empire - Part I\nCopyright (c) 1980 by Infocom, Inc. All rights reserved.\nZORK is a trademark of Infocom, Inc.\nRelease '
        self.assertEqual(self.output.string, string)
        
    def test_print_char(self):
        self.stack.push(65)
        instruction = self.processor.decoder.decode_instruction(0x63c5)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63c5)
        self.assertEqual(instruction.name, 'print_char')
        self.assertEqual(instruction.next, 0x63c8)
        self.assertEqual(next, None)
        string = 'A'
        self.assertEqual(self.output.string, string)
        
    def test_print_num(self):
        self.stack.push(42)
        instruction = self.processor.decoder.decode_instruction(0x63a8)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63a8)
        self.assertEqual(instruction.name, 'print_num')
        self.assertEqual(instruction.next, 0x63ab)
        self.assertEqual(next, None)
        string = str(42)
        self.assertEqual(self.output.string, string)
    
    def test_print_num_negative(self):
        self.stack.push(0xffff)
        instruction = self.processor.decoder.decode_instruction(0x63a8)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63a8)
        self.assertEqual(instruction.name, 'print_num')
        self.assertEqual(instruction.next, 0x63ab)
        self.assertEqual(next, None)
        string = str(-1)
        self.assertEqual(self.output.string, string)
    
    def test_print_obj(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        instruction = self.processor.decoder.decode_instruction(0x5ee2)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5ee2)
        self.assertEqual(instruction.name, 'print_obj')
        self.assertEqual(instruction.next, 0x5ee4)
        self.assertEqual(next, None)
        string = 'West of House'
        self.assertEqual(self.output.string, string)
    
    def test_print_addr(self):
        self.fail()
            
    def test_print_paddr(self):
        self.stack.locals[-1] = [42, 42, 42, 0xf490 >> 1]
        instruction = self.processor.decoder.decode_instruction(0x5f82)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f82)
        self.assertEqual(instruction.name, 'print_paddr')
        self.assertEqual(instruction.next, 0x5f84)
        self.assertEqual(next, None)
        string = 'There is a small mailbox here.'
        self.assertEqual(self.output.string, string)
        
    def test_pull(self):
        self.stack.locals[-1] = [42, 42]
        self.stack.push(1000)
        instruction = self.processor.decoder.decode_instruction(0x5ea3)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x5ea3)
        self.assertEqual(instruction.name, 'pull')
        self.assertEqual(instruction.next, 0x5ea6)
        result = self.stack.get_local(1)
        self.assertEqual(result, 1000)
        
    def test_push(self):
        self.stack.locals[-1] = [1000]
        instruction = self.processor.decoder.decode_instruction(0x5e9a)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x5e9a)
        self.assertEqual(instruction.name, 'push')
        self.assertEqual(instruction.next, 0x5e9d)
        result = self.stack.pop()
        self.assertEqual(result, 1000)
        
    def test_put_prop_size_1(self):
        self.fail()
        
    def test_put_prop_size_2(self):
        self.memory.write_word(0x0c76, 0xffff)

        instruction = self.processor.decoder.decode_instruction(0x47e2)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x47e2)
        self.assertEqual(instruction.name, 'put_prop')
        self.assertEqual(instruction.next, 0x47e7)
        result = self.memory.read_word(0x0c76)
        self.assertEqual(result, 0x001f)
        
    def test_ret_none(self):
        self.stack.push_call([42, 42, 42, 42, 1000], 1000, None, 2)
        
        instruction = self.processor.decoder.decode_instruction(0x4745)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x4745)
        self.assertEqual(instruction.name, 'ret')
        self.assertEqual(instruction.next, 0x4747)
        self.assertEqual(next, 1000)
        
    def test_ret_stack(self):
        self.stack.push_call([42, 42, 42, 42, 1000], 1000, 0, 2)
        
        instruction = self.processor.decoder.decode_instruction(0x4745)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x4745)
        self.assertEqual(instruction.name, 'ret')
        self.assertEqual(instruction.next, 0x4747)
        self.assertEqual(next, 1000)
        self.assertEqual(self.stack.pop(), 1000)
        
    def test_ret_local(self):
        self.stack.locals[-1] = [42]
        self.stack.push_call([42, 42, 42, 42, 1000], 1000, 1, 2)
        
        instruction = self.processor.decoder.decode_instruction(0x4745)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x4745)
        self.assertEqual(instruction.name, 'ret')
        self.assertEqual(instruction.next, 0x4747)
        self.assertEqual(next, 1000)
        self.assertEqual(self.stack.get_local(0), 1000)
        
    def test_ret_global(self):
        self.stack.push_call([42, 42, 42, 42, 1000], 1000, 0x10, 2)
        
        instruction = self.processor.decoder.decode_instruction(0x4745)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x4745)
        self.assertEqual(instruction.name, 'ret')
        self.assertEqual(instruction.next, 0x4747)
        self.assertEqual(next, 1000)
        result = self.memory.read_word(self.processor.header.get_globals_table_location())
        self.assertEqual(result, 1000)
        
    def test_ret_popped(self):
        self.stack.push_call([], 1000, 0, 42)
        self.stack.push(42)
        instruction = self.processor.decoder.decode_instruction(0x5f48)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f48)
        self.assertEqual(instruction.name, 'ret_popped')
        self.assertEqual(instruction.next, 0x5f49)
        self.assertEqual(next, 1000)
        self.assertEqual(self.stack.pop(), 42)
        
    def test_rfalse(self):
        self.stack.push_call([], 1000, 0, 42)
        instruction = self.processor.decoder.decode_instruction(0x7967)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x7967)
        self.assertEqual(instruction.name, 'rfalse')
        self.assertEqual(instruction.next, 0x7968)
        self.assertEqual(next, 1000)
        self.assertEqual(self.stack.pop(), 0)
        
    def test_rtrue(self):
        self.stack.push_call([], 1000, 0, 42)
        
        instruction = self.processor.decoder.decode_instruction(0x63cc)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x63cc)
        self.assertEqual(instruction.name, 'rtrue')
        self.assertEqual(instruction.next, 0x63cd)
        self.assertEqual(next, 1000)
        self.assertEqual(self.stack.pop(), 1)
        
    def test_set_attr(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
    
        instruction = self.processor.decoder.decode_instruction(0x5edc)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5edc)
        self.assertEqual(instruction.name, 'set_attr')
        self.assertEqual(instruction.next, 0x5edf)
        self.assertEqual(next, None)
        result = self.processor.object_table.get_object_attribute(35, 0x1c)
        self.assertTrue(result)
        
    def test_sread(self):
        self.fail()
        
    def test_store_stack(self):
        self.fail()
        
    def test_store_local(self):
        self.stack.locals[-1] = [42, 42]
        instruction = self.processor.decoder.decode_instruction(0x5edf)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5edf)
        self.assertEqual(instruction.name, 'store')
        self.assertEqual(instruction.next, 0x5ee2)
        self.assertEqual(next, None)
        result = self.stack.get_local(1)
        self.assertEqual(result, 1)
        
    def test_store_global(self):
        instruction = self.processor.decoder.decode_instruction(0x481d)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x481d)
        self.assertEqual(instruction.name, 'store')
        self.assertEqual(instruction.next, 0x4820)
        self.assertEqual(next, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location())
        self.assertEqual(result, 0x23)
    
    def test_storeb(self):
        self.fail()
        
    def test_storew(self):
        self.stack.locals[-1] = [1000, 42, 42, 42, 46]
        self.memory.write_word(50, 42)
        
        instruction = self.processor.decoder.decode_instruction(0x4740)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4740)
        self.assertEqual(instruction.name, 'storew')
        self.assertEqual(instruction.next, 0x4745)
        self.assertEqual(next, None)
        result = self.memory.read_word(50)
        self.assertEqual(result, 1000)
        
    def test_sub_both_positive_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 1000 + 0x6)
        
        instruction = self.processor.decoder.decode_instruction(0x4731)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4731)
        self.assertEqual(instruction.name, 'sub')
        self.assertEqual(instruction.next, 0x4735)
        self.assertEqual(next, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location() + (0x62 << 1))
        self.assertEqual(result, 1000)
        
    def test_sub_both_positive_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0x5)
        
        instruction = self.processor.decoder.decode_instruction(0x4731)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4731)
        self.assertEqual(instruction.name, 'sub')
        self.assertEqual(instruction.next, 0x4735)
        self.assertEqual(next, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location() + (0x62 << 1))
        self.assertEqual(result, 0xffff)
        
    def test_sub_first_negative_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xfff6)
        
        instruction = self.processor.decoder.decode_instruction(0x4731)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4731)
        self.assertEqual(instruction.name, 'sub')
        self.assertEqual(instruction.next, 0x4735)
        self.assertEqual(next, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location() + (0x62 << 1))
        self.assertEqual(result, 0xfff0)
        
    def test_sub_first_negative_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0x8005)
        
        instruction = self.processor.decoder.decode_instruction(0x4731)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4731)
        self.assertEqual(instruction.name, 'sub')
        self.assertEqual(instruction.next, 0x4735)
        self.assertEqual(next, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location() + (0x62 << 1))
        self.assertEqual(result, 0x7fff)
        
    def test_sub_second_negative_no_overflow(self):
        self.fail() #0x4ff1
        
    def test_sub_second_negative_with_overflow(self):
        self.fail()  #0x4ff1
        
    def test_sub_both_negative_no_overflow(self):
        self.fail() #0x5590
        
    def test_sub_both_negative_with_overflow(self):
        self.fail()  #0x5590
        
    def test_test_attr_false(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        instruction = self.processor.decoder.decode_instruction(0x4826)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4826)
        self.assertEqual(instruction.name, 'test_attr')
        self.assertEqual(instruction.next, 0x482a)
        self.assertEqual(next, 0x482a)
    
    def test_test_attr_true(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        self.processor.object_table.set_object_attribute(35, 0x1c)
        instruction = self.processor.decoder.decode_instruction(0x4826)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4826)
        self.assertEqual(instruction.name, 'test_attr')
        self.assertEqual(instruction.next, 0x482a)
        self.assertEqual(next, 0x4830)     

class TestDecoderV1(unittest.TestCase):
    def setUp(self):
        self.memory = chatmachine.vm.memory.MemoryV1('data/zork1-5.z5')
        self.stack = chatmachine.vm.stack.Stack()
        self.input = chatmachine.vm.streams.KeyboardInputStreamV1()
        self.output = chatmachine.vm.streams.ScreenOutputStreamV1()

        self.processor = chatmachine.vm.processor.ProcessorV1(self.memory, self.stack, self.input, self.output)
        
    def test_decode_calling(self):
        instruction = self.processor.decoder.decode_instruction(0x47ad)
        self.assertEqual(str(instruction), 'CALL 4706 (#2cd0,#ffff) -> -(SP)')

    def test_decode_storing(self):
        instruction = self.processor.decoder.decode_instruction(0x47e7)
        self.assertEqual(str(instruction), 'ADD G21,#02 -> -(SP)')
        
    def test_decode_branching_one_byte(self):
        instruction = self.processor.decoder.decode_instruction(0x472d)
        self.assertEqual(str(instruction), 'JE L03,L02 [FALSE] 4747')
        
    def test_decode_branching_two_bytes_positive_offset(self):
        instruction = self.processor.decoder.decode_instruction(0x608d)
        self.assertEqual(str(instruction), 'TEST_ATTR L03,#1d [TRUE] 60d1')
        
    def test_decode_branching_two_bytes_negative_offset(self):
        self.fail() #0x56d1
    
    def test_decode_2op_sc_sc(self):
        instruction = self.processor.decoder.decode_instruction(0x481d)
        self.assertEqual(str(instruction), 'STORE #10,#23')
        
    def test_decode_2op_sc_var(self):
        instruction = self.processor.decoder.decode_instruction(0x481d)
        self.assertEqual(str(instruction), 'STORE #2d,G00')
        
    def test_decode_2op_var_sc(self):
        instruction = self.processor.decoder.decode_instruction(0x4725)
        self.assertEqual(str(instruction), 'ADD G72,#b4 -> L02')
        
    def test_decode_2op_var_var(self):
        instruction = self.processor.decoder.decode_instruction(0x4729)
        self.assertEqual(str(instruction), 'ADD G72,G62 -> L03')
        
    def test_decode_1op_lc(self):
        instruction = self.processor.decoder.decode_instruction(0x4755)
        self.assertEqual(str(instruction), 'JUMP 472d')
        
    def test_decode_1op_sc(self):
        instruction = self.processor.decoder.decode_instruction(0x4ca1)
        self.assertEqual(str(instruction), 'INC #04')
        
    def test_decode_1op_var(self):
        instruction = self.processor.decoder.decode_instruction(0x4735)
        self.assertEqual(str(instruction), 'JZ L01 [TRUE] 473c')
        
    def test_decode_0op(self):
        instruction = self.processor.decoder.decode_instruction(0x63cb)
        self.assertEqual(str(instruction), 'NEW_LINE')
             
    def test_decode_var_1(self):
        instruction = self.processor.decoder.decode_instruction(0x482a)
        self.assertEqual(str(instruction), 'CALL 6326 -> -(SP)')
        
    def test_decode_var_2(self):
        instruction = self.processor.decoder.decode_instruction(0x470d)
        self.assertEqual(str(instruction), 'CALL 471a (L00) -> L02')
        
    def test_decode_var_3(self):
        instruction = self.processor.decoder.decode_instruction(0x4740)
        self.assertEqual(str(instruction), 'STOREW L04,#02,L00')
        
    def test_decode_var_4(self):
        instruction = self.processor.decoder.decode_instruction(0x5f3f)
        self.assertEqual(str(instruction), 'CALL 5fdc (G00,L00,#ffff) -> -(SP)')
        

