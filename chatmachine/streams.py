import sys
import subprocess

class OutputStream(object):
    def write(self, string):
        pass

class InputStream(object):
    def read(self):
        pass
            
class FileOutputStreamV1(OutputStream):
    def __init__(self, filename):
        self.active = False
        self.filename = filename
            
    def write(self, string):
        if not self.active:
            self.file = open(self.filename, 'wb')
            self.active = True
        self.file.write(string)
        
    def __del__(self):
        if self.active:
            self.file.close()

class ScreenOutputStreamV1(OutputStream):
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
       
class KeyboardInputStreamV1(InputStream):
    def read(self):
        return raw_input() + '\n'

class MemoryOutputStreamV3(OutputStream):
    pass

class OutputDemuxV1(OutputStream):
    def __init__(self, screen, transcript, header):
        self.screen = screen
        self.transcript = transcript
        self.header = header
        
    def write(self, string, echo = False):
        if echo:
            if self.header.get_flag_transcript():
                self.transcript.write(string)
        else:
            if self.header.get_flag_transcript():
                self.transcript.write(string)
            self.screen.write(string)
    
    def __getattr__(self, name):
        return getattr(self.screen, name)

class FileInputStream(InputStream):
    pass
    
class InputMux(InputStream):
    pass
    

