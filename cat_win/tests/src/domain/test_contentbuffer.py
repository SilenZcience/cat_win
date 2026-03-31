from unittest import TestCase

from cat_win.src.domain.contentbuffer import ContentBuffer


class TestContentBuffer(TestCase):
    def test_contentbuffer_init(self):
        cb = ContentBuffer(['line1', 'line2'], ['prefix1', 'prefix2'], ['suffix1', 'suffix2'])
        self.assertEqual(cb.lines, ['line1', 'line2'])
        self.assertEqual(cb.prefixes, ['prefix1', 'prefix2'])
        self.assertEqual(cb.suffixes, ['suffix1', 'suffix2'])

    def test_contentbuffer_init_empty(self):
        cb = ContentBuffer()
        self.assertEqual(cb.lines, [])
        self.assertEqual(cb.prefixes, [])
        self.assertEqual(cb.suffixes, [])

    def test_content_buffer_init_mismatched_lengths(self):
        with self.assertRaises(ValueError):
            ContentBuffer(['line1'], ['prefix1', 'prefix2'], ['suffix1'])

    def test_contentbuffer_from_lines(self):
        cb = ContentBuffer.from_lines(['line1', 'line2'], default_prefix='p', default_suffix='s')
        self.assertEqual(cb.lines, ['line1', 'line2'])
        self.assertEqual(cb.prefixes, ['p', 'p'])
        self.assertEqual(cb.suffixes, ['s', 's'])

    def test_contentbuffer_from_rows(self):
        cb = ContentBuffer.from_rows([('line1', 'prefix1'), ('line2', 'prefix2', 'suffix2'), ('line3',)])
        self.assertEqual(cb.lines, ['line1', 'line2', 'line3'])
        self.assertEqual(cb.prefixes, ['prefix1', 'prefix2', ''])
        self.assertEqual(cb.suffixes, ['', 'suffix2', ''])

    def test_contentbuffer_from_rows_invalid(self):
        with self.assertRaises(ValueError):
            ContentBuffer.from_rows([('line1','pre', 'suff', '?'), ('line2', 'prefix2', 'suffix2')])
        with self.assertRaises(ValueError):
            ContentBuffer.from_rows([('line1','pre', 'suff'), tuple()])

    def test_contentbuffer_ensure(self):
        cb = ContentBuffer.from_lines(['line1', 'line2'])
        self.assertIs(ContentBuffer.ensure(cb), cb)
        new_cb = ContentBuffer.ensure([('line1', 'p1'), ('line2', 'p2')])
        self.assertEqual(new_cb.lines, ['line1', 'line2'])
        self.assertEqual(new_cb.prefixes, ['p1', 'p2'])
        self.assertEqual(new_cb.suffixes, ['', ''])

    def test_contentbuffer_len_and_bool(self):
        cb = ContentBuffer.from_lines(['line1', 'line2'])
        self.assertEqual(len(cb), 2)
        self.assertTrue(cb)
        empty_cb = ContentBuffer()
        self.assertEqual(len(empty_cb), 0)
        self.assertFalse(empty_cb)

    def test_contentbuffer_iter(self):
        cb = ContentBuffer.from_lines(['line1', 'line2'], default_prefix='p', default_suffix='s')
        self.assertEqual(list(cb), [('line1', 'p', 's'), ('line2', 'p', 's')])

    def test_contentbuffer_getitem(self):
        cb = ContentBuffer.from_lines(['line1', 'line2'], default_prefix='p', default_suffix='s')
        self.assertEqual(cb[0], ('line1', 'p', 's'))
        self.assertEqual(cb[1], ('line2', 'p', 's'))
        cb_slice = cb[:1]
        self.assertIsInstance(cb_slice, ContentBuffer)
        self.assertEqual(cb_slice.lines, ['line1'])
        self.assertEqual(cb_slice.prefixes, ['p'])
        self.assertEqual(cb_slice.suffixes, ['s'])

    def test_contentbuffer_add(self):
        cb1 = ContentBuffer.from_lines(['line1'], default_prefix='p1', default_suffix='s1')
        cb2 = ContentBuffer.from_lines(['line2'], default_prefix='p2', default_suffix='s2')
        cb3 = cb1 + cb2
        self.assertEqual(cb3.lines, ['line1', 'line2'])
        self.assertEqual(cb3.prefixes, ['p1', 'p2'])
        self.assertEqual(cb3.suffixes, ['s1', 's2'])

    def test_eqlality(self):
        cb1 = ContentBuffer.from_lines(['line1'], default_prefix='p1', default_suffix='s1')
        cb2 = ContentBuffer.from_lines(['line1'], default_prefix='p1', default_suffix='s1')
        cb3 = ContentBuffer.from_lines(['line2'], default_prefix='p2', default_suffix='s2')
        self.assertEqual(cb1, cb2)
        self.assertNotEqual(cb1, cb3)
        self.assertNotEqual(cb1, [('line1', 'p1', 's1')])  # different type

    def test_contentbuffer_add_with_non_contentbuffer(self):
        cb1 = ContentBuffer.from_lines(['line1'], default_prefix='p1', default_suffix='s1')
        cb2 = [('line2', 'p2')]
        cb3 = cb1 + cb2
        self.assertEqual(cb3.lines, ['line1', 'line2'])
        self.assertEqual(cb3.prefixes, ['p1', 'p2'])
        self.assertEqual(cb3.suffixes, ['s1', ''])

    def test_contentbuffer_append(self):
        cb = ContentBuffer.from_lines(['line1'], default_prefix='p1', default_suffix='s1')
        cb.append('line2', prefix='p2', suffix='s2')
        self.assertEqual(cb.lines, ['line1', 'line2'])
        self.assertEqual(cb.prefixes, ['p1', 'p2'])
        self.assertEqual(cb.suffixes, ['s1', 's2'])

        cb = ContentBuffer.from_lines(['line1'], default_prefix='p1', default_suffix='s1')
        cb.append('line2')
        self.assertEqual(cb.lines, ['line1', 'line2'])
        self.assertEqual(cb.prefixes, ['p1', ''])
        self.assertEqual(cb.suffixes, ['s1', ''])

        cb = ContentBuffer()
        cb.append('line1', prefix='p1', suffix='s1')
        self.assertEqual(cb.lines, ['line1'])
        self.assertEqual(cb.prefixes, ['p1'])
        self.assertEqual(cb.suffixes, ['s1'])

    def test_reverse(self):
        cb = ContentBuffer.from_lines(['line1', 'line2'], default_prefix='p', default_suffix='s')
        cb.reverse()
        self.assertEqual(cb.lines, ['line2', 'line1'])
        self.assertEqual(cb.prefixes, ['p', 'p'])
        self.assertEqual(cb.suffixes, ['s', 's'])

    def test_sort(self):
        cb = ContentBuffer.from_rows([('line2', 'a'), ('line1', 'b')])
        cb.sort(key=lambda x: x[0])
        self.assertEqual(cb.lines, ['line1', 'line2'])
        self.assertEqual(cb.prefixes, ['b', 'a'])
        self.assertEqual(cb.suffixes, ['', ''])

        cb.sort(key=lambda x: x[1])
        self.assertEqual(cb.lines, ['line2', 'line1'])
        self.assertEqual(cb.prefixes, ['a', 'b'])
        self.assertEqual(cb.suffixes, ['', ''])

    def test_sort_no_key(self):
        cb = ContentBuffer.from_rows([('line2', 'a'), ('line1', 'b')])
        with self.assertRaises(NotImplementedError):
            cb.sort()

    def test_filter(self):
        cb = ContentBuffer.from_rows([('line1', 'p1', 's1'), ('line2', 'p2', 's2')])
        cb.filter(lambda line, prefix, suffix: prefix == 'p1')
        self.assertEqual(cb.lines, ['line1'])
        self.assertEqual(cb.prefixes, ['p1'])
        self.assertEqual(cb.suffixes, ['s1'])

        cb = ContentBuffer.from_rows([('line1', 'p1', 's1'), ('line2', 'p2', 's2')])
        cb.filter(lambda line, prefix, suffix: suffix == 's2')
        self.assertEqual(cb.lines, ['line2'])
        self.assertEqual(cb.prefixes, ['p2'])
        self.assertEqual(cb.suffixes, ['s2'])

        cb = ContentBuffer.from_rows([('line1', 'p1', 's1'), ('line2', 'p2', 's2')])
        cb.filter(lambda line, prefix, suffix: line == 'line3')
        self.assertEqual(cb.lines, [])
        self.assertEqual(cb.prefixes, [])
        self.assertEqual(cb.suffixes, [])

    def test_map(self):
        cb = ContentBuffer.from_rows([('line1', 'p1', 's1'), ('line2', 'p2', 's2')])
        new_cb = cb.map(lambda line, prefix, suffix: (line.upper(), prefix.upper(), suffix.upper()))
        self.assertEqual(new_cb.lines, ['LINE1', 'LINE2'])
        self.assertEqual(new_cb.prefixes, ['P1', 'P2'])
        self.assertEqual(new_cb.suffixes, ['S1', 'S2'])
