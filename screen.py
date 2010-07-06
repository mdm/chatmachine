import sys

class Screen(object):
    def __init__(self, version):
        self.esc = "%s[" % chr(27)
        self.version = version
        self.upper_window_size = 0
        self.upper_window_selected = False
        self.clear_screen()

    def split_window(self, size):
        self.upper_window_size = size
        if (self.version == 3):
            self.clear_window(False)

    def set_window(self, number):
        if (number == 1):
            self.upper_window_selected = True
        else:
            print '@@@', number

    # ANSI specific methods below

    def ansi(self, cmd):
        self.write("%s%s" % (self.esc, cmd))

    def save_cursor(self):
        print 'Not yet implemented!!'
    
    def restore_cursor(self):
        print 'Not yet implemented!!'

    def set_cursor(self, row, column):
        self.ansi('%d;%dH' % (row, column))

    def clear_window(self, clear_lower_window):
        print 'Not yet implemented!!'

    def clear_screen(self):
        self.ansi('2J')  # clear screen
        self.ansi('H')  # move to top left
        
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

    def write(self, string):
        sys.stdout.write(string)
