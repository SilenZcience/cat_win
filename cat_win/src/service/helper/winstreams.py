"""
winstreams
credit: https://github.com/RobinDavid/pyADS
"""

from pathlib import Path
try:
    import ctypes

    kernel32 = ctypes.windll.kernel32 # throws AttributeError on non-Windows OS
    class LARGE_INTEGER_UNION(ctypes.Structure):
        _fields_ = [
            ("LowPart", ctypes.c_ulong),
            ("HighPart", ctypes.c_ulong),
        ]

    class LARGE_INTEGER(ctypes.Union):
        _fields_ = [
            ("large1", LARGE_INTEGER_UNION),
            ("large2", LARGE_INTEGER_UNION),
            ("QuadPart",    ctypes.c_longlong),
        ]

    class WIN32_FIND_STREAM_DATA(ctypes.Structure):
        _fields_ = [
            ("StreamSize", LARGE_INTEGER),
            ("cStreamName", ctypes.c_wchar * 296),
        ]

    WINSTREAMS_MODULE_ERROR = False
except AttributeError:
    WINSTREAMS_MODULE_ERROR = True


class WinStreams:
    """
    WinStreams
    """
    def __init__(self, filename: Path):
        self.filename = str(filename)
        self.streams = self.init_streams()

    def init_streams(self):
        """
        find the winstreams
        """
        if WINSTREAMS_MODULE_ERROR:
            return []

        file_infos = WIN32_FIND_STREAM_DATA()
        streamlist = []

        findFirstStreamW = kernel32.FindFirstStreamW
        findFirstStreamW.restype = ctypes.c_void_p

        myhandler = kernel32.FindFirstStreamW(ctypes.c_wchar_p(self.filename),
                                              0, ctypes.byref(file_infos), 0)
        p = ctypes.c_void_p(myhandler)

        if file_infos.cStreamName:
            streamname = file_infos.cStreamName.split(":")[1]
            if streamname:
                streamlist.append(streamname)

            while kernel32.FindNextStreamW(p, ctypes.byref(file_infos)):
                streamlist.append(file_infos.cStreamName.split(":")[1])

        kernel32.FindClose(p)  # Close the handle

        return streamlist


    def __iter__(self):
        return iter(self.streams)
