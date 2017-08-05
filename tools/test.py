import timeit


def print_char(i):
    print(chr(i))
    
def do_if_inline(i):
    if (i == 65):
        print(chr(65))
    elif (i == 66):
        print(chr(66))
    elif (i == 67):
        print(chr(67))
    elif (i == 68):
        print(chr(68))
    elif (i == 69):
        print(chr(69))
    elif (i == 70):
        print(chr(70))
    elif (i == 71):
        print(chr(71))
    elif (i == 72):
        print(chr(72))
    elif (i == 73):
        print(chr(73))
    elif (i == 74):
        print(chr(74))
    elif (i == 75):
        print(chr(75))
    elif (i == 76):
        print(chr(76))
    elif (i == 77):
        print(chr(77))
    elif (i == 78):
        print(chr(78))
    elif (i == 79):
        print(chr(79))
    elif (i == 80):
        print(chr(80))

def do_if_call(i):
    if (i == 65):
        print_char(65)
    elif (i == 66):
        print_char(66)
    elif (i == 67):
        print_char(67)
    elif (i == 68):
        print_char(68)
    elif (i == 69):
        print_char(69)
    elif (i == 70):
        print_char(70)
    elif (i == 71):
        print_char(71)
    elif (i == 72):
        print_char(72)
    elif (i == 73):
        print_char(73)
    elif (i == 74):
        print_char(74)
    elif (i == 75):
        print_char(75)
    elif (i == 76):
        print_char(76)
    elif (i == 77):
        print_char(77)
    elif (i == 78):
        print_char(78)
    elif (i == 79):
        print_char(79)
    elif (i == 80):
        print_char(80)

lut_dict = {65:print_char, 66:print_char, 67:print_char, 68:print_char, 69:print_char, 70:print_char, 71:print_char, 72:print_char, 73:print_char, 74:print_char, 75:print_char, 76:print_char, 77:print_char, 78:print_char, 79:print_char, 80:print_char}

def do_lut_dict(i):
    lut_dict[i](i)

lut_list = [print_char] * 16

def do_lut_list(i):
    lut_list[i - 65](i)


last = [80] * 10

time_reference = timeit.Timer('for i in range(10): print_char(80)', 'from __main__ import *').timeit()
time_if_inline = timeit.Timer('for i in last: do_if_inline(i)', 'from __main__ import *').timeit()
time_if_call = timeit.Timer('for i in last: do_if_call(i)', 'from __main__ import *').timeit()
time_lut_dict = timeit.Timer('for i in last: do_lut_dict(i)', 'from __main__ import *').timeit()
time_lut_list = timeit.Timer('for i in last: do_lut_list(i)', 'from __main__ import *').timeit()

print()
print(time_reference, time_if_inline, time_if_call, time_lut_dict, time_lut_list)

