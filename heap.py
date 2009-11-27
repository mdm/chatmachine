import struct
import ctypes
import logging

import zstring

logger = logging.getLogger('heap')

class Heap:
    def __init__(self, filename):
        story_file = open(filename)
        self.data = ctypes.create_string_buffer(story_file.read())
        story_file.close()
        self.header = Header(self)
        self.object_table = ObjectTable(self)

    def read_byte(self, address):
        if not (0 <= address < (len(self.data) - 1)): raise IndexError
        byte = struct.unpack_from('B', self.data, address)[0]
        logger.debug("read [%02X]" % byte)
        return byte

    def write_byte(self, address, value):
        if not (0 <= address < (len(self.data) - 1)): raise IndexError
        if not (0 <= value <= 0xFF): raise ValueError
        struct.pack_into('B', self.data, address, value)

    def read_word(self, address):
        if not (0 <= address < (len(self.data) - 2)): raise IndexError
        word = struct.unpack_from('>H', self.data, address)[0]
        logger.debug("read [%04X]" % word)
        return word

    def write_word(self, address, value, signed = False):
        if not (0 <= address < (len(self.data) - 2)): raise IndexError
        if not (0 <= value <= 0xFFFF): raise ValueError
        struct.pack_into('>H', self.data, address, value)

    def get_header(self):
        return self.header

    def get_object_table(self):
        return self.object_table


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
        return self.heap.read_word(0x1A) # TODO: multiply by version-dependant constant

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


class ObjectTable:
    def __init__(self, heap):
        self.heap = heap
        self.header = self.heap.get_header()

    def get_default_property(self, property_number):
        object_table = self.header.get_object_table_location()
        #TODO: check for illegal property numbers
        return sel.heap.read_word(2 * (property_number - 1))

    def get_object_addr(self, object_number):
        #TODO: check for illegal object numbers
        version = self.header.get_z_version()
        object_table = self.header.get_object_table_location()

        if (version < 4):
            max_properties = 31
            object_size = 9
        else:
            max_properties = 63
            object_size = 14
        
        first_object = object_table + 2 * max_properties
        return first_object + object_size * (object_number - 1)

    def get_object_attribute(self, object_number, attribute_number):
        #TODO: check for illegal attribute numbers
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            if (attribute_number < 16):
                is_set = self.heap.read_word(object_addr) &     (1 << (15 - attribute_number))
            else:
                is_set = self.heap.read_word(object_addr + 2) & (1 << (31 - attribute_number))
        else:
            if (attribute_number < 16):
                is_set = self.heap.read_word(object_addr) &     (1 << (15 - attribute_number))
            elif (attribute_number < 32):
                is_set = self.heap.read_word(object_addr + 2) & (1 << (31 - attribute_number))
            else:
                is_set = self.heap.read_word(object_addr + 4) & (1 << (47 - attribute_number))

        if (is_set):
            return True
        else:
            return False

    def get_object_parent(self, object_number):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            parent = self.heap.read_byte(object_addr + 4)
        else:
            parent = self.heap.read_word(object_addr + 6)

        logger.debug("parent of %d is %d" % (object_number, parent))
        return parent

    def get_object_sibling(self, object_number):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            sibling = self.heap.read_byte(object_addr + 5)
        else:
            sibling = self.heap.read_word(object_addr + 8)

        return sibling

    def get_object_child(self, object_number):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            child = self.heap.read_byte(object_addr + 6)
        else:
            child = self.heap.read_word(object_addr + 10)

        return child

    def get_object_properties_table(self, object_number):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            properties_table = self.heap.read_word(object_addr + 7)
        else:
            properties_table = self.heap.read_word(object_addr + 12)

        return properties_table

    def get_object_short_name(self, object_number):
        properties_table = self.get_object_properties_table(object_number)
        short_name_words = self.heap.read_byte(properties_table)
        addr = properties_table + 1
        string = zstring.ZString()
        while(string.add(self.heap.read_word(addr))):
            addr += 2
        #print short_name_words
        return string

    def get_property_number(self, property_addr):
        version = self.header.get_z_version()
        size_byte = self.heap.read_byte(property_addr)

        if (version < 4):
            number = size_byte & 0x1f
        else:
            number = size_byte & 0x3f
        return number

    def get_property_length(self, property_addr):
        version = self.header.get_z_version()
        size_byte = self.heap.read_byte(property_addr)
        offset = 1

        if (version < 4):
            size = (size_byte >> 5) + 1
        else:
            if (size_byte & 128):
                size_byte = self.heap.read_byte(property_addr + 1)
                offset = 2
                size = size_byte & 0x3f
                if (size == 0):
                    size = 64
            else:
                size = (size_byte >> 6) + 1

        return (offset, size)

    def get_property_addr(self, object_number, property_number):
        #TODO: check for illegal property numbers
        version = self.header.get_z_version()
        properties_table = self.get_object_properties_table(object_number)
        short_name_words = self.heap.read_byte(properties_table)

        property_addr = properties_table + 1 + 2 * short_name_words
        number = self.get_property_number(property_addr)
        while (number > 0):
            offset, size = self.get_property_length(property_addr)

            logger.debug("%d %d %d %d" % (property_addr, number, offset, size))
            if (number == property_number):
                return property_addr
            else:
                property_addr += offset + size
                number = self.get_property_number(property_addr)
        
        return 0

    def get_property(self, object_number, property_number):
        property_addr = self.get_property_addr(object_number, property_number)
        offset, size = self.get_property_length(property_addr)
        
        if (size == 1):
            return self.heap.read_byte(property_addr + offset)
        elif (size == 2):
            return self.heap.read_word(property_addr + offset)
        else:
            print 'ERROR: size > 2. get_prop undefined.'




