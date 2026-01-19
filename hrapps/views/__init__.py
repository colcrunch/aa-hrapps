class Field:
    def __init__(self, type, question, options=None, required=False):
        self.type = type
        self.question = question
        self.required = required
        if options is not None:
            self.options = tuple(options)
        else:
            self.options = None