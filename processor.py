import sys
import struct

def readWord(offset, signed = False):
	if (signed):
		return struct.unpack_from('>h', game, offset)[0]
	else:
		return struct.unpack_from('>H', game, offset)[0]

file = open(sys.argv[1])
game = file.read()
file.close()

print len(game)
version = ord(game[0])
print 'Version:', version
highmem_base = readWord(0x4)
print 'High-mem base address:', highmem_base
initial_pc = readWord(0x6)
print 'Initial program counter:', initial_pc
dictionary_loc = readWord(0x8)
object_table_loc = readWord(0xA)
global_var_table_loc = readWord(0xC)
print dictionary_loc, object_table_loc, global_var_table_loc
staticmem_base = readWord(0xE)
print 'Static memory base address:', staticmem_base
flags2 = readWord(0x10)
if (flags2 & 1): print 'Transcripting is on.'
if (flags2 & 2): print 'Game forces fixed-pitch font.'
if (flags2 & 4): print 'Interpreter requests status line redraw.'
if (flags2 & 8): print 'Game wants to use pictures.'
if (flags2 & 16): print 'Game wants to use UNDO opcodes.'
if (flags2 & 32): print 'Game wants to use a mouse.'
if (flags2 & 64): print 'Game wants to use colours.'
if (flags2 & 128): print 'Game wants to use sound effects.'
if (flags2 & 256): print 'Game wants to use menus.'
abbr_table_loc = readWord(0x18)
print abbr_table_loc
file_length = readWord(0x1A)
print 'File length:', file_length
checksum = readWord(0x1C)
print 'Checksum:', checksum
interpreter_number = ord(game[0x1E])
interpreter_version = ord(game[0x1F])
print 'Interpreter:', interpreter_number, interpreter_version
screen_height_chars = ord(game[0x20])
screen_width_chars = ord(game[0x21])
print 'Screen size (chars):', screen_width_chars, screen_height_chars
screen_width_units = readWord(0x22)
screen_height_units = readWord(0x24)
print 'Screen size (units):', screen_width_units, screen_height_units
font_width_units = ord(game[0x26])
font_height_units = ord(game[0x27])
print 'Font size (units):', font_width_units, font_height_units
default_bg_color = ord(game[0x2C])
default_fg_color = ord(game[0x2D])
print 'Default colors (bg, fg):', default_bg_color, default_fg_color
term_char_table_loc = readWord(0x2E)
print term_char_table_loc
alphabet_table_loc = readWord(0x34)
print alphabet_table_loc
header_ext_table_loc = readWord(0x36)
print header_ext_table_loc

isRunning = True
while (isRunning):
	#fetch
	#decode
	#exec
	isRunning = False

print 'Goodbye'
