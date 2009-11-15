import binascii
import struct

test = '17 C4 3A 6B 52 F2 00 91 38 F7 1A FE 97 E5'
bin = binascii.a2b_hex(test.replace(' ', ''))
print bin

zchars = []
for i in range(len(bin) / 2):
    word = struct.unpack_from('>H', bin, i * 2)[0]
    zchars.append((word & 0x7C00) >> 10)
    zchars.append((word & 0x3E0) >> 5)
    zchars.append(word & 0x1F)
    if (word & 0x8000):
	end = True
    else:
	end = False

upcase = False
punct = False
zscii = ''
A2 = " \n0123456789.,!?_#'\"/\\-:()"
for char in zchars:
    if (char == 0):
	zscii += ' '
    elif (char == 4):
	upcase = True
    elif (char == 5):
	punct = True
    else:
	if (upcase):
	    zscii += chr(char - 6 + ord('A'))
	elif (punct):
	    if (char == 6):
		zscii += '*'
	    else:
		zscii += A2[char - 6]
	else:
	    zscii += chr(char - 6 + ord('a'))
	upcase = False
	punct = False

print zchars
print zscii
    

    
