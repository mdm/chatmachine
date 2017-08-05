import zoperators
import streams
import random
import array

import logging
logging.basicConfig(filename='debug.log',level=logging.DEBUG)

class ProcessorV1(object):
    def __init__(self, memory, stack, input, output):
        #TODO: handle Z-code versions via processor subclasses
        self.memory = memory
        self.header = self.memory.get_header()
        self.object_table = self.memory.get_object_table()
        self.stack = stack
        
        self.input = input
        self.output = output
        
        self.decoder = zoperators.DecoderV1(self.memory)                   
        self.cache = {}
        self.running = False
        self.debugging = False
    
    def execute(self, instruction):
        next_address = None
        exec(instruction)
        return next_address
    
    def debug(self):
        self.debugging = True
        self.run()
        
    def halt(self):
        self.running = False

    def run(self):
        pc = self.memory.get_header().get_initial_pc()
    
        block = []
        start = pc
        count = 0
        self.running = True
        self.debugging = True
        instructions = {}
        
        while (self.running):
            try:
                if (pc in self.cache) and (len(block) == 0):
                    #logging.debug('%x: (cached block)' % pc)
                    logging.debug('%x: %s' % (pc, str(instructions[pc])))
                    pc = self.execute(self.cache[pc])
                    start = pc
                else:
                    instruction = self.decoder.decode_instruction(pc)
                    assembled, continuable = instruction.assemble(self.debugging)
                    block.append(assembled)
                    logging.debug('%x: %s' % (pc, str(instruction)))
                    #if instruction.name == 'call':
                    #    raise NotImplementedError, 'untested call'
                    if continuable:
                        pc = instruction.next_address
                    else:
                        #logging.debug(' %d, %d' % (start, pc))
                        #logging.debug('\n' + '\n'.join(block))
                        compiled = compile('\n'.join(block), '<jit>', 'exec')   
                        self.cache[start] = compiled
                        instructions[start] = instruction
                        pc = self.execute(compiled)
                        block = []
                        start = pc
                count += 1
            except Exception:
                print count, 'instructions were executed.', self.debugging
                print 'calls:', self.stack.calls
                print 'locals:', self.stack.locals
                print 'stack:', self.stack.stack
                print '0x%x' % instruction.start, str(instruction)
                print assembled
                print self.memory.read_word(self.header.get_globals_table_location() + (0x26 << 1))
                raise
    
    def save_state(self, pc):
        save_filename = self.memory.get_story_filename() + '.sav'
        data = array.array('B')
        data.fromstring('IFZS')
        data.fromstring('IFhd')
        data.fromlist([0, 0, 0, 13])
        data.append(self.memory.read_byte(0x2))
        data.append(self.memory.read_byte(0x3))
        for i in range(6):
            data.append(self.memory.read_byte(0x12 + i))
        checksum = self.memory.get_checksum()
        checksum = self.memory.read_word(0x1C)
        data.append(checksum >> 8)
        data.append(checksum & 0xFF)
        data.append(pc >> 16)
        data.append((pc >> 8) & 0xFF)
        data.append(pc & 0xFF)
        data.append(0) # pad byte
        data.fromstring('CMem')
        memory = self.memory.serialize()
        length = len(memory)
        data.append(length >> 24)
        data.append((length >> 16) & 0xFF)
        data.append((length >> 8) & 0xFF)
        data.append(length & 0xFF)
        data.extend(memory)
        if length % 2 == 1:
            data.append(0) # pad byte
        data.fromstring('Stks')
        stack = self.stack.serialize()
        length = len(stack)
        data.append(length >> 24)
        data.append((length >> 16) & 0xFF)
        data.append((length >> 8) & 0xFF)
        data.append(length & 0xFF)
        data.extend(stack)
        if length % 2 == 1:
            data.append(0) # pad byte
        save_file = open(save_filename, 'wb')
        save_file.write('FORM')
        length = len(data)
        save_file.write(chr(length >> 24))
        save_file.write(chr((length >> 16) & 0xFF))
        save_file.write(chr((length >> 8) & 0xFF))
        save_file.write(chr(length & 0xFF))
        save_file.write(data)
        save_file.close()
    
    def restore_state(self):
        story_filename = self.memory.get_story_filename()
        flags = None
        memory = None
        stack = None
        self.memory = self.memory.__class__.deserialize(story_filename, flags, memory)
        self.stack = self.stack.__class__.deserialize(stack)

