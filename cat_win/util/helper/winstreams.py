"""
winstreams
credit: https://github.com/RobinDavid/pyADS
"""

try:
    from ctypes import windll
    from ctypes import Structure, Union, byref
    from ctypes import c_wchar, c_wchar_p, c_ulong, c_longlong, c_void_p

    WINSTREAMS_MODULE_ERROR = False

    kernel32 = windll.kernel32

    class LARGE_INTEGER_UNION(Structure):
        _fields_ = [
            ("LowPart", c_ulong),
            ("HighPart", c_ulong),
            ]

    class LARGE_INTEGER(Union):
        _fields_ = [
            ("large1", LARGE_INTEGER_UNION),
            ("large2", LARGE_INTEGER_UNION),
            ("QuadPart",    c_longlong),
            ]

    class WIN32_FIND_STREAM_DATA(Structure):
        _fields_ = [
            ("StreamSize", LARGE_INTEGER),
            ("cStreamName", c_wchar * 296),
            ]
except ImportError:
    WINSTREAMS_MODULE_ERROR = True


class WinStreams:
    def __init__(self, filename: str):
        self.filename = filename
        self.streams = self.init_streams()

    def init_streams(self):
        if WINSTREAMS_MODULE_ERROR:
            return []

        file_infos = WIN32_FIND_STREAM_DATA()
        streamlist = []

        findFirstStreamW = kernel32.FindFirstStreamW
        findFirstStreamW.restype = c_void_p

        myhandler = kernel32.FindFirstStreamW(c_wchar_p(self.filename), 0, byref(file_infos), 0)
        p = c_void_p(myhandler)

        if file_infos.cStreamName:
            streamname = file_infos.cStreamName.split(":")[1]
            if streamname and not self.filename.endswith(':'+streamname):
                streamlist.append(streamname)

            while kernel32.FindNextStreamW(p, byref(file_infos)):
                streamname = file_infos.cStreamName.split(":")[1]
                if not self.filename.endswith(':'+streamname):
                    streamlist.append(streamname)

        kernel32.FindClose(p)  # Close the handle

        return streamlist


    def __iter__(self):
        return iter(self.streams)
