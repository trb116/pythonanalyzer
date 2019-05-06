class AlaudaServerError(Exception):

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __str__(self):
        return '[alauda server error] {0} {1}'.format(self.status_code, self.message)

    __repr__ = __str__


class AlaudaInputError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return '[alauda input error] {0}'.format(self.message)

    __repr__ = __str__


class AlaudaExecError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return '[alauda exec error] {0}'.format(self.message)

    __repr__ = __str__
