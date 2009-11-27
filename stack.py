class Stack:
    def __init__(self):
	self.stack = []
	self.frame_start = 0 # first index after frame header

    def push(self, value):
	self.stack.append(value)

    def pop(self):
	if (len(self.stack) <= self.frame_start):
	    print 'Illegal stack pop.'
	else:
	    return self.stack.pop()

    def get_size(self):
	return len(self.stack)

    def get_value(self, frame_offset):
	return self.stack[self.frame_start + frame_offset]

    def set_value(self, frame_offset, value):
	self.stack[self.frame_start + frame_offset] = value

    def push_frame(self, return_address, result_variable, num_locals, num_args):
	# pushing frame header
	self.push((return_address, result_variable, num_locals, num_args))
	self.push(self.frame_start)
	self.frame_start = len(self.stack)
	#self.print_me()
	
    def pop_frame(self):
	self.rewind(self.frame_start)
	self.frame_start = self.stack.pop()
	return self.stack.pop()

    def rewind(self, target_size):
	self.stack = self.stack[:target_size]

    def print_me(self):
	print self.frame_start, self.stack
