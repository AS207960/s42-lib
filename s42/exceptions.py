class AddressError(Exception):
    def __init__(self, message):
        self.message = message


class PreconditionError(AddressError):
    def __init__(self, precondition):
        self.precondition = precondition
        super().__init__(message="Precondition failed")


class RequiredElementError(AddressError):
    def __init__(self, element, line):
        self.element = element
        self.line = line
        super().__init__(message="Required element missing")


class RequiredElementsError(AddressError):
    def __init__(self, elements, line):
        self.elements = elements
        self.line = line
        super().__init__(message="Required element missing")
