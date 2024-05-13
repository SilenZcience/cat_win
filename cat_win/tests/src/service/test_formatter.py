from unittest import TestCase

from cat_win.src.service.formatter import Formatter
# import sys
# sys.path.append('../cat_win')

class TestFormatter(TestCase):
    maxDiff = None

    def test_format_json(self):
        in_put = '{"person":{"name":"Alice","age":25,"employees":[{"name":"Bob"},{"name:":"David"}]}}'
        expected_output = '{\n  "person": {\n    "name": "Alice",\n    "age": 25,\n    "employees": [\n      {\n        "name": "Bob"\n      },\n      {\n        "name:": "David"\n      }\n    ]\n  }\n}'
        self.assertEqual(Formatter.format_json(in_put), (expected_output, True))

    def test_format_json_invalid(self):
        in_put = '<lib><book id="1"><title>Cats</title></book><book id="2"></book></lib>'
        self.assertEqual(Formatter.format_json(in_put), (in_put, False))

    def test_format_xml(self):
        in_put = '<lib><book id="1"><title>Cats</title></book><book id="2"></book></lib>'
        expected_output = '<?xml version="1.0" ?>\n<lib>\n  <book id="1">\n    <title>Cats</title>\n  </book>\n  <book id="2"/>\n</lib>\n'
        self.assertEqual(Formatter.format_xml(in_put), (expected_output, True))

    def test_format_xml_invalid(self):
        in_put = '{"person":{"name":"Alice","age":25,"employees":[{"name":"Bob"},{"name:":"David"}]}}'
        self.assertEqual(Formatter.format_xml(in_put), (in_put, False))

    def test_format_format_json(self):
        in_put = '{"person":{"name":"Alice","age":25,"employees":[{"name":"Bob"},{"name:":"David"}]}}'
        expected_output = [
            ('', '{'),
            ('', '  "person": {'),
            ('', '    "name": "Alice",'),
            ('', '    "age": 25,'),
            ('', '    "employees": ['),
            ('', '      {'),
            ('', '        "name": "Bob"'),
            ('', '      },'),
            ('', '      {'),
            ('', '        "name:": "David"'),
            ('', '      }'),
            ('', '    ]'),
            ('', '  }'),
            ('', '}'),
        ]
        self.assertCountEqual(Formatter.format([('', in_put)]), expected_output)

    def test_format_format_xml(self):
        in_put = '<lib><book id="1"><title>Cats</title></book><book id="2"></book></lib>'
        expected_output = [
            ('', '<?xml version="1.0" ?>'),
            ('', '<lib>'),
            ('', '  <book id="1">'),
            ('', '    <title>Cats</title>'),
            ('', '  </book>'),
            ('', '  <book id="2"/>'),
            ('', '</lib>'),
        ]
        self.assertCountEqual(Formatter.format([('', in_put)]), expected_output)

    def test_format_format_invalid(self):
        self.assertCountEqual(Formatter.format([('', '-')]), [('', '-')])
