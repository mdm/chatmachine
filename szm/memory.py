#import struct
#import ctypes
import array
import logging

import zstring

logger = logging.getLogger('memory')
logger.setLevel(logging.WARNING)

class Memory:
    def __init__(self, filename):
        story_file = open(filename)
        #self.data = ctypes.create_string_buffer(story_file.read())
        self.data = array.array('B', story_file.read())
        self.header = Header(self)
        self.object_table = ObjectTable(self)
        self.dictionary = Dictionary(self, self.header.get_dictionary_location())

    def read_byte(self, address):
        #if not (0 <= address < len(self.data)): raise IndexError
        #byte = struct.unpack_from('B', self.data, address)[0]
        #logger.debug("read [%02X]" % byte)
        #return byte
        return self.data[address]

    def write_byte(self, address, value):
        #if not (0 <= address < len(self.data)): raise IndexError
        #if not (0 <= value <= 0xFF): raise ValueError
        #struct.pack_into('B', self.data, address, value)
        self.data[address] = value

    def read_word(self, address):
        #if not (0 <= address < (len(self.data) - 1)): raise IndexError
        #word = struct.unpack_from('>H', self.data, address)[0]
        #logger.debug("read [%04X]" % word)
        #return word
        return (self.data[address] << 8) + self.data[address + 1]

    def write_word(self, address, value):
        #if not (0 <= address < (len(self.data) - 1)): raise IndexError
        #if not (0 <= value <= 0xFFFF): raise ValueError
        #struct.pack_into('>H', self.data, address, value)
        self.data[address] = value >> 8
        self.data[address + 1] = value & 0xFF

    def read_string(self, address):
        words = []
        words.append(self.read_word(address))
        while not (words[-1] & 0x8000):
            address += 2
            words.append(self.read_word(address))
        string = zstring.ZString()
        string.unpack_words(words)
        return (address + 2), string.decode()

    def get_header(self):
        return self.header

    def get_object_table(self):
        return self.object_table

    def get_dictionary(self):
        return self.dictionary
    
    def get_terminating_chars(self):
        chars = []
        addr = self.header.get_terminating_chars_table_location()
        char = self.read_byte(addr)
        while (char > 0):
            chars.append(char)
            addr += 1
            char = self.read_byte(addr)


class Header:
    #STATUS_TYPE, FILE_SPLIT, STATUS_AVAILABLE, SCREEN_SPLIT_AVAILABLE, VARIABLE_DEFAULT_FONT = 1, 2, 4, 5, 6
    def __init__(self, heap):
        self.heap = heap

    def get_z_version(self):
        return self.heap.read_byte(0x0)

    def get_flags1(self):
        return self.heap.read_byte(0x1)

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
    
    def set_flags1_v3(self, use_score, has_two_discs, do_censor, has_no_statusline, has_screen_splitting, has_variable_pitch_default_font):
        self.heap.write_byte(0x1, value)

    def set_flags1_v458(self, has_colors, has_pictures, has_boldface, has_italic, has_monospace, has_sound, has_timed_input):
        self.heap.write_byte(0x1, value)

    def set_flags2(self, do_transcript, do_redraw_statusline, use_pictures, use_undo, use_mouse, use_colors, use_sound, use_menus):
        self.heap.write_byte(0x1, value)

    # flags

    #def set_has_status_line


class ObjectTable:
    def __init__(self, heap):
        self.heap = heap
        self.header = self.heap.get_header()

    def get_default_property_data(self, property_number):
        object_table = self.header.get_object_table_location()
        #TODO: check for illegal property numbers
        return self.heap.read_word(object_table + 2 * (property_number - 1))

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
                is_set = self.heap.read_word(object_addr) & (1 << (15 - attribute_number))
            else:
                is_set = self.heap.read_word(object_addr + 2) & (1 << (31 - attribute_number))
        else:
            if (attribute_number < 16):
                is_set = self.heap.read_word(object_addr) & (1 << (15 - attribute_number))
            elif (attribute_number < 32):
                is_set = self.heap.read_word(object_addr + 2) & (1 << (31 - attribute_number))
            else:
                is_set = self.heap.read_word(object_addr + 4) & (1 << (47 - attribute_number))

        if (is_set):
            return True
        else:
            return False

    def set_object_attribute(self, object_number, attribute_number):
        #TODO: check for illegal attribute numbers
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            if (attribute_number < 16):
                self.heap.write_word(object_addr, self.heap.read_word(object_addr) | (1 << (15 - attribute_number)))
            else:
                self.heap.write_word(object_addr + 2, self.heap.read_word(object_addr + 2) | (1 << (31 - attribute_number)))
        else:
            if (attribute_number < 16):
                self.heap.write_word(object_addr, self.heap.read_word(object_addr) | (1 << (15 - attribute_number)))
            elif (attribute_number < 32):
                self.heap.write_word(object_addr + 2, self.heap.read_word(object_addr + 2) | (1 << (31 - attribute_number)))
            else:
                self.heap.write_word(object_addr + 4, self.heap.read_word(object_addr + 4) | (1 << (47 - attribute_number)))

    def clear_object_attribute(self, object_number, attribute_number):
        #TODO: check for illegal attribute numbers
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            if (attribute_number < 16):
                self.heap.write_word(object_addr, self.heap.read_word(object_addr) & ~(1 << (15 - attribute_number)))
            else:
                self.heap.write_word(object_addr + 2, self.heap.read_word(object_addr + 2) & ~(1 << (31 - attribute_number)))
        else:
            if (attribute_number < 16):
                self.heap.write_word(object_addr, self.heap.read_word(object_addr) & ~(1 << (15 - attribute_number)))
            elif (attribute_number < 32):
                self.heap.write_word(object_addr + 2, self.heap.read_word(object_addr + 2) & ~(1 << (31 - attribute_number)))
            else:
                self.heap.write_word(object_addr + 4, self.heap.read_word(object_addr + 4) & ~(1 << (47 - attribute_number)))

    def get_object_parent(self, object_number):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            parent = self.heap.read_byte(object_addr + 4)
        else:
            parent = self.heap.read_word(object_addr + 6)

        logger.debug("parent of %d is %d" % (object_number, parent))
        return parent

    def set_object_parent(self, object_number, parent):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            self.heap.write_byte(object_addr + 4, parent)
        else:
            self.heap.write_word(object_addr + 6, parent)

        logger.debug("parent of %d is %d" % (object_number, parent))

    def get_object_sibling(self, object_number):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            sibling = self.heap.read_byte(object_addr + 5)
        else:
            sibling = self.heap.read_word(object_addr + 8)

        return sibling

    def set_object_sibling(self, object_number, sibling):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            self.heap.write_byte(object_addr + 5, sibling)
        else:
            self.heap.write_word(object_addr + 8, sibling)

    def get_object_child(self, object_number):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            child = self.heap.read_byte(object_addr + 6)
        else:
            child = self.heap.read_word(object_addr + 10)

        return child

    def set_object_child(self, object_number, child):
        version = self.header.get_z_version()
        object_addr = self.get_object_addr(object_number)

        if (version < 4):
            self.heap.write_byte(object_addr + 6, child)
        else:
            self.heap.write_word(object_addr + 10, child)

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

    def get_property_info_forwards(self, property_info_addr):
        version = self.header.get_z_version()
        size_byte = self.heap.read_byte(property_info_addr)

        if (version < 4):
            number = size_byte & 0x1f
        else:
            number = size_byte & 0x3f
        
        if (version < 4):
            size = (size_byte >> 5) + 1
        else:
            if (size_byte & 128):
                size_byte = self.heap.read_byte(property_info_addr + 1)
                size = size_byte & 0x3f
                if (size == 0):
                    size = 64
                elif (size < 3):
                    print 'WARNING: Property', number, 'has size', size, 'encoded as two bytes!'
            else:
                size = (size_byte >> 6) + 1

        return (number, size)

    def get_property_info_backwards(self, property_data_addr):
        version = self.header.get_z_version()
        size_byte = self.heap.read_byte(property_data_addr - 1)

        if (version < 4):
            size = (size_byte >> 5) + 1
        else:
            if (size_byte & 128):
                size = size_byte & 0x3f
                if (size == 0):
                    size = 64
                elif (size < 3):
                    print 'WARNING: Property', number, 'has size', size, 'encoded as two bytes!'
                size_byte = self.heap.read_byte(property_data_addr - 2)
            else:
                size = (size_byte >> 6) + 1

        if (version < 4):
            number = size_byte & 0x1f
        else:
            number = size_byte & 0x3f
        
        return (number, size)

    def get_property_data_addr(self, object_number, property_number):
        #TODO: check for illegal property numbers
        version = self.header.get_z_version()
        properties_table = self.get_object_properties_table(object_number)
        logger.debug("Properties table at %04X." % properties_table)
        short_name_words = self.heap.read_byte(properties_table)

        property_info_addr = properties_table + 1 + 2 * short_name_words
        number, size = self.get_property_info_forwards(property_info_addr)
        while (number > 0):
            logger.debug("%d %d %d" % (property_info_addr, number, size))
            if (number == property_number):
                if (version < 4) or (size < 3):
                    return property_info_addr + 1
                else:
                    return property_info_addr + 2
            else:
                if (version < 4) or (size < 3):
                    property_info_addr += size + 1
                else:
                    property_info_addr += size + 2
                number, size = self.get_property_info_forwards(property_info_addr)
        
        logger.warning("Object %d doesn't have property %d." % (object_number, property_number))
        return 0

    def get_property_data(self, object_number, property_number):
        property_data_addr = self.get_property_data_addr(object_number, property_number)

        if (property_data_addr == 0):
            return self.get_default_property_data(property_number)
        else:
            number, size = self.get_property_info_backwards(property_data_addr)
            if (size == 1):
                return self.heap.read_byte(property_data_addr)
            elif (size == 2):
                return self.heap.read_word(property_data_addr)
            else:
                print 'ERROR: size > 2. get_prop undefined.'

    def set_property_data(self, object_number, property_number, value):
        property_data_addr = self.get_property_data_addr(object_number, property_number)
        number, size = self.get_property_info_backwards(property_data_addr)
        
        if (size == 1):
            self.heap.write_byte(property_data_addr, value)
        elif (size == 2):
            self.heap.write_word(property_data_addr, value)
        else:
            print 'ERROR: size > 2. set_prop undefined.'
    
    def dump_dot_file(self, filename, num_objects):
        dotfile = open(filename, 'wb')
        dotfile.write("digraph object_tree {\n")
        for obj in range(1, num_objects + 1):
            dotfile.write("    %d;\n" % obj)
            parent = self.get_object_parent(obj)
            if (parent > 0):
                dotfile.write("    %d -> %d [style=dotted, color=red];\n" % (obj, parent))
            child = self.get_object_child(obj)
            if (child > 0):
                dotfile.write("    %d -> %d [color=green];\n" % (obj, child))
            sibling = self.get_object_sibling(obj)
            if (sibling > 0):
                dotfile.write("    %d -> %d [color=blue];\n" % (obj, sibling))
        dotfile.write("}\n")
        dotfile.close()


class Dictionary:
    def __init__(self, heap, location):
        self.heap = heap
        self.header = self.heap.get_header()
        self.location = location
        location += self.heap.read_byte(location) + 1
        self.entry_length = self.heap.read_byte(location)
        self.num_entries = self.heap.read_word(location + 1)
        self.first_entry = location + 3

    def get_word_separators(self):
        num_separators = self.heap.read_byte(self.location)
        separators = ''
        for i in range(num_separators):
            separators += chr(self.heap.read_byte(self.location + i + 1))
        return separators

    def get_num_entries(self):
        return self.num_entries

    def get_entry_addr(self, number): # this is 1-based
        return self.first_entry + (number - 1) * self.entry_length

    def get_encoded_text(self, number): # this is 1-based
        version = self.header.get_z_version()
        addr = self.get_entry_addr(number)
        encoded = []
        if (version < 4):
            for i in range(2):
                encoded.append(self.heap.read_word(addr + i * 2))
        else:
            for i in range(3):
                encoded.append(self.heap.read_word(addr + i * 2))
        return encoded

