import unittest

import chatmachine.memory
import chatmachine.stack
import chatmachine.streams
import chatmachine.processor


class MockOutputStreamV1(chatmachine.streams.OutputStream):
    def write(self, string):
        self.string = string


class TestOperatorV1(unittest.TestCase):
    def setUp(self):
        self.memory = chatmachine.memory.MemoryV1('data/zork1-5.z5')
        self.stack = chatmachine.stack.Stack()
        self.input = chatmachine.streams.KeyboardInputStreamV1()
        self.output = MockOutputStreamV1()

        self.processor = chatmachine.processor.ProcessorV1(self.memory, self.stack, self.input, self.output)
        
    def test_add_both_positive_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 1000 - 0xb4)
        self.stack.locals.append([42 ,42 ,42])
        
        instruction = self.processor.decoder.decode_instruction(0x4725)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4725)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next_address, 0x4729)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.locals[-1][2], 1000)
        
    def test_add_both_positive_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0x8000 - 0xb4 + 0xa0)
        self.stack.locals.append([42 ,42 ,42])
        
        instruction = self.processor.decoder.decode_instruction(0x4725)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4725)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next_address, 0x4729)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.locals[-1][2], 0x80a0)
        
    def test_add_first_negative_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xffff - 0xb4)
        self.stack.locals.append([42 ,42 ,42])
        
        instruction = self.processor.decoder.decode_instruction(0x4725)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4725)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next_address, 0x4729)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.locals[-1][2], 0xffff)
        
    def test_add_first_negative_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xffff)
        self.stack.locals.append([42 ,42 ,42])
        
        instruction = self.processor.decoder.decode_instruction(0x4725)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4725)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next_address, 0x4729)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.locals[-1][2], 0xb3)
        
    def test_add_second_negative_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xb4)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xffff - 0xb4)
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4729)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4729)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next_address, 0x472d)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.locals[-1][3], 0xffff)
        
    def test_add_second_negative_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xb4)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xffff - 0xb3)
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4729)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4729)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next_address, 0x472d)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.locals[-1][3], 0)
        
    def test_add_both_negative_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0xfffe)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xffff)
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4729)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4729)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next_address, 0x472d)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.locals[-1][3], 0xfffd)
        
    def test_add_both_negative_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x72 << 1), 0x8000)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xffff)
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4729)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4729)
        self.assertEqual(instruction.name, 'add')
        self.assertEqual(instruction.next_address, 0x472d)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.locals[-1][3], 0x7fff)
        
    def test_and(self):
        self.stack.push(0xff00)
        instruction = self.processor.decoder.decode_instruction(0x63a2)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63a2)
        self.assertEqual(instruction.name, 'and')
        self.assertEqual(instruction.next_address, 0x63a8)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.pop(), 0x700)
        
    def test_call_less_arguments_than_locals(self):
        instruction = self.processor.decoder.decode_instruction(0x47ad)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x47ad)
        self.assertEqual(instruction.name, 'call')
        self.assertEqual(next_address, 0x470d)
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
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f0f)
        self.assertEqual(instruction.name, 'call')
        self.assertEqual(next_address, 0x855d)
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
        self.assertEqual(self.memory.get_object_table().get_object_attribute(23, 0x1b), True)
        self.stack.locals.append([42 ,42 ,42, 42, 23])
        instruction = self.processor.decoder.decode_instruction(0x5a3c)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5a3c)
        self.assertEqual(instruction.name, 'clear_attr')
        self.assertEqual(instruction.next_address, 0x5a3f)
        self.assertEqual(self.memory.get_object_table().get_object_attribute(23, 0x1b), False)

    def test_dec(self):
        self.fail()
        
    def test_dec_chk_local(self):
        self.stack.locals.append([42 ,0x8000])
        instruction = self.processor.decoder.decode_instruction(0x5052)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5052)
        self.assertEqual(instruction.name, 'dec_chk')
        self.assertEqual(instruction.next_address, 0x5056)
        self.assertEqual(next_address, 0x507a)
        self.assertEqual(self.stack.get_local(1), 0x7fff)
        
    def test_dec_chk_global(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x0b << 1), 0)
        instruction = self.processor.decoder.decode_instruction(0x4abd)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4abd)
        self.assertEqual(instruction.name, 'dec_chk')
        self.assertEqual(instruction.next_address, 0x4ac1)
        self.assertEqual(next_address, 0x4ac1)
        self.assertEqual(self.memory.read_word(self.processor.header.get_globals_table_location() + (0x0b << 1)), 0xffff)
        
    def test_dec_chk_underflow(self):
        self.fail()
        
    def test_div_both_positive(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x01 << 1), 11)
        self.stack.push(2)
        instruction = self.processor.decoder.decode_instruction(0xe6e1)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0xe6e1)
        self.assertEqual(instruction.name, 'div')
        self.assertEqual(instruction.next_address, 0xe6e5)
        self.assertEqual(self.stack.pop(), 5)
        
    def test_div_first_negative(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x01 << 1), -11 & 0xffff)
        self.stack.push(2)
        instruction = self.processor.decoder.decode_instruction(0xe6e1)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0xe6e1)
        self.assertEqual(instruction.name, 'div')
        self.assertEqual(instruction.next_address, 0xe6e5)
        self.assertEqual(self.stack.pop(), -5 & 0xffff)
        
    def test_div_second_negative(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x01 << 1), 11)
        self.stack.push(-2 & 0xffff)
        instruction = self.processor.decoder.decode_instruction(0xe6e1)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0xe6e1)
        self.assertEqual(instruction.name, 'div')
        self.assertEqual(instruction.next_address, 0xe6e5)
        self.assertEqual(self.stack.pop(), -5 & 0xffff)
        
    def test_div_both_negative(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x01 << 1), -11 & 0xffff)
        self.stack.push(-2 & 0xffff)
        instruction = self.processor.decoder.decode_instruction(0xe6e1)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0xe6e1)
        self.assertEqual(instruction.name, 'div')
        self.assertEqual(instruction.next_address, 0xe6e5)
        self.assertEqual(self.stack.pop(), 5)
        
    def test_get_child(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        instruction = self.processor.decoder.decode_instruction(0x5f2c)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f2c)
        self.assertEqual(instruction.name, 'get_child')
        self.assertEqual(instruction.next_address, 0x5f30)
        self.assertEqual(next_address, 0x5f30)
        self.assertEqual(self.stack.pop(), 252)
        
    def test_get_next_prop(self):
        self.fail()
        
    def test_get_parent(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x26 << 1), 252)
        instruction = self.processor.decoder.decode_instruction(0x5eeb)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5eeb)
        self.assertEqual(instruction.name, 'get_parent')
        self.assertEqual(instruction.next_address, 0x5eee)
        self.assertEqual(self.stack.pop(), 35)
        self.assertEqual(next_address, None)
    
    def test_get_prop_default(self):
        self.stack.locals[-1] = [42, 42, 42]
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        self.memory.write_word(0x54, 0xffff)
        instruction = self.processor.decoder.decode_instruction(0x5f1a)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f1a)
        self.assertEqual(instruction.name, 'get_prop')
        self.assertEqual(instruction.next_address, 0x5f1e)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.get_local(2), 0xffff)
        
    def test_get_prop_value(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        instruction = self.processor.decoder.decode_instruction(0x5f0b)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f0b)
        self.assertEqual(instruction.name, 'get_prop')
        self.assertEqual(instruction.next_address, 0x5f0f)
        self.assertEqual(next_address, None)
        self.assertEqual(self.stack.pop(), 0x42ad)
        
    def test_get_prop_addr_existing(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x0 << 1), 252)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x42 << 1), 18)
        self.stack.locals.append([42])
        instruction = self.processor.decoder.decode_instruction(0x681f)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x681f)
        self.assertEqual(instruction.name, 'get_prop_addr')
        self.assertEqual(instruction.next_address, 0x6823)
        self.assertEqual(self.stack.get_local(0), 0x1ffa)
                    
    def test_get_prop_addr_missing(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x0 << 1), 252)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x42 << 1), 42)
        self.stack.locals.append([42])
        instruction = self.processor.decoder.decode_instruction(0x681f)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x681f)
        self.assertEqual(instruction.name, 'get_prop_addr')
        self.assertEqual(instruction.next_address, 0x6823)
        self.assertEqual(self.stack.get_local(0), 0)
            
    def test_get_prop_len(self):
        self.stack.locals.append([0x200f, 42])
        instruction = self.processor.decoder.decode_instruction(0x6827)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6827)
        self.assertEqual(instruction.name, 'get_prop_len')
        self.assertEqual(instruction.next_address, 0x682a)
        self.assertEqual(self.stack.get_local(1), 4)
            
    def test_get_sibling(self):
        self.stack.locals[-1] = [42, 42, 42, 252]
        instruction = self.processor.decoder.decode_instruction(0x6057)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6057)
        self.assertEqual(instruction.name, 'get_sibling')
        self.assertEqual(instruction.next_address, 0x605b)
        self.assertEqual(self.stack.get_local(3), 199)
        self.assertEqual(next_address, 0x605b)
        
    def test_inc_local(self):
        self.stack.locals[-1] = [42, 0xffff]
        instruction = self.processor.decoder.decode_instruction(0x6dcf)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6dcf)
        self.assertEqual(instruction.name, 'inc')
        self.assertEqual(instruction.next_address, 0x6dd1)
        self.assertEqual(self.stack.get_local(1), 0)
        
    def test_inc_global(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x02 << 1), 999)
        instruction = self.processor.decoder.decode_instruction(0x6fbf)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6fbf)
        self.assertEqual(instruction.name, 'inc')
        self.assertEqual(instruction.next_address, 0x6fc1)
        self.assertEqual(self.memory.read_word(self.processor.header.get_globals_table_location() + (0x02 << 1)), 1000)
        
    def test_inc_chk_local_true(self):
        self.stack.locals.append([999])
        instruction = self.processor.decoder.decode_instruction(0x63ba)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63ba)
        self.assertEqual(instruction.name, 'inc_chk')
        self.assertEqual(instruction.next_address, 0x63be)
        self.assertEqual(self.stack.get_local(0), 1000)
        self.assertEqual(next_address, 0x63be)
        
    def test_inc_chk_local_false(self):
        self.stack.locals.append([0x7fff])
        instruction = self.processor.decoder.decode_instruction(0x63ba)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63ba)
        self.assertEqual(instruction.name, 'inc_chk')
        self.assertEqual(instruction.next_address, 0x63be)
        self.assertEqual(self.stack.get_local(0), 0x8000)
        self.assertEqual(next_address, 0x63c1)
    
    def test_inc_chk_overflow(self):
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
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x472d)
        self.assertEqual(instruction.name, 'je')
        self.assertEqual(instruction.next_address, 0x4731)
        self.assertEqual(next_address, 0x4747)
        
    def test_je_true_on_false(self):
        self.stack.locals.append([42 ,42 ,42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x472d)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x472d)
        self.assertEqual(instruction.name, 'je')
        self.assertEqual(instruction.next_address, 0x4731)
        self.assertEqual(next_address, 0x4731)
    
    def test_jg_both_negative(self):
        self.stack.locals.append([0xfffe])
        self.stack.push(0xffff)
        instruction = self.processor.decoder.decode_instruction(0x46d0)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x46d0)
        self.assertEqual(instruction.name, 'jg')
        self.assertEqual(instruction.next_address, 0x46d4)
        self.assertEqual(next_address, 0x46d4)
    
    def test_jg_both_positive(self):
        self.stack.locals.append([42 ,42 , 1, 42])
        instruction = self.processor.decoder.decode_instruction(0x4c95)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4c95)
        self.assertEqual(instruction.name, 'jg')
        self.assertEqual(instruction.next_address, 0x4c99)
        self.assertEqual(next_address, 0x4c99)
        
    def test_jg_positive_and_negative(self):
        self.stack.locals.append([42 ,42 , 0xffff, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4c95)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4c95)
        self.assertEqual(instruction.name, 'jg')
        self.assertEqual(instruction.next_address, 0x4c99)
        self.assertEqual(next_address, 0x4c99)
        
    def test_jin(self):
        self.stack.push_call([35], 1000, 0, 0)
        instruction = self.processor.decoder.decode_instruction(0x6113)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6113)
        self.assertEqual(instruction.name, 'jin')
        self.assertEqual(instruction.next_address, 0x6117)
        self.assertEqual(next_address, 1000)
        self.assertEqual(self.stack.pop(), 0)
        
    def test_jl_both_negative(self):
        self.stack.locals.append([0xffff, 0xfffe])
        instruction = self.processor.decoder.decode_instruction(0xc653)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0xc653)
        self.assertEqual(instruction.name, 'jl')
        self.assertEqual(instruction.next_address, 0xc657)
        self.assertEqual(next_address, 0xc659)
            
    def test_jl_both_positive(self):
        self.stack.locals.append([999, 1000])
        instruction = self.processor.decoder.decode_instruction(0xc653)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0xc653)
        self.assertEqual(instruction.name, 'jl')
        self.assertEqual(instruction.next_address, 0xc657)
        self.assertEqual(next_address, 0xc657)
            
    def test_jl_positive_and_negative(self):
        self.stack.locals.append([0xffff, 1])
        instruction = self.processor.decoder.decode_instruction(0xc653)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0xc653)
        self.assertEqual(instruction.name, 'jl')
        self.assertEqual(instruction.next_address, 0xc657)
        self.assertEqual(next_address, 0xc657)
            
    def test_jump_positive_offset(self):
        instruction = self.processor.decoder.decode_instruction(0x4789)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4789)
        self.assertEqual(instruction.name, 'jump')
        self.assertEqual(instruction.next_address, 0x478c)
        self.assertEqual(next_address, 0x47a4)
            
    def test_jump_negative_offset(self):
        instruction = self.processor.decoder.decode_instruction(0x4755)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4755)
        self.assertEqual(instruction.name, 'jump')
        self.assertEqual(instruction.next_address, 0x4758)
        self.assertEqual(next_address, 0x472d)
        
    def test_jz_false_on_true(self):
        self.stack.locals.append([42, 42])
        
        instruction = self.processor.decoder.decode_instruction(0x4735)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4735)
        self.assertEqual(instruction.name, 'jz')
        self.assertEqual(instruction.next_address, 0x4738)
        self.assertEqual(next_address, 0x4738)
        
    def test_jz_true_on_true(self):
        self.stack.locals.append([42, 0])
        
        instruction = self.processor.decoder.decode_instruction(0x4735)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4735)
        self.assertEqual(instruction.name, 'jz')
        self.assertEqual(instruction.next_address, 0x4738)
        self.assertEqual(next_address, 0x473c)

    def test_loadb_stack(self):
        self.stack.locals.append([42])
        self.memory.write_byte(42, 100)
        
        instruction = self.processor.decoder.decode_instruction(0x63c1)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63c1)
        self.assertEqual(instruction.name, 'loadb')
        self.assertEqual(instruction.next_address, 0x63c5)
        self.assertEqual(self.stack.pop(), 100)
        
    def test_loadb_local(self):
        self.stack.locals.append([38, 42, 42, 42, 42])
        self.memory.write_byte(42, 100)
        
        instruction = self.processor.decoder.decode_instruction(0x4c8d)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4c8d)
        self.assertEqual(instruction.name, 'loadb')
        self.assertEqual(instruction.next_address, 0x4c91)
        self.assertEqual(self.stack.get_local(4), 100)
        
    def test_loadb_global(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x34 << 1), 41)
        self.memory.write_byte(42, 100)
        
        instruction = self.processor.decoder.decode_instruction(0x4aa0)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4aa0)
        self.assertEqual(instruction.name, 'loadb')
        self.assertEqual(instruction.next_address, 0x4aa4)
        self.assertEqual(self.memory.read_word(self.processor.header.get_globals_table_location() + (0x0b << 1)), 100)
        
    def test_loadw_stack(self):
        self.stack.locals.append([42, 42, 42, 96])
        self.memory.write_word(96 + 2 * 2, 1000)
        
        instruction = self.processor.decoder.decode_instruction(0x4747)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4747)
        self.assertEqual(instruction.name, 'loadw')
        self.assertEqual(instruction.next_address, 0x474b)
        self.assertEqual(self.stack.pop(), 1000)
        
    def test_loadw_local(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x34 << 1), 42)
        self.stack.locals.append([0, 42])
        self.memory.write_word(42, 1000)
        
        instruction = self.processor.decoder.decode_instruction(0x4ac4)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4ac4)
        self.assertEqual(instruction.name, 'loadw')
        self.assertEqual(instruction.next_address, 0x4ac8)
        self.assertEqual(self.stack.get_local(1), 1000)
            
    def test_mod(self):
        self.fail()
        
    def test_mul_both_positive(self):
        self.stack.locals.append([42, 42, 42, 42])
        self.stack.push(0x4000)
        instruction = self.processor.decoder.decode_instruction(0x4cbf)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4cbf)
        self.assertEqual(instruction.name, 'mul')
        self.assertEqual(instruction.next_address, 0x4cc3)
        self.assertEqual(self.stack.get_local(3), 0x8000)
        
    def test_mul_positive_and_negative_with_overflow(self):
        self.stack.locals.append([42, 42, 42, 42])
        self.stack.push(0xffff)
        instruction = self.processor.decoder.decode_instruction(0x4cbf)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4cbf)
        self.assertEqual(instruction.name, 'mul')
        self.assertEqual(instruction.next_address, 0x4cc3)
        self.assertEqual(self.stack.get_local(3), 0xfffe)
        
    def test_new_line(self):
        instruction = self.processor.decoder.decode_instruction(0x63cb)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63cb)
        self.assertEqual(instruction.name, 'new_line')
        self.assertEqual(instruction.next_address, 0x63cc)
        self.assertEqual(next_address, None)
        string = '\n'
        self.assertEqual(self.output.string, string)
        
    def test_not(self):
        self.fail()

    def test_or(self):
        self.fail()
        
    def test_pop(self):
        self.fail()
        
        
    def test_print(self):
        instruction = self.processor.decoder.decode_instruction(0x6329)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x6329)
        self.assertEqual(instruction.name, 'print')
        self.assertEqual(instruction.next_address, 0x639e)
        self.assertEqual(next_address, None)
        string = 'ZORK: The Great Underground Empire - Part I\nCopyright (c) 1980 by Infocom, Inc. All rights reserved.\nZORK is a trademark of Infocom, Inc.\nRelease '
        self.assertEqual(self.output.string, string)
        
    def test_print_char(self):
        self.stack.push(65)
        instruction = self.processor.decoder.decode_instruction(0x63c5)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63c5)
        self.assertEqual(instruction.name, 'print_char')
        self.assertEqual(instruction.next_address, 0x63c8)
        self.assertEqual(next_address, None)
        string = 'A'
        self.assertEqual(self.output.string, string)
        
    def test_print_num(self):
        self.stack.push(42)
        instruction = self.processor.decoder.decode_instruction(0x63a8)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63a8)
        self.assertEqual(instruction.name, 'print_num')
        self.assertEqual(instruction.next_address, 0x63ab)
        self.assertEqual(next_address, None)
        string = str(42)
        self.assertEqual(self.output.string, string)
    
    def test_print_num_negative(self):
        self.stack.push(0xffff)
        instruction = self.processor.decoder.decode_instruction(0x63a8)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x63a8)
        self.assertEqual(instruction.name, 'print_num')
        self.assertEqual(instruction.next_address, 0x63ab)
        self.assertEqual(next_address, None)
        string = str(-1)
        self.assertEqual(self.output.string, string)
    
    def test_print_obj(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        instruction = self.processor.decoder.decode_instruction(0x5ee2)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5ee2)
        self.assertEqual(instruction.name, 'print_obj')
        self.assertEqual(instruction.next_address, 0x5ee4)
        self.assertEqual(next_address, None)
        string = 'West of House'
        self.assertEqual(self.output.string, string)
    
    def test_print_addr(self):
        self.stack.push(0xffe6)
        instruction = self.processor.decoder.decode_instruction(0x4901)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4901)
        self.assertEqual(instruction.name, 'print_addr')
        self.assertEqual(instruction.next_address, 0x4903)
        self.assertEqual(next_address, None)
        string = 'There is some gunk here.'
        self.assertEqual(self.output.string, string)
            
    def test_print_paddr(self):
        self.stack.locals[-1] = [42, 42, 42, 0xf490 >> 1]
        instruction = self.processor.decoder.decode_instruction(0x5f82)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f82)
        self.assertEqual(instruction.name, 'print_paddr')
        self.assertEqual(instruction.next_address, 0x5f84)
        self.assertEqual(next_address, None)
        string = 'There is a small mailbox here.'
        self.assertEqual(self.output.string, string)

    def test_print_ret(self):
        self.fail()
        
    def test_pull(self):
        self.stack.locals[-1] = [42, 42]
        self.stack.push(1000)
        instruction = self.processor.decoder.decode_instruction(0x5ea3)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x5ea3)
        self.assertEqual(instruction.name, 'pull')
        self.assertEqual(instruction.next_address, 0x5ea6)
        result = self.stack.get_local(1)
        self.assertEqual(result, 1000)
        
    def test_push(self):
        self.stack.locals[-1] = [1000]
        instruction = self.processor.decoder.decode_instruction(0x5e9a)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x5e9a)
        self.assertEqual(instruction.name, 'push')
        self.assertEqual(instruction.next_address, 0x5e9d)
        result = self.stack.pop()
        self.assertEqual(result, 1000)
        
    #def test_put_prop_size_1(self):
    #    self.fail()
    #TODO: not used in zork1-5
        
    def test_put_prop_size_2(self):
        self.memory.write_word(0x0c76, 0xffff)

        instruction = self.processor.decoder.decode_instruction(0x47e2)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x47e2)
        self.assertEqual(instruction.name, 'put_prop')
        self.assertEqual(instruction.next_address, 0x47e7)
        result = self.memory.read_word(0x0c76)
        self.assertEqual(result, 0x001f)
        
    def test_quit(self):
        self.fail()
        
    def test_random(self):
        self.fail()
        
    def test_ret_none(self):
        self.stack.push_call([42, 42, 42, 42, 1000], 1000, None, 2)
        
        instruction = self.processor.decoder.decode_instruction(0x4745)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x4745)
        self.assertEqual(instruction.name, 'ret')
        self.assertEqual(instruction.next_address, 0x4747)
        self.assertEqual(next_address, 1000)
        
    def test_ret_stack(self):
        self.stack.push_call([42, 42, 42, 42, 1000], 1000, 0, 2)
        
        instruction = self.processor.decoder.decode_instruction(0x4745)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x4745)
        self.assertEqual(instruction.name, 'ret')
        self.assertEqual(instruction.next_address, 0x4747)
        self.assertEqual(next_address, 1000)
        self.assertEqual(self.stack.pop(), 1000)
        
    def test_ret_local(self):
        self.stack.locals[-1] = [42]
        self.stack.push_call([42, 42, 42, 42, 1000], 1000, 1, 2)
        
        instruction = self.processor.decoder.decode_instruction(0x4745)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x4745)
        self.assertEqual(instruction.name, 'ret')
        self.assertEqual(instruction.next_address, 0x4747)
        self.assertEqual(next_address, 1000)
        self.assertEqual(self.stack.get_local(0), 1000)
        
    def test_ret_global(self):
        self.stack.push_call([42, 42, 42, 42, 1000], 1000, 0x10, 2)
        
        instruction = self.processor.decoder.decode_instruction(0x4745)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x4745)
        self.assertEqual(instruction.name, 'ret')
        self.assertEqual(instruction.next_address, 0x4747)
        self.assertEqual(next_address, 1000)
        result = self.memory.read_word(self.processor.header.get_globals_table_location())
        self.assertEqual(result, 1000)
        
    def test_ret_popped(self):
        self.stack.push_call([], 1000, 0, 42)
        self.stack.push(42)
        instruction = self.processor.decoder.decode_instruction(0x5f48)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5f48)
        self.assertEqual(instruction.name, 'ret_popped')
        self.assertEqual(instruction.next_address, 0x5f49)
        self.assertEqual(next_address, 1000)
        self.assertEqual(self.stack.pop(), 42)
        
    def test_rfalse(self):
        self.stack.push_call([], 1000, 0, 42)
        instruction = self.processor.decoder.decode_instruction(0x7967)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x7967)
        self.assertEqual(instruction.name, 'rfalse')
        self.assertEqual(instruction.next_address, 0x7968)
        self.assertEqual(next_address, 1000)
        self.assertEqual(self.stack.pop(), 0)
        
    def test_rtrue(self):
        self.stack.push_call([], 1000, 0, 42)
        
        instruction = self.processor.decoder.decode_instruction(0x63cc)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        
        self.assertEqual(instruction.start, 0x63cc)
        self.assertEqual(instruction.name, 'rtrue')
        self.assertEqual(instruction.next_address, 0x63cd)
        self.assertEqual(next_address, 1000)
        self.assertEqual(self.stack.pop(), 1)
        
    def test_set_attr(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
    
        instruction = self.processor.decoder.decode_instruction(0x5edc)
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5edc)
        self.assertEqual(instruction.name, 'set_attr')
        self.assertEqual(instruction.next_address, 0x5edf)
        self.assertEqual(next_address, None)
        result = self.processor.object_table.get_object_attribute(35, 0x1c)
        self.assertTrue(result)
        
    def test_sread(self):
        self.fail()

    #TODO: test 0xc89f
            
    #def test_store_stack(self):
    #    self.fail()
    #TODO: test this: not in zork1-5
        
    def test_store_local(self):
        self.stack.locals[-1] = [42, 42]
        instruction = self.processor.decoder.decode_instruction(0x5edf)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x5edf)
        self.assertEqual(instruction.name, 'store')
        self.assertEqual(instruction.next_address, 0x5ee2)
        self.assertEqual(next_address, None)
        result = self.stack.get_local(1)
        self.assertEqual(result, 1)
        
    def test_store_global(self):
        instruction = self.processor.decoder.decode_instruction(0x481d)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x481d)
        self.assertEqual(instruction.name, 'store')
        self.assertEqual(instruction.next_address, 0x4820)
        self.assertEqual(next_address, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location())
        self.assertEqual(result, 0x23)
    
    def test_storeb(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x34 << 1), 49)
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x0b << 1), 100)
        self.memory.write_byte(50, 42)
        
        instruction = self.processor.decoder.decode_instruction(0x4adb)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4adb)
        self.assertEqual(instruction.name, 'storeb')
        self.assertEqual(instruction.next_address, 0x4ae0)
        self.assertEqual(next_address, None)
        result = self.memory.read_byte(50)
        self.assertEqual(result, 100)
        
    def test_storew(self):
        self.stack.locals[-1] = [1000, 42, 42, 42, 46]
        self.memory.write_word(50, 42)
        
        instruction = self.processor.decoder.decode_instruction(0x4740)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4740)
        self.assertEqual(instruction.name, 'storew')
        self.assertEqual(instruction.next_address, 0x4745)
        self.assertEqual(next_address, None)
        result = self.memory.read_word(50)
        self.assertEqual(result, 1000)
        
    def test_sub_both_positive_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 1000 + 0x6)
        
        instruction = self.processor.decoder.decode_instruction(0x4731)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4731)
        self.assertEqual(instruction.name, 'sub')
        self.assertEqual(instruction.next_address, 0x4735)
        self.assertEqual(next_address, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location() + (0x62 << 1))
        self.assertEqual(result, 1000)
        
    def test_sub_both_positive_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0x5)
        
        instruction = self.processor.decoder.decode_instruction(0x4731)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4731)
        self.assertEqual(instruction.name, 'sub')
        self.assertEqual(instruction.next_address, 0x4735)
        self.assertEqual(next_address, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location() + (0x62 << 1))
        self.assertEqual(result, 0xffff)
        
    def test_sub_first_negative_no_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0xfff6)
        
        instruction = self.processor.decoder.decode_instruction(0x4731)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4731)
        self.assertEqual(instruction.name, 'sub')
        self.assertEqual(instruction.next_address, 0x4735)
        self.assertEqual(next_address, None)
        result = self.memory.read_word(self.processor.header.get_globals_table_location() + (0x62 << 1))
        self.assertEqual(result, 0xfff0)
        
    def test_sub_first_negative_with_overflow(self):
        self.memory.write_word(self.processor.header.get_globals_table_location() + (0x62 << 1), 0x8005)
        
        instruction = self.processor.decoder.decode_instruction(0x4731)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4731)
        self.assertEqual(instruction.name, 'sub')
        self.assertEqual(instruction.next_address, 0x4735)
        self.assertEqual(next_address, None)
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
        
    def test_test(self):
        self.fail()  #0x5590
        
    def test_test_attr_false(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        instruction = self.processor.decoder.decode_instruction(0x4826)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4826)
        self.assertEqual(instruction.name, 'test_attr')
        self.assertEqual(instruction.next_address, 0x482a)
        self.assertEqual(next_address, 0x482a)
    
    def test_test_attr_true(self):
        self.memory.write_word(self.processor.header.get_globals_table_location(), 35)
        self.processor.object_table.set_object_attribute(35, 0x1c)
        instruction = self.processor.decoder.decode_instruction(0x4826)    
        assembled, continuable = instruction.assemble(False)
        compiled = compile(assembled, '<test>', 'exec')
        next_address = self.processor.execute(compiled)
        self.assertEqual(instruction.start, 0x4826)
        self.assertEqual(instruction.name, 'test_attr')
        self.assertEqual(instruction.next_address, 0x482a)
        self.assertEqual(next_address, 0x4830)     

class TestDecoderV1(unittest.TestCase):
    def setUp(self):
        self.memory = chatmachine.memory.MemoryV1('data/zork1-5.z5')
        self.stack = chatmachine.stack.Stack()
        self.input = chatmachine.streams.KeyboardInputStreamV1()
        self.output = chatmachine.streams.ScreenOutputStreamV1()

        self.processor = chatmachine.processor.ProcessorV1(self.memory, self.stack, self.input, self.output)
        
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
        instruction = self.processor.decoder.decode_instruction(0x56d1)
        self.assertEqual(str(instruction), 'INC_CHK #04,L02 [FALSE] 56bc')
    
    def test_decode_2op_sc_sc(self):
        instruction = self.processor.decoder.decode_instruction(0x481d)
        self.assertEqual(str(instruction), 'STORE #10,#23')
        
    def test_decode_2op_sc_var(self):
        instruction = self.processor.decoder.decode_instruction(0x4823)
        self.assertEqual(str(instruction), 'STORE #2d,G00')
        
    def test_decode_2op_var_sc(self):
        instruction = self.processor.decoder.decode_instruction(0x4725)
        self.assertEqual(str(instruction), 'ADD G72,#b4 -> L02')
        
    def test_decode_2op_var_var(self):
        instruction = self.processor.decoder.decode_instruction(0x4729)
        self.assertEqual(str(instruction), 'ADD G72,G62 -> L03')
        
    def test_decode_1op_lc(self):
        instruction = self.processor.decoder.decode_instruction(0x4755)
        self.assertEqual(str(instruction), 'JUMP #ffd7')
        
    def test_decode_1op_sc(self):
        instruction = self.processor.decoder.decode_instruction(0x4ca1)
        self.assertEqual(str(instruction), 'INC #04')
        
    def test_decode_1op_var(self):
        instruction = self.processor.decoder.decode_instruction(0x4735)
        self.assertEqual(str(instruction), 'JZ L01 [TRUE] 473c')
        
    def test_decode_0op(self):
        instruction = self.processor.decoder.decode_instruction(0x63cb)
        self.assertEqual(str(instruction), 'NEW_LINE ')
             
    def test_decode_var_1(self):
        instruction = self.processor.decoder.decode_instruction(0x482a)
        self.assertEqual(str(instruction), 'CALL 6326 () -> -(SP)')
        
    def test_decode_var_2(self):
        instruction = self.processor.decoder.decode_instruction(0x470d)
        self.assertEqual(str(instruction), 'CALL 471a (L00) -> L02')
        
    def test_decode_var_3(self):
        instruction = self.processor.decoder.decode_instruction(0x4740)
        self.assertEqual(str(instruction), 'STOREW L04,#02,L00')
        
    def test_decode_var_4(self):
        instruction = self.processor.decoder.decode_instruction(0x5f3f)
        self.assertEqual(str(instruction), 'CALL 5fdc (G00,L00,#ffff) -> -(SP)')
        

