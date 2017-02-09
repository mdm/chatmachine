import array

class MemoryV1:
    def __init__(self, filename):
        self.story_filename = filename
        story_file = open(self.story_filename)
        self.data = array.array('B', story_file.read())
        story_file.close()
        self.header = HeaderV1(self)
        self.object_table = ObjectTableV1(self)
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

    def compress(self):
        story_file = open(self.story_filename)
        original_data = array.array('B', story_file.read())
        story_file.close()
        result = array.array('B')
        run = 0
        for original, current in zip(original_data, self.data):
            diff = original ^ current
            if diff == 0:
                run += 1
                if run == 255:
                    result.append(0)
                    result.append(run)
                    run = 0
            else:
                if run > 0:
                    result.append(0)
                    result.append(run)
                run = 0
                result.append(diff)
        if run > 0:
            result.append(0)
            result.append(run)
        return result

    def uncompress(self, compressed):
        story_file = open(self.story_filename)
        original_data = array.array('B', story_file.read())
        story_file.close()
        backup = self.data
        self.data = array.array('B')
        pos_original = 0
        pos_compressed = 0
        while pos_compressed < len(compressed):
            if compressed[pos_compressed] == 0:
                for i in range(compressed[pos_compressed + 1]):
                    self.data.append(original_data[pos_original + i])
                pos_original += compressed[pos_compressed + 1]
                pos_compressed += 2
            else:
                self.data.append(compressed[pos_compressed] ^ original_data[pos_original])
                pos_original += 1
                pos_compressed += 1
        while pos_original < len(original_data):
            self.data.append(original_data[pos_original])
            pos_original += 1


    def decode_zscii(self, code):
        #if (code == 0):
        char = ''
        if (code == 13):
            char = '\\n'
        elif (32 <= code <= 126):
            char = chr(code)
        elif (155 <= code <= 251):
            #TODO: implement default unicode table
            char = '?'
        return char
    
    def decode_string(self, address, newline):
        #TODO: cache alphabets somewhere
        alphabets = [list('abcdefghijklmnopqrstuvwxyz'), list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), list(' 0123456789.,!?_#\'\"/\\<-:()')]
        previous = 0
        current = 0
        constructing = -2 # nice hack from gnusto: -2: not constructing multi-zchar zscii, -1: constructing, n>=0: read 1 byte
        zscii = []
        zchars = []
        while True:
            word = self.read_word(address)
            zchars.extend([(word & 0x7c00) >> 10, (word & 0x3e0) >> 5, word & 0x1f])
            address += 2
            if (word & 0x8000):
                break
        for zchar in zchars:
            if (constructing == -2):
                if (zchar == 0):
                    zscii.append(' ')
                elif (zchar == 1):
                    zscii.append(newline)
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
                    zscii.append(alphabets[current][zchar - 6])
                    current = previous
            elif (constructing == -1):
                constructing = zchar << 5
            else:
                code = constructing + zchar
                zscii.append(self.decode_zscii(code))
                current = previous
                constructing = -2
        return ''.join(zscii), address

    def dump_string(self, address):
        zchars = []
        while True:
            word = self.read_word(address)
            zchars.extend([(word & 0x7c00) >> 10, (word & 0x3e0) >> 5, word & 0x1f])
            address += 2
            if (word & 0x8000):
                break
        print zchars
    
    def tokenize(self, text, parse, dictionary = None, flag = False):
        if dictionary == None:
            dictionary = self.get_default_dictionary()
        separators = dictionary.get_word_separators()
        words = []
        current = []
        pos = 1
        start = pos
        #print self.read_byte(text + 1)
        char = chr(self.read_byte(text + pos))
        while not char == '\0':
            if char == ' ':
                if len(current) > 0:
                    words.append((start, ''.join(current)))
                    current = []
                start = pos + 1
            elif char in separators:
                if len(current) > 0:
                    words.append((start, ''.join(current)))
                    current = []
                words.append((pos, char))
                start = pos + 1
            else:
                current.append(char)
            pos += 1
            char = chr(self.read_byte(text + pos))
        if len(current) > 0:
            words.append((start, ''.join(current)))
        alphabet2 = ' 0123456789.,!?_#\'\"/\\<-:()'
        #alphabet2[17] = '\\\''
        #alphabet2[18] = '\\\"'
        #alphabet2[20] = '\\\\'
        #print '@@@', words, alphabet2
        #words = [(0, 'pdp10'), (1, 'r2d2'), (2, 'test'), (3, 'longtest'), (4, 'storm-')]
        #print '$$$', words
        words = words[:self.read_byte(parse)]
        #print '$$$', words, self.read_byte(parse)
        self.write_byte(parse + 1, len(words)) #TODO: handle security?
        token = []
        shifting = -1
        pos = 2
        for word in words:
            #print '***', word
            for char in word[1]:
                index = alphabet2.find(char)
                if index > -1:
                    if shifting > -1:
                        token[shifting] = 5
                    else:
                        shifting = len(token)
                        token.append(3)
                    token.append(index + 6)
                else:
                    shifting = -1
                    token.append(ord(char) - 97 + 6)
            token = token[:6]
            token.extend([5]  * (6 - len(token)))
            encoded = [(token[0] << 10) + (token[1] << 5) + token[2], (token[3] << 10) + (token[4] << 5) + token[5]]
            if not token[5] == 3:
                encoded[1] = encoded[1] | 0x8000
            #print token, encoded
            address = 0
            for i in range(1, abs(dictionary.get_num_entries()) + 1): # optimize for sorted dicts
                entry = dictionary.get_encoded_string(i)
                #print self.decode_string(dictionary.get_entry_addr(i))
                #print '!!!', entry, word
                if entry[0] == encoded[0] and entry[1] == encoded[1]:
                    address = dictionary.get_entry_addr(i)
                    break
            #print '!!!', hex(address), len(word[1]), word[0]
            self.write_word(parse + pos, address)
            self.write_byte(parse + pos + 2, len(word[1]))
            self.write_byte(parse + pos + 3, word[0])
            pos += 4
            token = []
            

    def get_header(self):
        return self.header

    def get_object_table(self):
        return self.object_table

    def get_default_dictionary(self):
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
        return bool(self.memory.read_word(0x10) & 1)

    def set_flag_transcript(self):
        self.memory.write_word(0x10, self.memory.read_word(0x10) | 1)
        
    def get_standard_revision_number(self):
        return self.memory.read_word(0x32)

    def set_standard_revision_number(self, value):
        self.memory.write_word(0x32, value)


class ObjectTableV1:
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
        
    def unlink_object(self, object_number):
        parent = self.get_object_parent(object_number)
        self.set_object_parent(object_number, 0)
        if not parent == 0:
            parent_first_child = self.get_object_child(parent)
            next_sibling = self.get_object_sibling(object_number)
            self.set_object_sibling(object_number, 0)
            if (parent_first_child == object_number):
                self.set_object_child(parent, next_sibling)
            else:
                previous_sibling = parent_first_child
                previous_sibling_sibling = self.get_object_sibling(previous_sibling)
                while not previous_sibling_sibling == object_number:
                    previous_sibling = previous_sibling_sibling
                    previous_sibling_sibling = self.get_object_sibling(previous_sibling)
                self.set_object_sibling(previous_sibling, next_sibling)

    def get_object_properties_table(self, object_number):
        object_addr = self.get_object_addr(object_number)
        properties_table = self.memory.read_word(object_addr + 7)
        return properties_table

    def get_object_short_name(self, object_number):
        properties_table = self.get_object_properties_table(object_number)
        #short_name_words = self.memory.read_byte(properties_table)
        return self.memory.decode_string(properties_table + 1, '\n')[0]

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

    def get_next_property_number(self, object_number, property_number):
        #TODO: check for illegal property numbers
        #TODO: use binary search
        properties_table = self.get_object_properties_table(object_number)
        short_name_words = self.memory.read_byte(properties_table)

        property_info_addr = properties_table + 1 + 2 * short_name_words
        number, size = self.get_property_info_forwards(property_info_addr)
        
        if (property_number == 0):
            return number
        else:
            while (number > 0):
                old_number = number
                property_info_addr += size + 1
                number, size = self.get_property_info_forwards(property_info_addr)
                if (old_number == property_number):
                    return number
        
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
        separators = []
        for i in range(num_separators):
            separators.append(chr(self.memory.read_byte(self.location + i + 1)))
        return separators

    def get_entry_length(self):
        return self.entry_length
    
    def get_num_entries(self):
        return self.num_entries

    def get_entry_addr(self, number): # this is 1-based
        return self.first_entry + (number - 1) * self.entry_length

    def get_encoded_string(self, number): # this is 1-based
        addr = self.get_entry_addr(number)
        #print '%%%', self.memory.decode_string(addr)
        encoded = []
        for i in range(2):
                encoded.append(self.memory.read_word(addr + i * 2))
        return encoded

