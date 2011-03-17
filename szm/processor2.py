class Processor(object):
    def __init__(self, memory, stack, out_screen, out_transcript, out_memory, out_command, in_keyboard, in_file):
        #TODO: handle Z-code versions via processor subclasses
        self.memory = memory
        self.stack = stack
        
        self.outputs = {}
        self.outputs['screen'] = out_screen
        self.outputs['screen'].select()
        self.outputs['transcript'] = out_transcript
        self.outputs['memory'] = out_memory
        self.outputs['command'] = out_command
        self.inputs = {}
        self.inputs['keyboard'] = in_keyboard
        self.inputs['file'] = in_file
        self.selected_input = 'keyboard'
        
        self.names = {}
        self.names['2OP'] = ['halt', 'je','jl', 'jg', 'dec_chk', 'inc_chk', 'jin', 'test', 'or', 'and', 'test_attr', 'set_attr', 'clear_attr', 'store', 'insert_obj', 'loadw', 'loadb', 'get_prop', 'get_prop_addr', 'get_next_prop', 'add', 'sub', 'mul', 'div', 'mod', 'call_2s', 'call_2n', 'set_colour', 'throw'] # 'halt' has no opcode, but is used as a placeholder
        self.names['1OP'] = ['jz', 'get_sibling', 'get_child', 'get_parent', 'get_prop_len', 'inc', 'dec', 'print_addr', 'call_1s', 'remove_obj', 'print_obj', 'ret', 'jump', 'print_paddr', 'load', 'call_1n'] #TODO: replace 'call_1n' with 'not' for versions 1-4
        self.names['0OP'] = ['rtrue', 'rfalse', 'print', 'print_ret', 'nop', 'save', 'restore', 'restart', 'ret_popped', 'catch', 'quit', 'new_line', 'show_status', 'verify', 'extended', 'piracy'] #TODO: replace 'catch' with 'pop' for versions 1-4 and handle illegal instructions correctly
        self.names['VAR'] = ['call', 'call_vs', 'storew', 'storeb', 'put_prop', 'read', 'print_char', 'print_num', 'random', 'push', 'pull', 'split_window', 'set_window', 'call_vs2', 'erase_window', 'erase_line', 'set_cursor', 'get_cursor', 'set_text_style', 'buffer_mode', 'output_stream', 'input_stream', 'sound_effect', 'read_char', 'scan_table', 'not', 'call_vn', 'call_vn2', 'tokenise', 'encode_text', 'copy_table', 'print_table', 'check_arg_count']
        self.names['EXT'] = ['save', 'restore', 'log_shift', 'art_shift', 'set_font', 'draw_picture', 'picture_data', 'erase_picture', 'set_margins', 'save_undo', 'restore_undo', 'print_unicode', 'check_unicode']
        
        self.running = False
    
    def decode_all(self):
        self.current = first
        
    def run(self):
        self.running = True
        while (self.running):
            self.current.execute()
            self.current = self.current.next()
    
    def debug(self):
        pass
        
    def halt():
        self.running = False
        
