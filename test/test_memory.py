import unittest

import chatmachine.vm.memory

class TestMemory(unittest.TestCase):
    def setUp(self):
        self.data = chatmachine.vm.memory.MemoryV1('data/zork1-5.z5')

    def test_read_byte_first(self):
        self.assertEquals(0x01, self.data.read_byte(0))

    def test_read_byte_last(self):
        self.assertEquals(0x45, self.data.read_byte(0x10000))

    def test_write_byte(self):
        self.data.write_byte(0xffff, 0xff)
        self.assertEquals(self.data.read_byte(0xffff), 0xff)

    def test_read_word(self):
        self.assertEquals(0x4520, self.data.read_word(0x10000))

    def test_write_word(self):
        self.data.write_word(0xffff, 0x11ff)
        self.assertEquals(self.data.read_word(0xffff), 0x11ff)

    def test_decode_string(self):
        self.data.dump_string(0xf304)
        string, address = self.data.decode_string(0xf304)
        print '##%s##%x' % (string, address)
        self.fail()

    def test_get_header(self):
        self.fail()
        
    def test_get_object_table(self):
        self.fail()

    def test_get_dictionary(self):
        self.fail()
        
    def test_get_terminating_chars(self):
        self.fail()

    
class TestHeader(unittest.TestCase):
    def setUp(self):
        self.header = chatmachine.vm.memory.MemoryV1('data/zork1-5.z5').get_header()

    def test_get_z_version(self):
	    self.assertEquals(self.header.get_z_version(), 1)


class TestObjectTable(unittest.TestCase):
    def setUp(self):
        self.object_table = chatmachine.vm.memory.Memory('data/zork1-5.z5').get_object_table()


