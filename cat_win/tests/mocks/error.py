
class ErrorDefGen:
    def get_def(error):
        def func(*args, **kwargs):
            raise error
        return func
