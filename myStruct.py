import ctypes
import os
import re

class PyStruct(ctypes.Structure):
    _fields_ = [("image_available",     ctypes.c_bool),
                ("jpeg_bytes",          ctypes.c_char_p),
                ("jpeg_bytes_size",     ctypes.c_longlong),
                ("frame_epoch_time_ms", ctypes.c_longlong),
                ("frame_number",        ctypes.c_longlong),
                ("results_str",         ctypes.c_char_p)]

lib = ctypes.cdll.LoadLibrary(os.path.abspath('libstruct.so'))
_init_struct = lib.init_struct
_init_struct.argtypes = [ctypes.c_bool, ctypes.c_char_p,
                         ctypes.c_longlong, ctypes.c_longlong,
                         ctypes.c_longlong, ctypes.c_char_p]
_init_struct.restype = ctypes.POINTER(PyStruct)

myStruct = _init_struct(True, ctypes.c_char_p(b'JPG bytes here'),
                        1, 2, 3, ctypes.c_char_p(b'JSON results here'))
out = [print('{} = {}'.format(d, getattr(myStruct.contents, d)))
       for d in dir(myStruct.contents)
       if not re.match('^_', d)]
