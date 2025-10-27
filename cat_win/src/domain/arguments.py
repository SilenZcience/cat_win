"""
arguments
"""

from cat_win.src.const.argconstants import DIFFERENTIABLE_ARGS


def reduce_list(args: list) -> list:
    """
    remove duplicate args regardless if shortform or
    longform has been used, an exception exists for those
    args that contain different information per parameter.

    Parameters:
    args (list):
        the entire list of args, containing possible duplicates

    Returns:
    new_args (list):
        the args-list without duplicates
    """
    new_args = []
    temp_args_id = []

    for arg in args:
        arg_id, _ = arg
        # it can make sense to have the exact same parameter twice, even if it has
        # the same information, therefor we do not test for the param here.
        if arg_id in DIFFERENTIABLE_ARGS:
            new_args.append(arg)
        elif arg_id not in temp_args_id:
            temp_args_id.append(arg_id)
            new_args.append(arg)

    return new_args

def diff_list(args: list, to_remove: list) -> list:
    """
    subtract args in to_remove from args in args regardless
    if shortform or longform has been used, an exception exists for those
    args that contain different information per parameter.

    Parameters:
    args (list):
        the entire list of args
    to_remove (list):
        the list of args to subtract from the args list

    Returns:
    new_args (list):
        the args-list without duplicates
    """
    new_args = []
    temp_args_id = [id for id, _ in to_remove]
    temp_args = [arg for arg in to_remove if arg[0] in DIFFERENTIABLE_ARGS]

    for arg in args:
        arg_id, _ = arg
        if arg_id not in temp_args_id or arg_id in DIFFERENTIABLE_ARGS:
            new_args.append(arg)

    for arg in temp_args:
        try:
            new_args.remove(arg)
        except ValueError:
            pass

    return new_args

class Arguments:
    """
    define a holder object to store useful meta information
    about the user defined arguments
    """
    def __init__(self) -> None:
        self.args: list = []  # list of all used parameters: format [(id, param),...]
        self.args_id: dict = {}

    def set_args(self, args: list) -> None:
        """
        set the args to use.

        Parameters:
        args (list):
            the args to set
        """
        self.args = reduce_list(args)
        for arg_id, _ in self.args:
            self.args_id[arg_id] = True

    def add_args(self, args: list) -> None:
        """
        add args to use from now on.

        Parameters:
        args (list):
            the args to add
        """
        self.args_id = {}
        self.set_args(self.args + args)

    def delete_args(self, args: list) -> None:
        """
        delete (some) args to longer use them from now on.

        Parameters:
        args (list):
            the list of args to delete
        """
        self.args_id = {}
        self.set_args(diff_list(self.args, args))

    def find_first(self, arg_id1: int, arg_id2: int, is_first: bool = False) -> tuple:
        """
        decide if an argument was passed in before another one.

        Parameters:
        arg_id1 (int):
            the first arg to compare
        arg_id2 (int):
            the second arg to compare

        Returns:
        (tuple|None):
            the argument that was passed in first or None
            with is_first == True:
            the first argument if it was passed in before the second one else None
        """
        if not self[arg_id1] and (not self[arg_id2] or is_first):
            return None
        for a_id, param in self.args:
            if a_id == arg_id1:
                return (arg_id1, param)
            if a_id == arg_id2:
                return None if is_first else (arg_id2, param)

    def __getitem__(self, o: int) -> bool:
        return self.args_id.get(o, False)

    def __iter__(self):
        return iter(self.args)

    def __len__(self) -> int:
        return len(self.args)
