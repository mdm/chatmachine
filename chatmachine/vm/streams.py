import sys

class OutputStream(object):
    def write(self, string):
        pass

class ScreenOutputStreamV1(OutputStream):
    def write(self, string):
        sys.stdout.write(string)
        
    def redraw_status(self, room, score, turns):
        string = "(%s,    score: %d, turns: %d)\n" % (room, score, turns)
        sys.stdout.write(string)
       
    
class FileOutputStreamV1(OutputStream):
    pass

class MemoryOutputStreamV3(OutputStream):
    pass

class OutputDemuxV1(OutputStream):
    pass


class InputStream(object):
    def read(self):
        pass
        
class KeyboardInputStreamV1(InputStream):
    def read(self):
        return raw_input()

class FileInputStream(InputStream):
    pass
    
class InputMux(InputStream):
    pass
    

