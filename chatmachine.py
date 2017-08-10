#!/usr/bin/python3

import sys
import time
import cProfile

from chatmachine import memory
from chatmachine import stack
from chatmachine import streams
from chatmachine import processor


memory = memory.MemoryV1(sys.argv[1])
stack = stack.Stack()
input = streams.KeyboardInputStreamV1()
screen = streams.ScreenOutputStreamV1()
transcript = streams.FileOutputStreamV1(time.strftime('%Y%m%d%H%M%S') + '.log')
output = streams.OutputDemuxV1(screen, transcript, memory.get_header())

processor = processor.ProcessorV1(memory, stack, input, output)


#profile = ''
#cProfile.run(processor.run(), profile)

processor.run()
print('Goodbye')


