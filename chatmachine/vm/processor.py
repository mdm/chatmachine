import zoperators
import streams
import sys

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
        self.debugging = True
    
    def execute(self, instruction):
        next = None
        exec(instruction)
        return next
    
    def debug(self):
        pass
        
    def halt():
        self.running = False

    def run(self):
        pc = self.memory.get_header().get_initial_pc()
    
        block = []
        count = 0
        self.running = True
        while (self.running):
            try:
                if (pc in self.cache) and (len(block) == 0):
                    logging.debug('%x\n(cached)' % pc)
                    pc = self.execute(self.cache[pc])
                else:
                    instruction = self.decoder.decode_instruction(pc)
                    if instruction.name == 'clear_attr' and count > 0:
                        raise NotImplementedError, 'untested clear_attr'
                    if instruction.name == 'put_prop' and count > 112:
                        raise NotImplementedError, 'untested put_prop (size 1)'
                    assembled, continuable = instruction.assemble(self.debugging)
                    block.append(assembled)
                    #if instruction.name == 'call':
                    #    raise NotImplementedError, 'untested call'
                    if continuable:
                        logging.debug('%x\n(building)' % pc)
                        pc = instruction.next
                    else:
                        compiled = compile('\n'.join(block), '<jit>', 'exec')   
                        block = []
                        self.cache[pc] = compiled
                        logging.debug('%x\n%s\n(new block)' % (pc, str(instruction)))
                        pc = self.execute(compiled)
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


