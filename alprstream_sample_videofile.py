import os
from argparse import ArgumentParser
from openalpr import Alpr
from alprstream import AlprStream

parser = ArgumentParser()
parser.add_argument('--video', type=str, default=os.path.expanduser('~/Downloads/720p.mp4'))
parser.add_argument('--batch', action='store_true')
args = parser.parse_args()

def print_frame_results(json):
    """Formats JSON output if a plate was detected.

    :param json: Python dict returned from AlprStream.process_frame()
    :return None: Prints plate results + confidence to console
    """
    if len(json['results']) != 0:
        print('Epoch time: {}\nProcessing Time (ms): {:.2f}'.format(
            json['epoch_time'], json['processing_time_ms']
        ))
        d = json['results'][0]
        print('\tPlate: {} ({:.2f})\n\tRegion: {} ({:.2f})'.format(
            d['plate'], d['confidence'], d['region'], d['region_confidence']
        ))
        print('=' * 79)

def print_batch_results(batch):
    """Wrapper function to print_frame_results for batches.

    :param batch: Python list returned from AlprStream.process_batch()
    :return None: Prints plate results + confidence to console
    """
    if len(batch) != 0:
        print_frame_results(batch[0])

alpr_stream = AlprStream(10)
alpr = Alpr('us', '/etc/openalpr/alprd.conf', '/usr/share/openalpr/runtime_data')
alpr_stream.connect_video_file(args.video, 0)
print('Pointer to stream instance: ', hex(alpr_stream.alprstream_pointer))
print('Results will load below when plates are detected...\n')
print('=' * 79)

while alpr_stream.video_file_active() or alpr_stream.get_queue_size() > 0:
    if args.batch:
        print_batch_results(alpr_stream.process_batch(alpr))
    else:
        print_frame_results(alpr_stream.process_frame(alpr))
