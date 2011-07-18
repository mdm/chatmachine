import sys

class OutputStream(object):
    def write(self, string):
        pass

class ScreenOutputStreamV1(OutputStream):
    def write(self, string):
        sys.stdout.write(string)
    
class FileOutputStreamV1(OutputStream):
    pass

class MemoryOutputStreamV3(OutputStream):
    pass

class OutputDemuxV1(OutputStream):
    pass


class InputStream(object):
    def read(time = 0):
        pass
        
class KeyboardInputStreamV1(InputStream):
    pass

class FileInputStream(InputStream):
    pass
    
class InputMux(InputStream):
    pass
    

