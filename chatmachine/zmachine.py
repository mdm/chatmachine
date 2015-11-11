import sys
import time
import cProfile

import console.streams
import vm.memory
import vm.stack
import vm.streams
import vm.processor


memory = vm.memory.MemoryV1(sys.argv[1])
stack = vm.stack.Stack()
input = console.streams.KeyboardInputStreamV1()
screen = console.streams.ScreenOutputStreamV1()
transcript = vm.streams.FileOutputStreamV1(time.strftime('%Y%m%d%H%M%S') + '.log')
output = vm.streams.OutputDemuxV1(screen, transcript, memory.get_header())

processor = vm.processor.ProcessorV1(memory, stack, input, output)


#profile = ''
#cProfile.run(processor.run(), profile)

processor.run()
print 'Goodbye'


