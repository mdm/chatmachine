import optparse
import ctypes

import heap

usage = 'usage: %prog [options] storyfile'
epilog = 'A Z-machine intepreter for interactive fiction with Skype support.'
opt_parser = optparse.OptionParser(usage=usage, epilog=epilog)
opt_parser.add_option('-s', '--screen', default='ansi', help='screen type: ansi or skype (default: %default)')
options, arguments = opt_parser.parse_args()

if not arguments:
    opt_parser.print_help()
    sys.exit(-1)

storyfile = open(arguments[0])
story = ctypes.create_string_buffer(storyfile.read())
storyfile.close()

memory = memory.Memory(story)
stack = stack.Stack()
screen = screen.Screen()
# processor = processor.Processor()
# streams = streams.StreamHandler()
# 
