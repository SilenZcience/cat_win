"""
registerwrapper
"""


def _wrapper_factory(action_map):
    def register(*arg_ids: int):
        def _register_action(func):
            for arg_id in arg_ids:
                if isinstance(arg_id, tuple):
                    action_map[arg_id[0]] = func(arg_id[1])
                    continue
                action_map[arg_id] = func
            return func
        return _register_action
    return register

STARTUP_ACTIONS = {}
register_startup = _wrapper_factory(STARTUP_ACTIONS)

PRE_CONTENT_ACTIONS = {}
register_pre = _wrapper_factory(PRE_CONTENT_ACTIONS)

PRO_CONTENT_ACTIONS = {}
register_pro = _wrapper_factory(PRO_CONTENT_ACTIONS)

POST_CONTENT_ACTIONS = {}
register_post = _wrapper_factory(POST_CONTENT_ACTIONS)
