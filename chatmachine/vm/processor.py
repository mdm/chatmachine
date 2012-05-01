import zoperators
import streams
import random

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
        next = None
        exec(instruction)
        return next
    
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
        
        while (self.running):
            try:
                if (pc in self.cache) and (len(block) == 0):
                    logging.debug('%x: (cached block)' % pc)
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
                        pc = instruction.next
                    else:
                        #logging.debug(' %d, %d' % (start, pc))
                        #logging.debug('\n' + '\n'.join(block))
                        compiled = compile('\n'.join(block), '<jit>', 'exec')   
                        self.cache[start] = compiled
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

