

import cat_win.tests.src.service.helper.test_utility as test_utility
from cat_win.src.service.helper.utilityold import comp_eval as comp_eval_old
from cat_win.src.service.helper.utilityold import comp_conv as comp_conv_old


class TestConverterCompOld(test_utility.TestConverterComp):
    def setUp(self):
        self._comp_eval_backup = test_utility.comp_eval
        self._comp_conv_backup = test_utility.comp_conv
        test_utility.comp_eval = comp_eval_old
        test_utility.comp_conv = comp_conv_old

    def tearDown(self):
        test_utility.comp_eval = self._comp_eval_backup
        test_utility.comp_conv = self._comp_conv_backup
