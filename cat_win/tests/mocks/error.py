"""
error
"""

class ErrorDefGen:
    """
    generate a function that raises a specific error
    """
    @staticmethod
    def get_def(error: Exception):
        """
        return a function that raises a specific error
        """
        def func(*args, **kwargs):
            raise error
        return func
