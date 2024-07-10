"""
visualizer
"""

import os

from cat_win.src.const.colorconstants import ColorOptions
from cat_win.src.service.helper.iohelper import IoHelper


GRAY_SCALE_VECTOR    = r"█▓▒░ "
DIGRAPH_VIEW_CONTROL = ColorOptions.Fore['GREEN']

BYTE_VIEW_0          = ColorOptions.Fore['BLACK']
BYTE_VIEW_CONTROL    = ColorOptions.Fore['GREEN']
BYTE_VIEW_PRINTABLE  = ColorOptions.Fore['BLUE']
BYTE_VIEW_EXTENDED   = ColorOptions.Fore['RED']
BYTE_VIEW_256        = ColorOptions.Fore['WHITE']


COLOR_RESET          = ColorOptions.Style['RESET']


def get_scan_curve(_list, n: int):
    """
    break a given list into chunks of a given size.
    every other chunk is inverted to generate the scan curve pattern.
    
    Parameters:
    _list (iterable):
        the list or bytearray to scan
    n (int):
        the size of the chunks
    
    Yields:
    _listchunk
        the next chunk to display
    """
    i, _length = 0, len(_list)
    while i*n <= _length:
        if not i % 2:
            yield _list[i*n:(i+1)*n]
        else:
            r_list = list(reversed(_list[i*n:(i+1)*n]))
            r_list = [-1] * (n-len(r_list)) + r_list
            yield r_list
        i += 1

class Visualizer:
    def __init__(self, files: list, v_type: str = 'ByteView', truncate: list = None) -> None:
        self.files = files
        self.v_type =v_type
        self.truncate = truncate if truncate is not None else [None, None, None]

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
            return BYTE_VIEW_0
        if byte == 255:
            return BYTE_VIEW_256
        if byte >= 128:
            return BYTE_VIEW_EXTENDED
        if 32 <= byte < 127 or byte in [9,10,13]:
            return BYTE_VIEW_PRINTABLE
        return BYTE_VIEW_CONTROL

    def visualize_byte_view(self, file_p: str) -> None:
        """
        visualize all bytes in a given file. display the visualization using the scan curve.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """

        d_char = GRAY_SCALE_VECTOR[0] * 2
        width = min(os.get_terminal_size()[0] // 2, 256)
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))

        vis_row, last_byte = '', -1
        for row in get_scan_curve(bin_content, width):
            for byte in row:
                if byte < 0:
                    vis_row += '  '
                    continue
                if byte != last_byte:
                    vis_row += f"{COLOR_RESET}{Visualizer.get_color_byte_view(byte)}"
                    last_byte = byte
                vis_row += d_char
            if vis_row:
                print(vis_row)
                vis_row = ''
        print(COLOR_RESET)

    def visualize_digraph_dot_plot(self, file_p: str) -> None:
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
        print(f"{DIGRAPH_VIEW_CONTROL}+{'-'*512}+{COLOR_RESET}")
        for i in range(256):
            for j in range(256):
                for index, border in enumerate(borders):
                    if digraph[i*256+j] >= border:
                        vis_row += (GRAY_SCALE_VECTOR[index] * 2)
                        break
                else:
                    vis_row += '  '
            print(f"{DIGRAPH_VIEW_CONTROL}|{vis_row}|{COLOR_RESET}")
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
        print(f"{DIGRAPH_VIEW_CONTROL}+{status_bar.ljust(512, '-')}+{COLOR_RESET}")

    def visualize_files(self) -> None:
        if self.v_type == 'ByteView':
            visualizer = self.visualize_byte_view
        if self.v_type == 'DigraphDotPlotView':
            visualizer = self.visualize_digraph_dot_plot
        for file in self.files:
            visualizer(file)
