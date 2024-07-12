"""
vishelper
"""

import math


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

class SpaceFilling:
    @staticmethod
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

    @staticmethod
    def _get_zorder_index(y: int, x: int) -> int:
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

    @staticmethod
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
                        row.append(_list_chunk[SpaceFilling._get_zorder_index(y, x)])
                    except IndexError:
                        row.append(-1)
                if row[0] < 0:
                    break
                yield row
            i += 1

    @staticmethod
    def _get_hilbert_index(n: int, y: int, x: int) -> int:
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

    @staticmethod
    def get_hilbert_curve(_list: bytes, width: int):
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
                        row.append(_list_chunk[SpaceFilling._get_hilbert_index(width, y, x)])
                    except IndexError:
                        row.append(-1)
                if row[0] < 0:
                    break
                yield row
            i += 1


class Entropy:
    @staticmethod
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
