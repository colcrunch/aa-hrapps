class Field:
    def __init__(self, type, question, options=None, required=False):
        self.type = type
        self.question = question
        self.required = required
        if options is not None:
            self.options = tuple(options)
        else:
            self.options = None

    def __dict__(self):
        return {
            "type": self.type,
            "question": self.question,
            "required": self.required,
            "options": self.options
        }

class ResponseItem:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer

    @property
    def answer_is_list(self):
        return isinstance(self.answer, list)