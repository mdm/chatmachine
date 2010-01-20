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

    def get_num_locals(self):
        return len(self.locals[-1])

    def set_num_locals(self, num_locals):
        self.locals[-1] = [0] * num_locals
        #print self.locals

    def push_call(self, return_address, result_variable, arg_count):
	self.stack.append([])
	self.locals.append([])
        self.calls.append((return_address, result_variable, arg_count, frame_start))
	
    def pop_call(self):
	self.stack.pop()
	self.locals.pop()
	return self.calls.pop()

    def print_me(self):
	print self.frame_start, self.stack

