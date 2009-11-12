import struct

class Heap:
    def __init__(self, filename):
	story_file = open(filename)
	self.data = story_file.read()
	story_file.close()
	self.header = Header(self)

    def read_byte(self, address):
	return struct.unpack_from('B', self.data, address)[0]

    def write_byte(self, address, value):
	struct.pack_to('B', self.data, address, value)[0]

    def read_word(self, address, signed = False):
	if (signed):
	    return struct.unpack_from('>h', self.data, address)[0]
	else:
	    return struct.unpack_from('>H', self.data, address)[0]

    def write_word(self, address, value, signed = False):
	if (signed):
	    struct.pack_to('>h', self.data, address, value)[0]
	else:
	    struct.pack_to('>H', self.data, address, value)[0]

    def get_header(self):
	return self.header


class Header:
    #STATUS_TYPE, FILE_SPLIT, STATUS_AVAILABLE, SCREEN_SPLIT_AVAILABLE, VARIABLE_DEFAULT_FONT = 1, 2, 4, 5, 6
    def __init__(self, heap):
	self.heap = heap

    def get_z_version(self):
	return self.heap.read_byte(0x0)

    def get_high_memory_base(self):
	return self.heap.read_word(0x4)

    def get_initial_pc(self):
	#print self.memory
	return self.heap.read_word(0x6)

    def get_dictionary_location(self):
	return self.heap.read_word(0x8)

    def get_object_table_location(self):
	return self.heap.read_word(0xA)

    def get_globals_table_location(self):
	return self.heap.read_word(0xC)

    def get_static_memory_base(self):
	return self.heap.read_word(0xE)

    def get_flags2(self):
	return self.heap.read_word(0x10)

    def get_abbrevations_table_location(self):
	return self.heap.read_word(0x18)

    def get_file_length(self):
	return self.heap.read_word(0x1A)

    def get_checksum(self):
	return self.heap.read_word(0x1C)

    def get_interpreter_number(self):
	return self.heap.read_byte(0x1E)

    def get_interpreter_version(self):
	return self.heap.read_byte(0x1F)

    def get_screen_height(self):
	return self.heap.read_byte(0x20)

    def get_screen_width(self):
	return self.heap.read_byte(0x21)

    # TODO: some entires ommitted. check.

    def get_terminating_chars_table_location(self):
	return self.heap.read_word(0x2E)

    def get_alphabet_table_location(self):
	return self.heap.read_word(0x34)

    def get_header_extension_table_location(self):
	return self.heap.read_word(0x36)



