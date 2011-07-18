import array

class Memory:
    def __init__(self, filename):
        story_file = open(filename)
        #self.data = ctypes.create_string_buffer(story_file.read())
        self.data = array.array('B', story_file.read())
        self.header = HeaderV1(self)
        self.object_table = ObjectTable(self)
        self.dictionary = DictionaryV1(self, self.header.get_dictionary_location())

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

    def decode_zscii(self, code):
        if (code == 0):
            char = ''
        elif (code == 13):
            char = '\\n'
        elif (32 <= code <= 126):
            char = chr(code)
        elif (155 <= code <= 251):
            #TODO: implement default unicode table
            char = '?'
        return char
    
    def decode_string(self, address):
        #TODO: cache alphabets somewhere
        alphabets = [list('abcdefghijklmnopqrstuvwxyz'), list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), list(' 0123456789.,!?_#\'\"/\\<-:()')]
        alphabets[2][17] = '\\\''
        alphabets[2][17] = '\\\"'
        alphabets[2][20] = '\\\\'
        previous = 0
        current = 0
        constructing = -2 # nice hack from gnusto: -2: not constructing multi-zchar zscii, -1: constructing, n>=0: read 1 byte
        zscii = []
        while True:
            word = self.read_word(address)
            zchars = [(word & 0x7c00) >> 10, (word & 0x3e0) >> 5, word & 0x1f]
            for zchar in zchars:
                if (zchar == 0):
                    zscii.append(' ')
                elif (zchar == 1):
                    zscii.append('\\n')
                elif (zchar == 2):
                    previous = current
                    current = (current + 1) % 3
                elif (zchar == 3):
                    previous = current
                    current = (current + 2) % 3
                elif (zchar == 4):
                    current = (current + 1) % 3
                    previous = current
                elif (zchar == 5):
                    current = (current + 2) % 3
                    previous = current
                elif (current == 2) and (zchar == 6):
                    constructing = -1
                else:
                    if (constructing == -2):
                        zscii.append(alphabets[current][zchar - 6])
                        current = previous
                    elif (constructing == -1):
                        constructing = zchar << 5
                    else:
                        code = constructing + zchar
                        zscii.append(self.decode_zscii(code))
            address += 2
            if (word & 0x8000):
                break
                
        return ''.join(zscii), address

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


class HeaderV1:
    #STATUS_TYPE, FILE_SPLIT, STATUS_AVAILABLE, SCREEN_SPLIT_AVAILABLE, VARIABLE_DEFAULT_FONT = 1, 2, 4, 5, 6
    def __init__(self, memory):
        self.memory = memory

    def get_z_version(self):
        return self.memory.read_byte(0x0)

    def get_high_memory_base(self):
        return self.memory.read_word(0x4)

    def get_initial_pc(self):
        return self.memory.read_word(0x6)

    def get_dictionary_location(self):
        return self.memory.read_word(0x8)

    def get_object_table_location(self):
        return self.memory.read_word(0xA)

    def get_globals_table_location(self):
        return self.memory.read_word(0xC)

    def get_static_memory_base(self):
        return self.memory.read_word(0xE)

    def get_flag_transcript(self):
        return self.memory.read_word(0x10) & 0x100

    def set_flag_transcript(self):
        self.memory.read_word(0x10, self.memory.read_word(0x10) | 0x100)
        
    def get_standard_revision_number(self):
        return self.memory.read_word(0x32)

    def set_standard_revision_number(self, value):
        self.memory.write_word(0x32, value)


class ObjectTable:
    def __init__(self, memory):
        self.memory = memory
        self.header = self.memory.get_header()

    def get_default_property_data(self, property_number):
        object_table = self.header.get_object_table_location()
        #TODO: check for illegal property numbers
        return self.memory.read_word(object_table + 2 * (property_number - 1))

    def get_object_addr(self, object_number):
        #TODO: check for illegal object numbers
        object_table = self.header.get_object_table_location()

        max_properties = 31
        object_size = 9
        
        first_object = object_table + 2 * max_properties
        return first_object + object_size * (object_number - 1)

    def get_object_attribute(self, object_number, attribute_number):
        #TODO: check for illegal attribute numbers
        object_addr = self.get_object_addr(object_number)

        if (attribute_number < 16):
            is_set = self.memory.read_word(object_addr) & (1 << (15 - attribute_number))
        else:
            is_set = self.memory.read_word(object_addr + 2) & (1 << (31 - attribute_number))

        if (is_set):
            return True
        else:
            return False

    def set_object_attribute(self, object_number, attribute_number):
        #TODO: check for illegal attribute numbers
        object_addr = self.get_object_addr(object_number)
        
        if (attribute_number < 16):
            self.memory.write_word(object_addr, self.memory.read_word(object_addr) | (1 << (15 - attribute_number)))
        else:
            self.memory.write_word(object_addr + 2, self.memory.read_word(object_addr + 2) | (1 << (31 - attribute_number)))

    def clear_object_attribute(self, object_number, attribute_number):
        #TODO: check for illegal attribute numbers
        object_addr = self.get_object_addr(object_number)

        if (attribute_number < 16):
            self.memory.write_word(object_addr, self.memory.read_word(object_addr) & ~(1 << (15 - attribute_number)))
        else:
            self.memory.write_word(object_addr + 2, self.memory.read_word(object_addr + 2) & ~(1 << (31 - attribute_number)))

    def get_object_parent(self, object_number):
        object_addr = self.get_object_addr(object_number)
        return self.memory.read_byte(object_addr + 4)

    def set_object_parent(self, object_number, parent):
        object_addr = self.get_object_addr(object_number)
        self.memory.write_byte(object_addr + 4, parent)

    def get_object_sibling(self, object_number):
        object_addr = self.get_object_addr(object_number)
        return self.memory.read_byte(object_addr + 5)

    def set_object_sibling(self, object_number, sibling):
        object_addr = self.get_object_addr(object_number)
        self.memory.write_byte(object_addr + 5, sibling)

    def get_object_child(self, object_number):
        object_addr = self.get_object_addr(object_number)
        return self.memory.read_byte(object_addr + 6)

    def set_object_child(self, object_number, child):
        object_addr = self.get_object_addr(object_number)
        self.memory.write_byte(object_addr + 6, child)

    def get_object_properties_table(self, object_number):
        object_addr = self.get_object_addr(object_number)

        properties_table = self.memory.read_word(object_addr + 7)
        
        return properties_table

    def get_object_short_name(self, object_number):
        properties_table = self.get_object_properties_table(object_number)
        #short_name_words = self.memory.read_byte(properties_table)
        return self.memory.decode_string(properties_table + 1)[0]

    def get_property_info_forwards(self, property_info_addr):
        size_byte = self.memory.read_byte(property_info_addr)

        number = size_byte & 0x1f
        size = (size_byte >> 5) + 1

        return (number, size)

    def get_property_info_backwards(self, property_data_addr):
        size_byte = self.memory.read_byte(property_data_addr - 1)

        number = size_byte & 0x1f
        size = (size_byte >> 5) + 1
        
        return (number, size)

    def get_property_data_addr(self, object_number, property_number):
        #TODO: check for illegal property numbers
        #TODO: use binary search
        properties_table = self.get_object_properties_table(object_number)
        short_name_words = self.memory.read_byte(properties_table)

        property_info_addr = properties_table + 1 + 2 * short_name_words
        number, size = self.get_property_info_forwards(property_info_addr)
        while (number > 0):
            if (number == property_number):
                return property_info_addr + 1
            else:
                property_info_addr += size + 1
                number, size = self.get_property_info_forwards(property_info_addr)
        
        return 0

    def get_property_data(self, object_number, property_number):
        property_data_addr = self.get_property_data_addr(object_number, property_number)

        if (property_data_addr == 0):
            return self.get_default_property_data(property_number)
        else:
            number, size = self.get_property_info_backwards(property_data_addr)
            if (size == 1):
                return self.memory.read_byte(property_data_addr)
            elif (size == 2):
                return self.memory.read_word(property_data_addr)
            else:
                print 'ERROR: size > 2. get_prop undefined.'
                
    def set_property_data(self, object_number, property_number, value):
        property_data_addr = self.get_property_data_addr(object_number, property_number)
        number, size = self.get_property_info_backwards(property_data_addr)
        
        if (size == 1):
            self.memory.write_byte(property_data_addr, value)
        elif (size == 2):
            self.memory.write_word(property_data_addr, value)
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


class DictionaryV1:
    def __init__(self, memory, location):
        self.memory = memory
        self.header = self.memory.get_header()
        self.location = location
        location += self.memory.read_byte(location) + 1
        self.entry_length = self.memory.read_byte(location)
        self.num_entries = self.memory.read_word(location + 1)
        self.first_entry = location + 3

    def get_word_separators(self):
        num_separators = self.memory.read_byte(self.location)
        separators = ''
        for i in range(num_separators):
            separators += chr(self.memory.read_byte(self.location + i + 1))
        return separators

    def get_num_entries(self):
        return self.num_entries

    def get_entry_addr(self, number): # this is 1-based
        return self.first_entry + (number - 1) * self.entry_length

    def get_encoded_text(self, number): # this is 1-based
        addr = self.get_entry_addr(number)
        encoded = []
        for i in range(2):
                encoded.append(self.memory.read_word(addr + i * 2))
        return encoded
