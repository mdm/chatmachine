import sys

class Screen(object):
    def __init__(self, version):
        self.esc = "%s[" % chr(27)
        self.version = version
        self.upper_window_size = 0
        self.upper_window_selected = False
        self.reset()

    def reset(self):
        self.set_text_style(0)
        self.clear_screen()

    def split_window(self, size):
        self.upper_window_size = size
        if (self.version == 3):
            self.clear_window(False)

    def set_window(self, number):
        if (number == 1):
            if not self.upper_window_selected:
                self.save_cursor()
                self.upper_window_selected = True
            self.set_cursor(1,1)
        else:
            self.restore_cursor()
            self.upper_window_selected = False

    # ANSI specific methods below

    def ansi(self, cmd):
        self.write("%s%s" % (self.esc, cmd))

    def save_cursor(self):
        self.ansi('s')
    
    def restore_cursor(self):
        self.ansi('u')

    def set_cursor(self, row, column):
        self.ansi("%d;%dH" % (row, column))

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
            pass             # fixed pitch

    def set_colour(self, foreground, background):
        if not (foreground == 0):
            if (foreground == -1):
                pass         # colour under cursor
            elif (foreground == 1):
                self.ansi('39m')         # default
            elif (foreground == 10):
                pass         # light grey
            elif (foreground == 11):
                pass         # medium grey
            elif (foreground == 12):
                pass         # dark grey
            else:
                self.ansi(str(28 + foreground) + 'm')
        if not (background == 0):
            if (background == -1):
                pass         # colour under cursor
            elif (background == 1):
                self.ansi('49m')         # default
            elif (background == 10):
                pass         # light grey
            elif (background == 11):
                pass         # medium grey
            elif (background == 12):
                pass         # dark grey
            else:
                self.ansi(str(38 + background) + 'm')

    def write(self, string):
        sys.stdout.write(string)
