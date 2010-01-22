import sys

class OutputStream(object):
    def __init__(self):
        self.selected = False

    def write(self, data):
        print 'ERROR: Output stream does not implement write()'

class InputStream(object):
    def __init__(self):
        self.selected = False

    def read(self, terminating_chars):
        pass


class ScreenWriter(OutputStream):
    def __init__(self):
        super(ScreenWriter, self).__init__()
        self.selected = True

    def write(self, data):
        pass

    def get_features(self):
        pass

    def set_text_style(self):
        pass

class ConsoleWriter(ScreenWriter):
    def __init__(self):
        super(ConsoleWriter, self).__init__()
        self.esc = "%s[" % chr(27)
        self.ansi('2J')  # clear screen
        self.ansi('H')  # move to top left

    def write(self, string):
        sys.stdout.write(str(string))

    def ansi(self, cmd):
        self.write("%s%s" % (self.esc, cmd))

    def set_text_style(self, style):
        if (style == 0):
            self.ansi('0m')  # reset
        elif (style == 1):
            self.ansi('7m')  # reverse video
        elif (style == 2):
            self.ansi('1m')  # bold
        elif (style == 4):
            self.ansi('4m')  # italic --> underlined
        elif (style == 8):
            pass

class FileWriter(OutputStream):
    pass

class MemoryWriter(OutputStream):
    pass


class ConsoleReader(InputStream):
    pass

class FileReader(InputStream):
    def read(self, terminating_chars):
        pass

