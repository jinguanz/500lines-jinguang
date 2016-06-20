what_to_execute = {
    "instructions": [("LOAD_VALUE", 0),
                     ("LOAD_VALUE", 1),
                     ("ADD_TWO_VALUES", None),
                     ("PRINT_ANSWER", None)],
    "numbers": [7, 5]
}

class Interpreter(object):
    def __init__(self):
        self.stack = []

    def load_value(self, number):
        self.stack.append(number)

    def print_answer(self):
        answer = self.stack.pop()
        print answer

    def add_two_values(self):
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        self.stack.append(first_num + second_num)

    def run_code(self, what_to_execute):
        instructions = what_to_execute['instructions']
        numbers = what_to_execute['numbers']
        for each_step in instructions:
            instruction, argument = each_step
            if instruction == 'LOAD_VALUE':
                number = numbers[argument]
                self.load_value(number)
            elif instruction == 'ADD_TWO_VALUES':
                self.add_two_values()
            elif instruction == 'PRINT_ANSWER':
                self.print_answer()

interpreter = Interpreter()
interpreter.run_code(what_to_execute)
