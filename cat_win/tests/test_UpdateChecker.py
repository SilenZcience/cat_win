from unittest import TestCase

import cat_win.web.UpdateChecker as UpdateChecker
# import sys
# sys.path.append('../cat_win')


class TestUpdateChecker(TestCase):
    def test_onlyNumeric(self):
        self.assertEqual(UpdateChecker.onlyNumeric('1nh589h15io125b085218'), 158915125085218)
        self.assertEqual(UpdateChecker.onlyNumeric('1nh'), 1)
        self.assertEqual(UpdateChecker.onlyNumeric('123'), 123)
        self.assertEqual(UpdateChecker.onlyNumeric('abc'), 0)
    
    def test_genVersionTuples(self):
        self.assertEqual(UpdateChecker.genVersionTuples('1.0.33.0', '1.1.0a'),
                         (('01', '00', '33', '00'), ('01', '01', '0a', '00')))
        self.assertEqual(UpdateChecker.genVersionTuples('1.2.3', '1.2.3.4.5'),
                         (('1', '2', '3', '0', '0'), ('1', '2', '3', '4', '5')))
        self.assertEqual(UpdateChecker.genVersionTuples('1.12345', '1.2'),
                         (('00001', '12345'), ('00001', '00002')))
    
    def test_version_comparison_up_to_date(self):
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', '1.0.9'), 0)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', '1.0.09'), 0)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.10.9', 'v1.10.9'), 0)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.7a.9', '1.7a.9'), 0)
        self.assertEqual(UpdateChecker.newVersionAvailable('09.0.8b', '9.0.08b'), 0)
        self.assertEqual(UpdateChecker.newVersionAvailable('v7b.4', '07b.04.00'), 0)
        self.assertEqual(UpdateChecker.newVersionAvailable('9', '9.0.0'), 0)
        
    def test_version_comparison_stable_release(self):
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', '1.0.10'), 1)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.15', 'v1.0.016'), 1)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.12', '1.000.020'), 1)
        self.assertEqual(UpdateChecker.newVersionAvailable('v1.0.0', 'v01.00.01'), 1)
        self.assertEqual(UpdateChecker.newVersionAvailable('2.1.5a', '2.1.6'), 1)
        self.assertEqual(UpdateChecker.newVersionAvailable('v2.1b.5a', '2.1b.051'), 1)

    def test_version_comparison_pre_release(self):
        self.assertEqual(UpdateChecker.newVersionAvailable('v1.0.9', '1.0.9a'), 2)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', '1.0.09b'), 2)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', 'v1.0.10b'), 2)
        self.assertEqual(UpdateChecker.newVersionAvailable('2.1.5a', '2.1.5b'), 2)
    
    def test_version_comparison_stable_release_unsafe(self):
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', '1.01.10'), -1)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.15', '1.1.9'), -1)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', 'v2.0.9'), -1)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.12', '1.001.0'), -1)
        self.assertEqual(UpdateChecker.newVersionAvailable('v1.0.0', 'v01.001.01'), -1)
        self.assertEqual(UpdateChecker.newVersionAvailable('2.1.5a', '2.2.5'), -1)

    def test_version_comparison_pre_release_unsafe(self):
        self.assertEqual(UpdateChecker.newVersionAvailable('v1.0.9', '1a.0.9a'), -2)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', '1.0a.9'), -2)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', 'v1a.0.9'), -2)
        self.assertEqual(UpdateChecker.newVersionAvailable('1.0.9', '2b.0.10b'), -2)
        self.assertEqual(UpdateChecker.newVersionAvailable('v1.0.9', '1.0b.10'), -2)
        self.assertEqual(UpdateChecker.newVersionAvailable('2.1.5a', '2.1a.5'), -2)
        
    def test_version_availability_current_is_newest(self):
        self.assertEqual(UpdateChecker.newVersionAvailable('v1.1.9', '1.0.9a'), 0)

# python -m unittest discover -s tests -p test*.py
