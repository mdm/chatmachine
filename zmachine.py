import sys
import cProfile

import memory
import stack
import screen
import keyboard
import streams
import processor


memory = memory.Memory(sys.argv[1])
stack = stack.Stack()

screen = screen.Screen(memory.get_header().get_z_version())
out_screen = streams.ScreenWriter(screen)

transcript_file = None
out_transcript = streams.FileWriter(transcript_file)

out_memory = streams.MemoryWriter(memory)

command_file = None
out_command = streams.FileWriter(command_file)


#keyboard = keyboard.Keyboard()
keyboard = None
in_keyboard = streams.KeyboardReader(keyboard)

input_file = None
in_file = streams.FileReader(input_file)


processor = processor.Processor(memory, stack, out_screen, out_transcript, out_memory, out_command, in_keyboard, in_file)


cProfile.run(processor.run(), 'profile.txt')
print 'Goodbye'
