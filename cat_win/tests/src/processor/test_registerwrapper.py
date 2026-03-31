from unittest import TestCase

from cat_win.src.processor.registerwrapper import (
    _wrapper_factory,
    POST_CONTENT_ACTIONS,
    PRE_CONTENT_ACTIONS,
    PRO_CONTENT_ACTIONS,
    STARTUP_ACTIONS,
    register_post,
    register_pre,
    register_pro,
    register_startup,
)

class TestRegisterWrapper(TestCase):
    def setUp(self):
        self._snap_startup = dict(STARTUP_ACTIONS)
        self._snap_pre = dict(PRE_CONTENT_ACTIONS)
        self._snap_pro = dict(PRO_CONTENT_ACTIONS)
        self._snap_post = dict(POST_CONTENT_ACTIONS)
        STARTUP_ACTIONS.clear()
        PRE_CONTENT_ACTIONS.clear()
        PRO_CONTENT_ACTIONS.clear()
        POST_CONTENT_ACTIONS.clear()

    def tearDown(self):
        STARTUP_ACTIONS.clear()
        STARTUP_ACTIONS.update(self._snap_startup)

        PRE_CONTENT_ACTIONS.clear()
        PRE_CONTENT_ACTIONS.update(self._snap_pre)

        PRO_CONTENT_ACTIONS.clear()
        PRO_CONTENT_ACTIONS.update(self._snap_pro)

        POST_CONTENT_ACTIONS.clear()
        POST_CONTENT_ACTIONS.update(self._snap_post)

    def test_wrapper_factory_maps_plain_arg_ids_to_same_function(self):
        action_map = {}
        register = _wrapper_factory(action_map)

        @register(10, 20)
        def action():
            return 'ok'

        self.assertIs(action_map[10], action)
        self.assertIs(action_map[20], action)
        self.assertEqual(action(), 'ok')

    def test_wrapper_factory_tuple_arg_calls_factory_with_payload(self):
        action_map = {}
        register = _wrapper_factory(action_map)

        def mk_action(token):
            return lambda: f'generated:{token}'

        decorated = register((7, 'alpha'))(mk_action)
        self.assertIs(decorated, mk_action)
        self.assertIn(7, action_map)
        self.assertNotEqual(action_map[7], mk_action)
        self.assertEqual(action_map[7](), 'generated:alpha')

    def test_wrapper_factory_mixed_plain_and_tuple_registration(self):
        action_map = {}
        register = _wrapper_factory(action_map)

        def mk_action(token):
            return f'tuple:{token}'

        register(1, (2, 'x'), 3)(mk_action)

        self.assertIs(action_map[1], mk_action)
        self.assertEqual(action_map[2], 'tuple:x')
        self.assertIs(action_map[3], mk_action)

    def test_wrapper_factory_without_arg_ids_leaves_map_unchanged(self):
        action_map = {99: 'existing'}
        register = _wrapper_factory(action_map)

        @register()
        def action():
            return 'noop'

        self.assertEqual(action_map, {99: 'existing'})
        self.assertEqual(action(), 'noop')

    def test_wrapper_factory_later_registration_overwrites_same_key(self):
        action_map = {}
        register = _wrapper_factory(action_map)

        @register(1)
        def action_a():
            return 'a'

        @register(1)
        def action_b():
            return 'b'

        self.assertIs(action_map[1], action_b)
        self.assertEqual(action_a(), 'a')
        self.assertEqual(action_b(), 'b')

    def test_register_startup_populates_startup_actions(self):
        @register_startup(11)
        def startup_action():
            return 'startup'

        self.assertIs(STARTUP_ACTIONS[11], startup_action)

    def test_register_pre_populates_pre_content_actions(self):
        @register_pre(12)
        def pre_action():
            return 'pre'

        self.assertIs(PRE_CONTENT_ACTIONS[12], pre_action)

    def test_register_pro_populates_pro_content_actions(self):
        @register_pro(13)
        def pro_action():
            return 'pro'

        self.assertIs(PRO_CONTENT_ACTIONS[13], pro_action)

    def test_register_post_populates_post_content_actions(self):
        @register_post(14)
        def post_action():
            return 'post'

        self.assertIs(POST_CONTENT_ACTIONS[14], post_action)

    def test_each_register_writes_only_its_own_registry(self):
        @register_startup(1)
        def a():
            return 'a'

        @register_pre(2)
        def b():
            return 'b'

        @register_pro(3)
        def c():
            return 'c'

        @register_post(4)
        def d():
            return 'd'

        self.assertEqual(set(STARTUP_ACTIONS.keys()), {1})
        self.assertEqual(set(PRE_CONTENT_ACTIONS.keys()), {2})
        self.assertEqual(set(PRO_CONTENT_ACTIONS.keys()), {3})
        self.assertEqual(set(POST_CONTENT_ACTIONS.keys()), {4})
        self.assertNotIn(2, STARTUP_ACTIONS)
        self.assertNotIn(3, PRE_CONTENT_ACTIONS)
        self.assertNotIn(4, PRO_CONTENT_ACTIONS)
