"""
visualizer
"""

import math
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

ENTROPY_VERY_HIGH    = ColorOptions.Fore['WHITE']
ENTROPY_HIGH         = ColorOptions.Fore['YELLOW']
ENTROPY_MEDIUM       = ColorOptions.Fore['RED']
ENTROPY_LOW          = ColorOptions.Fore['BLUE']
ENTROPY_VERY_LOW     = ColorOptions.Fore['BLACK']

COLOR_RESET          = ColorOptions.Style['RESET']


def get_fit_terminal_square(length: int, width: int) -> int:
    """
    calculate the best fitting square size.
    
    Parameters:
    length (int):
        the length of the data stream
    width (int):
        the max width displayable on the console window

    Returns:
        largest fitting power of two
    """
    w = 1
    # find the largest power of two that fits in the (console window) width
    # and when squared does not exceed the (data stream) length
    while (w*w*4) <= length and w*2 <= width: # w*w*4 = (w*2)**2
        w *= 2
    return w

def get_scan_curve(_list: bytes, width: int):
    """
    break a given list into chunks of a given size.
    every other chunk is inverted to generate the scan curve pattern.
    
    Parameters:
    _list (iterable):
        the list or bytearray to put in pattern
    width (int):
        the max displayable width
    
    Yields:
    _list_chunk
        the next chunk to display
    """
    _length = len(_list)
    width = get_fit_terminal_square(_length, width)

    i = 0
    while i*width <= _length:
        if not i % 2:
            yield _list[i*width:(i+1)*width]
        else:
            r_list = list(reversed(_list[i*width:(i+1)*width]))
            r_list = [-1] * (width-len(r_list)) + r_list
            yield r_list
        i += 1

def get_zorder_index(y: int, x: int) -> int:
    """
    calculate the z-order curve index.
    
    Parameters:
    y (int):
        the row
    x (int):
        the column
    
    Returns:
    z (int):
        the z-order index
    """
    z = 0
    for i in range(max(x.bit_length(), y.bit_length())):
        z |= (x & (1 << i)) << i | (y & (1 << i)) << (i + 1)
    return z

def get_zorder_curve(_list: bytes, width: int):
    """
    break the given list into chunks of a given size.
    
    Parameters:
    _list (iterable):
        the list or bytearray to put in pattern
    width (int):
        the max displayable width
    
    Yields:
    _list_chunk
        the next chunk to display
    """
    _length = len(_list)
    width = get_fit_terminal_square(_length, width)

    i, n = 0, width**2
    while i*n <= _length:
        _list_chunk = _list[i*n:(i+1)*n]
        for y in range(width):
            row = []
            for x in range(width):
                try:
                    row.append(_list_chunk[get_zorder_index(y, x)])
                except IndexError:
                    row.append(-1)
            if row[0] < 0:
                break
            yield row
        i += 1

def get_hilbert_index(n: int, y: int, x: int) -> int:
    """
    calculate the hilbert curve index.
    
    Parameters:
    n (int):
        the order of the hilbert curve
    y (int):
        the row
    x (int):
        the column

    Returns:
    d (int):
        the hilbert curve index
    """
    d = 0
    s = n // 2
    while s > 0:
        rx = (x & s) > 0
        ry = (y & s) > 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x = n - 1 - x
                y = n - 1 - y
            x, y = y, x
        s = s // 2
    return d

def get_hilbert_curve(_list, width: int):
    """
    break the given list into chunks of a given size.
    
    Parameters:
    _list (iterable):
        the list or bytearray to put in pattern
    width (int):
        the max displayable width
    
    Yields:
    _list_chunk
        the next chunk to display
    """
    _length = len(_list)
    width = get_fit_terminal_square(_length, width)

    i, n = 0, width**2
    while i*n <= _length:
        _list_chunk = _list[i*n:(i+1)*n]
        for y in range(width):
            row = []
            for x in range(width):
                try:
                    row.append(_list_chunk[get_hilbert_index(width, y, x)])
                except IndexError:
                    row.append(-1)
            if row[0] < 0:
                break
            yield row
        i += 1

def normalized_shannon_entropy(data: bytes) -> int:
    frame_window = 128
    fmin1 = frame_window-1
    data = list(data) + [0]*(frame_window-1)

    if len(data) < frame_window:
        return []

    counter = dict(zip(range(256), [0]*256))

    # first frame:
    for i in range(frame_window):
        counter[data[i]] += 1
    probabilities = [count / frame_window for count in counter.values()]
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0) * 14.286

    # rest frames
    for i in range(1, len(data)-fmin1):
        counter[data[i-    1]] -= 1
        counter[data[i+fmin1]] += 1
        probabilities[data[i-    1]] = counter[data[i-    1]] / 128
        probabilities[data[i+fmin1]] = counter[data[i+fmin1]] / 128
        data[i-1] = int(entropy)
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0) * 14.286
    data[len(data)-frame_window] = int(entropy)

    return data[:-fmin1]


class Visualizer:
    """
    visualize given files in different ways.
    """
    debug: bool = False

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
            return ENTROPY_VERY_HIGH
        if entropy > 60:
            return ENTROPY_HIGH
        if entropy > 40:
            return ENTROPY_MEDIUM
        if entropy > 20:
            return ENTROPY_LOW
        return ENTROPY_VERY_LOW

    def visualize_byte_view(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using the scan curve.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        d_char = GRAY_SCALE_VECTOR[0] * 2
        width = os.get_terminal_size()[0] // 2
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
                vis_row += str(byte).rjust(4) if Visualizer.debug else d_char
            if vis_row:
                print(vis_row)
                vis_row = ''
        print(COLOR_RESET)

    def visualize_zorder_curve_view(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using a z-order curve view.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        d_char = GRAY_SCALE_VECTOR[0] * 2
        width = os.get_terminal_size()[0] // 2
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))

        vis_row, last_byte = '', -1
        for row in get_zorder_curve(bin_content, width):
            for byte in row:
                if byte < 0:
                    vis_row += '  '
                    continue
                if byte != last_byte:
                    vis_row += f"{COLOR_RESET}{Visualizer.get_color_byte_view(byte)}"
                    last_byte = byte
                vis_row += str(byte).rjust(4) if Visualizer.debug else d_char
            if vis_row:
                print(vis_row)
                vis_row = ''
            continue
        print(COLOR_RESET)

    def visualize_hilbert_curve_view(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using a hilbert curve view.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        d_char = GRAY_SCALE_VECTOR[0] * 2
        width = os.get_terminal_size()[0] // 2
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))

        vis_row, last_byte = '', -1
        for row in get_hilbert_curve(bin_content, width):
            for byte in row:
                if byte < 0:
                    vis_row += '  '
                    continue
                if byte != last_byte:
                    vis_row += f"{COLOR_RESET}{Visualizer.get_color_byte_view(byte)}"
                    last_byte = byte
                vis_row += str(byte).rjust(4) if Visualizer.debug else d_char
            if vis_row:
                print(vis_row)
                vis_row = ''
            continue
        print(COLOR_RESET)

    def visualize_shannon_entropy(self, file_p: str) -> None:
        """
        visualize all bytes in a given file.
        display the visualization using the shannon entropy.

        Parameters:
        file_p (str):
            a string representation of a file (-path)
        """
        d_char = GRAY_SCALE_VECTOR[0] * 2
        width = os.get_terminal_size()[0] // 2
        bin_content = IoHelper.read_file(file_p, True).__getitem__(slice(*self.truncate))
        bin_content = normalized_shannon_entropy(bin_content)

        vis_row, last_byte = '', -1
        for row in get_hilbert_curve(bin_content, width):
            for byte in row:
                if byte < 0:
                    vis_row += '  '
                    continue
                if byte != last_byte:
                    vis_row += f"{COLOR_RESET}{Visualizer.get_color_entropy(byte)}"
                    last_byte = byte
                vis_row += str(byte).rjust(4) if Visualizer.debug else d_char
            if vis_row:
                print(vis_row)
                vis_row = ''
            continue
        print(COLOR_RESET)

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
