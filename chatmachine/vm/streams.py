class OutputStream(object):
    def write(self, string):
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
        self.file.close()

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

class InputStream(object):
    def read(self):
        pass
        
class FileInputStream(InputStream):
    pass
    
class InputMux(InputStream):
    pass
    

