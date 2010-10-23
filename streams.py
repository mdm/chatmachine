class Writer(object):
    def __init__(self):
        self.selected = False

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def write(self, string):
        print 'ERROR: Stream writer does not implement write()'


class Reader(object):
    def read(self, max_len, time, terminating_chars):
        print 'ERROR: Stream reader does not implement read()'




class ScreenWriter(Writer):
    def __init__(self, screen):
        self.selected = False
        self.screen = screen

    def write(self, string):
        self.screen.write(string)


class FileWriter(Writer):
    def __init__(self, file):
       self.selected = False
       self.file = file


class MemoryWriter(Writer):
    def __init__(self, memory):
        self.selected = False
        self.memory = memory
        self.tables = []
        self.offsets = []

    def select(self, table):
        self.selected = True
        self.tables.append(table)
        self.offsets.append(table + 2)

    def deselect(self):
        self.selected = False
        self.tables.pop()
        self.offsets.pop()

    def write(self, string):
        #print '@@@', [string]
        #print 'MEMWRITE'
        for char in string:
            if ord(char) < 255:
                self.memory.write_byte(self.offsets[-1], ord(char))
                self.offsets[-1] += 1
            else:
                print '*** TRYING TO WRITE ILLEGAL CHARACTER TO MEMORY ***'
        #print self.tables[-1], self.offsets[-1] - (self.tables[-1] + 2)
        self.memory.write_word(self.tables[-1], self.offsets[-1] - (self.tables[-1] + 2))


class KeyboardReader(Reader):
    def __init__(self, keyboard):
        self.keyboard = keyboard

    def read(self, max_len, time, terminating_chars):
        return raw_input()[:max_len] + "\n"

class FileReader(Reader):
    def __init__(self, file):
        self.file = file

    def read(self, max_len, time, terminating_chars):
        pass

