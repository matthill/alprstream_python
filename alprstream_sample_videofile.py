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

def print_results(json):
    """Formats JSON output if a plate was detected."""
    if len(json['results']) != 0:
        print('Epoch time: {}\nProcessing Time (ms): {:.2f}'.format(
            json['epoch_time'], json['processing_time_ms']
        ))
        d = json['results'][0]
        print('\tPlate: {} ({:.2f})\n\tRegion: {} ({:.2f})'.format(
            d['plate'], d['confidence'], d['region'], d['region_confidence']
        ))
        print('=' * 79)

alpr_stream = AlprStream(10)
alpr = Alpr('us', '/etc/openalpr/alprd.conf', '/usr/share/openalpr/runtime_data')
alpr_stream.connect_video_file('/home/addison/Downloads/parkingLot-720p.mp4', 0) # Video from http://download.openalpr.com/bench/720p.mp4
print('Pointer to stream instance: ', hex(alpr_stream.alprstream_pointer))

while alpr_stream.video_file_active() or alpr_stream.get_queue_size() > 0:
    print_results(alpr_stream.process_frame(alpr))
    time.sleep(1.0)
