import unittest

import szm.memory

class TestMemory(unittest.TestCase):
    def setUp(self):
        self.data = szm.memory.Memory('data/Bronze.z5')

    def test_read_byte_first(self):
        self.assertEquals(0x08, self.data.read_byte(0))

    def test_read_byte_middle(self):
        self.assertEquals(0xa5, self.data.read_byte(0xffff))

    def test_read_byte_last(self):
        self.assertEquals(0x00, self.data.read_byte(0x57bff))

    def test_write_byte(self):
        self.data.write_byte(0xffff, 0xff)
        self.assertEquals(self.data.read_byte(0xffff), 0xff)

    def test_read_word(self):
        self.assertEquals(0xa541, self.data.read_word(0xffff))

    def test_write_word(self):
        self.data.write_word(0xffff, 0x11ff)
        self.assertEquals(self.data.read_word(0xffff), 0x11ff)

    def test_read_string(self):
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
        self.header = szm.memory.Memory('data/Bronze.z5').get_header()

    def test_get_z_version(self):
	    self.assertEquals(self.header.get_z_version(), 8)


class TestObjectTable(unittest.TestCase):
    def setUp(self):
        self.object_table = szm.memory.Memory('Bronze.z8').get_object_table()


