import ctypes
import time
from openalpr import Alpr
from alprstream import AlprStream

class AlprStreamRecognizedFrameC(ctypes.Structure):
    _fields_ = [("image_available",     ctypes.c_bool),
                ("jpeg_bytes",          ctypes.c_void_p),
                ("jpeg_bytes_size",     ctypes.c_longlong),
                ("frame_epoch_time_ms", ctypes.c_longlong),
                ("frame_number",        ctypes.c_longlong),
                ("results_str",         ctypes.c_char_p)]

alpr_stream = AlprStream(10)
alpr = Alpr('us', '/etc/openalpr/alprd.conf', '/usr/share/openalpr/runtime_data')
alpr_stream.connect_video_file('/home/addison/Downloads/parkingLot-720p.mp4', 0)
print('Pointer to stream instance: ', alpr_stream.alprstream_pointer)

while alpr_stream.video_file_active() or alpr_stream.get_queue_size() > 0:
    single_frame = alpr_stream.process_batch(alpr)
    group_results = alpr_stream.pop_completed_groups()
    print('=' * 79)
    time.sleep(1.0)
