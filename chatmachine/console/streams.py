import sys
import subprocess

import vm.streams

class ScreenOutputStreamV1(vm.streams.OutputStream):
    def __init__(self):
        self.esc = "%s[" % chr(27)
        sys.stdout.write(self.esc + '2J' + self.esc + '2;1H')
        
    def write(self, string):
        sys.stdout.write(string)
        
    def redraw_status(self, room, score, turns):
        width = int(subprocess.check_output(['tput', 'cols']))
        sys.stdout.write(self.esc + 's' + self.esc + 'H' + self.esc + '7m' + self.esc + 'K')
        string = "Score: %d, Turns: %d" % (score, turns)
        sys.stdout.write(room + ' ' * (width - len(room) - len(string)) + string + '\n')
        sys.stdout.write(self.esc + 'u' + self.esc + '0m')
       
class KeyboardInputStreamV1(vm.streams.InputStream):
    def read(self):
        return raw_input() + '\n'

