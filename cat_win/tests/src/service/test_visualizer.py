from unittest import TestCase
from unittest.mock import patch
import os

from cat_win.src.const.colorconstants import CVis
from cat_win.src.service.visualizer import Visualizer
from cat_win.src.service.helper.vishelper import Entropy
from cat_win.tests.mocks.std import StdOutMock

test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'texts', 'test.txt')


@patch('shutil.get_terminal_size', lambda: (120, 30))
class TestVisualizer(TestCase):
    maxDiff = None

    def test_get_color_byte_view(self):
        self.assertEqual(Visualizer.get_color_byte_view(0), CVis.BYTE_VIEW_0)
        self.assertEqual(Visualizer.get_color_byte_view(255), CVis.BYTE_VIEW_256)
        self.assertEqual(Visualizer.get_color_byte_view(254), CVis.BYTE_VIEW_EXTENDED)
        self.assertEqual(Visualizer.get_color_byte_view(128), CVis.BYTE_VIEW_EXTENDED)
        self.assertEqual(Visualizer.get_color_byte_view(126), CVis.BYTE_VIEW_PRINTABLE)
        self.assertEqual(Visualizer.get_color_byte_view(32), CVis.BYTE_VIEW_PRINTABLE)
        self.assertEqual(Visualizer.get_color_byte_view(13), CVis.BYTE_VIEW_PRINTABLE)
        self.assertEqual(Visualizer.get_color_byte_view(10), CVis.BYTE_VIEW_PRINTABLE)
        self.assertEqual(Visualizer.get_color_byte_view(9), CVis.BYTE_VIEW_PRINTABLE)
        self.assertEqual(Visualizer.get_color_byte_view(31), CVis.BYTE_VIEW_CONTROL)
        self.assertEqual(Visualizer.get_color_byte_view(127), CVis.BYTE_VIEW_CONTROL)
        self.assertEqual(Visualizer.get_color_byte_view(1), CVis.BYTE_VIEW_CONTROL)

    def test_get_color_entropy(self):
        self.assertEqual(Visualizer.get_color_entropy(100), CVis.ENTROPY_VERY_HIGH)
        self.assertEqual(Visualizer.get_color_entropy(81), CVis.ENTROPY_VERY_HIGH)
        self.assertEqual(Visualizer.get_color_entropy(80), CVis.ENTROPY_HIGH)
        self.assertEqual(Visualizer.get_color_entropy(61), CVis.ENTROPY_HIGH)
        self.assertEqual(Visualizer.get_color_entropy(60), CVis.ENTROPY_MEDIUM)
        self.assertEqual(Visualizer.get_color_entropy(41), CVis.ENTROPY_MEDIUM)
        self.assertEqual(Visualizer.get_color_entropy(40), CVis.ENTROPY_LOW)
        self.assertEqual(Visualizer.get_color_entropy(21), CVis.ENTROPY_LOW)
        self.assertEqual(Visualizer.get_color_entropy(20), CVis.ENTROPY_VERY_LOW)
        self.assertEqual(Visualizer.get_color_entropy(0), CVis.ENTROPY_VERY_LOW)

    def test_display_data(self):
        expected_result = """\
\x1b[0m\x1b[30m\u2588\u2588\x1b[0m\x1b[32m\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\x1b[0m\x1b[34m\u2588\u2588
\u2588\u2588\x1b[0m\x1b[32m\u2588\u2588\u2588\u2588\x1b[0m\x1b[34m\u2588\u2588\x1b[0m\x1b[32m\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588
\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588
\u2588\u2588\u2588\u2588\x1b[0m\x1b[34m\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588
\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588
\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588
\x1b[0m
"""
        def dummy_gen():
            for i in range(6):
                yield range(i*10, (i+1)*10)
        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            Visualizer.display_data(dummy_gen(), Visualizer.get_color_byte_view)
            self.assertEqual(fake_out.getvalue(), expected_result)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *_: b'1234')
    @patch('cat_win.src.service.helper.vishelper.SpaceFilling.get_scan_curve', lambda *_: 'get_scan_curve')
    def test_visualize_byte_view(self):
        files = [test_file_path]
        vis = Visualizer(files)

        with patch.object(Visualizer, "display_data") as mock_display_data:
            vis.visualize_byte_view(files[0])
            mock_display_data.assert_called_once_with('get_scan_curve', Visualizer.get_color_byte_view)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *_: b'1234')
    @patch('cat_win.src.service.helper.vishelper.SpaceFilling.get_zorder_curve', lambda *_: 'get_zorder_curve')
    def test_visualize_zorder_curve_view(self):
        files = [test_file_path]
        vis = Visualizer(files)

        with patch.object(Visualizer, "display_data") as mock_display_data:
            vis.visualize_zorder_curve_view(files[0])
            mock_display_data.assert_called_once_with('get_zorder_curve', Visualizer.get_color_byte_view)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *_: b'1234')
    @patch('cat_win.src.service.helper.vishelper.SpaceFilling.get_hilbert_curve', lambda *_: 'get_hilbert_curve')
    def test_visualize_hilbert_curve_view(self):
        files = [test_file_path]
        vis = Visualizer(files)

        with patch.object(Visualizer, "display_data") as mock_display_data:
            vis.visualize_hilbert_curve_view(files[0])
            mock_display_data.assert_called_once_with('get_hilbert_curve', Visualizer.get_color_byte_view)

    @patch('cat_win.src.service.helper.iohelper.IoHelper.read_file', lambda *_: b'1234')
    @patch('cat_win.src.service.helper.vishelper.SpaceFilling.get_hilbert_curve', lambda *_: 'get_hilbert_curve')
    def test_visualize_shannon_entropy(self):
        files = [test_file_path]
        vis = Visualizer(files)

        with patch.object(Entropy, "normalized_shannon_entropy") as mock_normalized_entropy, \
            patch.object(Visualizer, "display_data") as mock_display_data:
            vis.visualize_shannon_entropy(files[0])
            mock_normalized_entropy.assert_called_once_with(b'1234')
            mock_display_data.assert_called_once_with('get_hilbert_curve', Visualizer.get_color_entropy)

    def test_visualize_digraph_dot_plot(self):
        files = [test_file_path]
        vis = Visualizer(files)

        with patch('sys.stdout', new=StdOutMock()) as fake_out:
            vis.visualize_digraph_dot_plot(files[0])
            self.assertIn('Min: 0, Avg: 0.003, Max: 7', fake_out.getvalue())

    def test_visualize_files(self):
        files = [test_file_path]

        vis = Visualizer(files, 'ByteView')
        with patch.object(Visualizer, "visualize_byte_view") as mock_visualizer, \
            patch('sys.stdout', new=StdOutMock()) as fake_out:
            vis.visualize_files()
            mock_visualizer.assert_called_once_with(files[0])
            self.assertIn('Visualizing ', fake_out.getvalue())
        vis = Visualizer(files, 'ZOrderCurveView')
        with patch.object(Visualizer, "visualize_zorder_curve_view") as mock_visualizer, \
            patch('sys.stdout', new=StdOutMock()) as fake_out:
            vis.visualize_files()
            mock_visualizer.assert_called_once_with(files[0])
            self.assertIn('Visualizing ', fake_out.getvalue())
        vis = Visualizer(files, 'HilbertCurveView')
        with patch.object(Visualizer, "visualize_hilbert_curve_view") as mock_visualizer, \
            patch('sys.stdout', new=StdOutMock()) as fake_out:
            vis.visualize_files()
            mock_visualizer.assert_called_once_with(files[0])
            self.assertIn('Visualizing ', fake_out.getvalue())
        vis = Visualizer(files, 'ShannonEntropy')
        with patch.object(Visualizer, "visualize_shannon_entropy") as mock_visualizer, \
            patch('sys.stdout', new=StdOutMock()) as fake_out:
            vis.visualize_files()
            mock_visualizer.assert_called_once_with(files[0])
            self.assertIn('Visualizing ', fake_out.getvalue())
        vis = Visualizer(files, 'DigraphDotPlotView')
        with patch.object(Visualizer, "visualize_digraph_dot_plot") as mock_visualizer, \
            patch('sys.stdout', new=StdOutMock()) as fake_out:
            vis.visualize_files()
            mock_visualizer.assert_called_once_with(files[0])
            self.assertIn('Visualizing ', fake_out.getvalue())

    def test_set_flags(self):
        backup = Visualizer.debug
        Visualizer.set_flags(True)
        self.assertTrue(Visualizer.debug)
        Visualizer.set_flags(False)
        self.assertFalse(Visualizer.debug)
        Visualizer.set_flags(backup)
