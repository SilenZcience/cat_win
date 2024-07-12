"""
visualizer
"""

from functools import lru_cache
import os

from cat_win.src.const.colorconstants import CVis
from cat_win.src.service.helper.iohelper import IoHelper
from cat_win.src.service.helper.vishelper import SpaceFilling, Entropy


GRAY_SCALE_VECTOR    = r"█▓▒░ "


class Visualizer:
    """
    visualize given files in different ways.
    """
    debug: bool = False

    def __init__(self, files: list, v_type: str = 'ByteView', truncate: list = None) -> None:
        self.files = files
        self.v_type =v_type
        self.truncate = truncate if truncate is not None else [None, None, None]

    @lru_cache(maxsize=256)
    @staticmethod
    def get_color_byte_view(byte: int) -> str:
        """
        return a color based on the type of byte given
        
        Parameters:
        byte (int):
            the byte to check
        
        Returns:
            ansi color code
        """
        if byte == 0:
            return CVis.BYTE_VIEW_0
        if byte == 255:
            return CVis.BYTE_VIEW_256
        if byte >= 128:
            return CVis.BYTE_VIEW_EXTENDED
        if 32 <= byte < 127 or byte in [9,10,13]:
            return CVis.BYTE_VIEW_PRINTABLE
        return CVis.BYTE_VIEW_CONTROL

    @lru_cache(maxsize=256)
    @staticmethod
    def get_color_entropy(entropy: int) -> str:
        """
        return a color based on the value of the entropy given.
        entropy lies between 0 and 100.
        
        Parameters:
        entropy (int):
            the entropy to classify
        
        Returns:
            ansi color code
        """
        if entropy > 80:
            return CVis.ENTROPY_VERY_HIGH
        if entropy > 60:
            return CVis.ENTROPY_HIGH
        if entropy > 40:
            return CVis.ENTROPY_MEDIUM
        if entropy > 20:
            return CVis.ENTROPY_LOW
        return CVis.ENTROPY_VERY_LOW

    @staticmethod
    def display_data(data_generator, color_def) -> None:
        """
        print the visualization to stdout.
        
        Paramaters:
        data_generator (generator [yields partitioned lists]):
            the generator splitting the data into chunks
        color_def (def):
            the function used to determine the color for each byte
        """
        d_char = GRAY_SCALE_VECTOR[0] * 2

        vis_row, last_byte = '', -1
        for row in data_generator:
            for byte in row:
                if byte < 0:
                    vis_row += '  '
                    continue
                if byte != last_byte:
                    vis_row += f"{CVis.COLOR_RESET}{color_def(byte)}"
                    last_byte = byte
                vis_row += str(byte).rjust(4) if Visualizer.debug else d_char
            if vis_row:
                print(vis_row)
                vis_row = ''
        print(CVis.COLOR_RESET)

    def visualize_byte_view(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using the scan curve.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        width = os.get_terminal_size()[0] // 2
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))
        Visualizer.display_data(SpaceFilling.get_scan_curve(bin_content, width),
                                Visualizer.get_color_byte_view)

    def visualize_zorder_curve_view(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using a z-order curve view.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        width = os.get_terminal_size()[0] // 2
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))
        Visualizer.display_data(SpaceFilling.get_zorder_curve(bin_content, width),
                                Visualizer.get_color_byte_view)

    def visualize_hilbert_curve_view(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using a hilbert curve view.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        width = os.get_terminal_size()[0] // 2
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))
        Visualizer.display_data(SpaceFilling.get_hilbert_curve(bin_content, width),
                                Visualizer.get_color_byte_view)

    def visualize_shannon_entropy(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using the shannon entropy.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        width = os.get_terminal_size()[0] // 2
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))
        bin_content = Entropy.normalized_shannon_entropy(bin_content)
        Visualizer.display_data(SpaceFilling.get_hilbert_curve(bin_content, width),
                                Visualizer.get_color_entropy)

    def visualize_digraph_dot_plot(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using a digraph dot plot view.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))
        digraph = [0] * 65536

        bin_content_it = iter(bin_content)
        for byte_a, byte_b in zip(bin_content_it, bin_content_it):
            digraph[byte_a*256+byte_b] += 1
        bin_content_it = iter(bin_content)
        try:
            next(bin_content_it)
        except StopIteration:
            pass
        for byte_a, byte_b in zip(bin_content_it, bin_content_it):
            digraph[byte_a*256+byte_b] += 1

        digraph_sorted = sorted(digraph.copy(), reverse=True)

        d_min, d_max = digraph_sorted[-1], digraph_sorted[0]
        d_avg = sum(digraph)/65536
        # d_range = d_max - d_min

        try:
            last_pos_index = digraph_sorted.index(0)
        except ValueError:
            last_pos_index = 65536
        digraph_sorted = digraph_sorted[:last_pos_index]
        digraph_sorted.reverse()

        borders = [-1] * len(GRAY_SCALE_VECTOR)
        for i in range(len(borders)):
            # borders[i] = d_min + d_range//2 * i
            try:
                borders[i] = digraph_sorted[len(digraph_sorted)//len(GRAY_SCALE_VECTOR)*i]
            except IndexError:
                borders[i] = 0
        borders.reverse()

        vis_row = ''
        print(f"{CVis.DIGRAPH_VIEW_CONTROL}+{'-'*512}+{CVis.COLOR_RESET}")
        for i in range(256):
            for j in range(256):
                for index, border in enumerate(borders):
                    if digraph[i*256+j] >= border:
                        vis_row += (GRAY_SCALE_VECTOR[index] * 2)
                        break
                else:
                    vis_row += '  '
            print(f"{CVis.DIGRAPH_VIEW_CONTROL}|{vis_row}|{CVis.COLOR_RESET}")
            vis_row = ''

        shading_info_list = list(zip(borders, GRAY_SCALE_VECTOR))
        boundary_top = d_max+1
        for i, (b, g) in enumerate(shading_info_list, start=1):
            if g == ' ':
                g = '␣'
            if i == len(shading_info_list):
                shading_info_list[i-1] = f"{d_min}-{boundary_top}: {g}"
                continue
            shading_info_list[i-1] = f"{b}-{boundary_top}: {g}"
            boundary_top = b
        shading_info = ', '.join(shading_info_list)
        status_bar  = f"---- Min: {d_min}, Avg: {round(d_avg, 3)}, Max: {d_max} |"
        status_bar += f" Shading boundaries: {shading_info} "
        print(f"{CVis.DIGRAPH_VIEW_CONTROL}+{status_bar.ljust(512, '-')}+{CVis.COLOR_RESET}")

    def visualize_files(self) -> None:
        """
        visualize all initialized files by the defined method.
        """
        if self.v_type == 'ByteView':
            visualizer = self.visualize_byte_view
        if self.v_type == 'ZOrderCurveView':
            visualizer = self.visualize_zorder_curve_view
        if self.v_type == 'HilbertCurveView':
            visualizer = self.visualize_hilbert_curve_view
        if self.v_type == 'ShannonEntropy':
            visualizer = self.visualize_shannon_entropy
        if self.v_type == 'DigraphDotPlotView':
            visualizer = self.visualize_digraph_dot_plot
        for file in self.files:
            print(f"Visualizing '{file}':")
            visualizer(file)

    @staticmethod
    def set_flags(debug: bool):
        Visualizer.debug = debug
