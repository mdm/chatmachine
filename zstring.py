class ZString:
    def __init__(self):
        self.chars = []
        
    def add(self, word):
        self.chars.append((word & 0x7C00) >> 10)
        self.chars.append((word & 0x3E0) >> 5)
        self.chars.append(word & 0x1F)
        if (word & 0x8000):
            #print self.chars
            return False
        else:
            return True

    def compact(self):
        while (self.chars[-1] == 5): self.chars.pop()
        #TODO: remove all runs of 4's and 5's

    def __str__(self):
        self.compact()
        zscii = ''
        A2 = " \n0123456789.,!?_#'\"/\\-:()"
        i = 0
        while i < len(self.chars):
            if (self.chars[i] == 0):
                zscii += ' '
            elif (self.chars[i] == 4):
                i += 1
                zscii += chr(self.chars[i] - 6 + ord('A'))
            elif (self.chars[i] == 5):
                i += 1
                if (self.chars[i] == 6):
                    zscii += chr((self.chars[i + 1] << 5) + self.chars[i + 2])
                    i += 2
                else:
                    zscii += A2[self.chars[i] - 6]
            else:
                zscii += chr(self.chars[i] - 6 + ord('a'))
            i += 1
        return zscii

    

    
