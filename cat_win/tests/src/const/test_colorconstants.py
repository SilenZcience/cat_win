from unittest import TestCase

from cat_win.src.const.colorconstants import id_to_color_code, ColorOptions, CVis, CPB
# import sys
# sys.path.append('../cat_win')


class TestArgConstants(TestCase):
    maxDiff = None

    def test_id_to_color_code(self):
        self.assertEqual(id_to_color_code(30), '\x1b[30m')

    def test_unique_colors(self):
        all_colors_keys = list(ColorOptions.Fore.keys()) + \
            list(ColorOptions.Back.keys()) + \
                list(ColorOptions.Style.keys())
        all_colors_vals = list(ColorOptions.Fore.values()) + \
            list(ColorOptions.Back.values()) + \
                list(ColorOptions.Style.values())
        self.assertEqual(len(all_colors_keys), len(set(all_colors_keys))*2+2)
        self.assertEqual(len(all_colors_vals), len(set(all_colors_vals))+2)

    def test_remove_colors(self):
        for attr in dir(CVis):
            if not callable(getattr(CVis, attr)) and not attr.startswith("__"):
                self.assertNotEqual(getattr(CVis, attr), '')
        CVis.remove_colors()
        for attr in dir(CVis):
            if not callable(getattr(CVis, attr)) and not attr.startswith("__"):
                self.assertEqual(getattr(CVis, attr), '')

        for attr in dir(CPB):
            if not callable(getattr(CPB, attr)) and not attr.startswith("__"):
                self.assertNotEqual(getattr(CPB, attr), '')
        CPB.remove_colors()
        for attr in dir(CPB):
            if not callable(getattr(CPB, attr)) and not attr.startswith("__"):
                self.assertEqual(getattr(CPB, attr), '')
