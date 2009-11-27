import unittest
import ctypes
import os.path

import heap

class TestHeap(unittest.TestCase):
    def setUp(self):
        self.bronze = heap.Heap('Bronze.z8')
        self.curses = heap.Heap('curses.z5')
        self.zork1 = heap.Heap('zork1.z5')

    def compare_contents(self, first, second):
        for i in range(len(first)):
            if not first[i] == second[i]:
                return False
        return True

    def test_init(self):
        self.assertTrue(self.compare_contents(self.bronze.data, ctypes.create_string_buffer(open('Bronze.z8').read())))
        self.assertTrue(self.compare_contents(self.curses.data, ctypes.create_string_buffer(open('curses.z5').read())))
        self.assertTrue(self.compare_contents(self.zork1.data, ctypes.create_string_buffer(open('zork1.z5').read())))

        self.assertFalse(self.compare_contents(self.bronze.data, ctypes.create_string_buffer(open('zork1.z5').read())))

    def test_read_byte(self):
        bytes = [0x36, 0x2E, 0x33, 0x30, 0x80, 0x00, 0x94, 0xA5, 0x00, 0x00, 0x80, 0xA5, 0x00, 0x00, 0x00, 0x00]
        for i in range(len(bytes)):
            self.assertEquals(bytes[i], self.bronze.read_byte(0x3C + i))

        filesize = os.path.getsize('Bronze.z8')
        self.assertRaises(IndexError, self.bronze.read_byte, filesize)
        self.assertRaises(IndexError, self.bronze.read_byte, -1)

    def test_write_byte(self):
        self.bronze.write_byte(0x3C, 0x88)
        self.assertEquals(self.bronze.read_byte(0x3C), 0x88)

        self.assertRaises(ValueError, self.bronze.write_byte, 0x3C, 0x100)
        self.assertRaises(ValueError, self.bronze.write_byte, 0x3C, -1)

        filesize = os.path.getsize('Bronze.z8')
        self.assertRaises(IndexError, self.bronze.write_byte, filesize, 0xFF)
        self.assertRaises(IndexError, self.bronze.write_byte, -1, 0xFF)

    def test_read_word(self):
        words = [0x362E, 0x3330, 0x8000, 0x94A5, 0x0000, 0x80A5, 0x0000, 0x0000]
        for i in range(len(words)):
            self.assertEquals(words[i], self.bronze.read_word(0x3C + 2 * i))

        filesize = os.path.getsize('Bronze.z8')
        self.assertRaises(IndexError, self.bronze.read_word, filesize - 1)
        self.assertRaises(IndexError, self.bronze.read_word, -1)

    def test_write_word(self):
        self.bronze.write_word(0x3C, 0x11ff)
        self.assertEquals(self.bronze.read_word(0x3C), 0x11ff)

        self.assertRaises(ValueError, self.bronze.write_word, 0x3C, 0x10000)
        self.assertRaises(ValueError, self.bronze.write_word, 0x3C, -1)

        filesize = os.path.getsize('Bronze.z8')
        self.assertRaises(IndexError, self.bronze.write_word, filesize - 1, 0xFFFF)
        self.assertRaises(IndexError, self.bronze.write_word, -1, 0xFFFF)

    def test_get_header(self):
        self.fail()

    def test_get_object_table(self):
        self.fail()


class TestHeader(unittest.TestCase):
    def setUp(self):
        bronze = heap.Heap('Bronze.z8')
        curses = heap.Heap('curses.z5')
        etude = heap.Heap('etude.z5')

    def test_get_z_version(self):
        self.fail()


class TestObjectTable(unittest.TestCase):
    def setUp(self):
        bronze = heap.Heap('Bronze.z8')
        curses = heap.Heap('curses.z5')
        etude = heap.Heap('etude.z5')

if __name__ == '__main__':
    unittest.main()


