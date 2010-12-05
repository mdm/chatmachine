class ZString:
    def __init__(self):
        self.chars = []
        self.A2 = " \n0123456789.,!?_#'\"/\\-:()"
        
    def unpack_words(self, words):
        self.chars = []
        for word in words:
            self.chars.append((word & 0x7C00) >> 10)
            self.chars.append((word & 0x3E0) >> 5)
            self.chars.append(word & 0x1F)
            if (word & 0x8000):
                break

    def pack_words(self, chars = None):
        if not chars:
            chars = self.chars
            while ((len(self.chars) % 3) > 0):
                chars.append(5)
        word = chars[0] << 10
        word += chars[1] << 5
        word += chars[2]
        if (len(chars) == 3):
            return [word | 0x8000]
        else:
            return [word] + self.pack_words(chars[3:])

    def compact(self):
        new_chars = []
        shifting = False
        for char in self.chars:
            if char in [4, 5]:
                if shifting:
                    new_chars[-1] = char
                else:
                    new_chars.append(char)
                shifting = True
            else:
                new_chars.append(char)
                shifting = False
        if (len(new_chars) == 1) and shifting:
            self.chars = []
        else:
            while (new_chars[-1] in [4, 5]):
                new_chars.pop()
            self.chars = new_chars

    def encode(self, unencoded):
        self.chars = []
        for char in unencoded:
            value = ord(char)
            if ord('a') <= value <= ord('z'):
                self.chars.append(value - ord('a') + 6)
            elif ord('A') <= value <= ord('Z'):
                self.chars.append(4)
                self.chars.append(value - ord('A') + 6)
            elif (char == ' '):
                self.chars.append(0)
            elif char in self.A2:
                self.chars.append(5)
                self.chars.append(self.A2.index(char) + 6)
            else:
                print "ERROR: Don't know how to encode", char, "(%d)" % ord(char)

    def decode(self):
        self.compact()
        zscii = ''
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
                    zscii += self.A2[self.chars[i] - 6]
            else:
                zscii += chr(self.chars[i] - 6 + ord('a'))
            i += 1
        return zscii

    def __str__(self):
        return self.decode()
    
