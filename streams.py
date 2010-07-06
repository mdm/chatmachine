class Writer(object):
    def __init__(self):
        self.selected = False

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def write(self, data):
        print 'ERROR: Stream writer does not implement write()'


class Reader(object):
    def read(self, max_len, time, terminating_chars):
        print 'ERROR: Stream reader does not implement read()'




class ScreenWriter(Writer):
    def __init__(self, screen):
        self.selected = False
        self.screen = screen

    def write(self, data):
        self.screen.write(data)


class FileWriter(Writer):
    def __init__(self, file):
       self.selected = False
       self.file = file


class MemoryWriter(Writer):
    def __init__(self, memory):
        self.selected = False
        self.memory = memory
        self.tables = []

    def select(self, table):
        self.selected = True
        self.tables.append(table)

    def deselect(self):
        self.selected = False
        self.tables.pop()




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

