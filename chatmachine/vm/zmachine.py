import sys
import cProfile

import memory
import stack
import streams
import processor


memory = memory.MemoryV1(sys.argv[1])
stack = stack.Stack()
input = streams.KeyboardInputStreamV1()
output = streams.ScreenOutputStreamV1()

processor = processor.ProcessorV1(memory, stack, input, output)


#profile = ''
#cProfile.run(processor.run(), profile)

processor.run()
print 'Goodbye'


