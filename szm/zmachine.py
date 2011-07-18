import sys
import cProfile

import memory2
import stack
import streams2
import processor2


memory = memory2.Memory(sys.argv[1])
stack = stack.Stack()
input = streams2.KeyboardInputStreamV1()
output = streams2.ScreenOutputStreamV1()

processor = processor2.ProcessorV1(memory, stack, input, output)


#profile = ''
#cProfile.run(processor.run(), profile)

processor.run()
print 'Goodbye'


