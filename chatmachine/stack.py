import array

class Stack:
    def __init__(self):
    	self.stack = [[]]
        self.locals = [[]]
        self.calls = []

    def push(self, value):
    	self.stack[-1].append(value)

    def pop(self):
        return self.stack[-1].pop()

    def peek(self):
        return self.stack[-1][-1]

    def get_size(self):
    	return len(self.stack[-1])

    def get_local(self, var_nr):
    	return self.locals[-1][var_nr]

    def set_local(self, var_nr, value):
    	self.locals[-1][var_nr] = value

#    def get_num_locals(self):
#        return len(self.locals[-1])
#
#    def set_num_locals(self, num_locals):
#        self.locals[-1] = [0] * num_locals
#        #print self.locals

    def push_call(self, init_locals, return_address, result_variable, arg_count):
    	self.stack.append([])
    	self.locals.append(init_locals)
        self.calls.append((return_address, result_variable, arg_count))
	
    def pop_call(self):
	    self.stack.pop()
	    self.locals.pop()
	    return self.calls.pop()

    def print_current(self):
        print len(self.stack), self.stack[-1]
        print len(self.locals), self.locals[-1]
        print len(self.calls), self.calls[-1]

    def print_all(self):
        print len(self.stack), self.stack
        print len(self.locals), self.locals
        print len(self.calls), self.calls

    def serialize(self):
        result = array.array('B')
        for i in range(6):
            result.append(0)
        result.append(len(self.stack[0]) >> 8)
        result.append(len(self.stack[0]) & 0xFF)
        for elem in self.stack[0]:
            result.append(elem >> 8)
            result.append(elem & 0xFF)
        for i in range(len(self.calls)):
            return_address, result_variable, arg_count = self.calls[i]
            result.append(return_address >> 16)
            result.append((return_address >> 8) & 0xFF)
            result.append(return_address & 0xFF)
            if result_variable == None:
                result.append((1 << 4) + len(self.locals[i + 1]))
                result.append(0)
            else:
                result.append(len(self.locals[i + 1]))
                result.append(result_variable)
            args = 0
            for j in range(arg_count):
                args += 1 << j
            result.append(args)
            result.append(len(self.stack[i + 1]) >> 8)
            result.append(len(self.stack[i + 1]) & 0xFF)
            for value in self.locals[i + 1]:
                result.append(value >> 8)
                result.append(value & 0xFF)
            for value in self.stack[i + 1]:
                result.append(value >> 8)
                result.append(value & 0xFF)
        return result

    @classmethod
    def deserialize(cls, serialized):
        result = cls()
        pos = 0
        while pos < len(serialized):
            return_address = (serialized[pos] << 16) + (serialized[pos + 1] << 8) + serialized[pos + 2]
            pos += 3
            num_locals = serialized[pos] & 0xF
            if serialized[pos] & (1 << 4):
                result_variable = None
            else:
                result_variable = serialized[pos + 1]
            pos += 2
            arg_count = 0
            for i in range(7):
                if serialized[pos] & (1 << i):
                    arg_count += 1
            pos += 1
            if not return_address == 0:
                result.push_call([0] * num_locals, return_address, result_variable, arg_count)
            num_words = (serialized[pos] << 8) + serialized[pos + 1]
            pos += 2
            for i in range(num_locals):
                result.set_local(i, (serialized[pos] << 8) + serialized[pos + 1])
                pos += 2
            for i in range(num_words):
                result.push((serialized[pos] << 8) + serialized[pos + 1])
                pos += 2
        return result
        
