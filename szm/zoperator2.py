class Operator(object):
    def __init(self, processor, function):
        self.processor = processor
        self.function = getattr(processor, function)
        self.operands = []
        self.result = None
        self.next = None
            
    def execute(self):
        self.result = self.function(self.operands)
    
    def next(self):
        return self.next

        
class Decorator(Operator):
    def __init__(self, operator):
        self.wrapped_operator = operator

        
class LoadDecorator(Decorator):
    def execute(self):
        value = internal_memory.read(variable)
        self.wrapped_operator.execute()
    
    def next(self):
        self.wrapped_operator.next()


class StoreDecorator(Decorator):
    def execute(self):
        internal_memory.write(variable, value)
        self.wrapped_operator.execute()

    def next(self):
        self.wrapped_operator.next()


class BranchDecorator(Decorator):
    def execute(self):
        self.wrapped_operator.execute()

    def next(self):
        if branch_executed:
            return branch_target
        else:
            return next


class CallDecorator(Decorator):
    def execute(self):
        internal_memory.prepare_call()
        self.wrapped_operator.execute()
        
    def next(self):
        return called_operator

        
class ReturnDecorator(Decorator):
    def execute(self):
        internal_memory.prepare_return()
        self.wrapped_operator.execute()
        
    def next(self):
        return return_address

        
class PrintDecorator(Decorator):
    def execute(self):
        self.wrapped_operator.execute()
        screen.write(printable_string)

    def next(self):
        self.wrapped_operator.next()

        
class ParseDecorator(Decorator):
    def execute(self):
        self.wrapped_operator.execute()
        parse(dictionary, input)

    def next(self):
        self.wrapped_operator.next()


