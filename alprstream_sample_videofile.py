import os
from argparse import ArgumentParser
from openalpr import Alpr
from alprstream import AlprStream
from vehicleclassifier import VehicleClassifier

parser = ArgumentParser()
parser.add_argument('--video', type=str, default=os.path.expanduser('~/Downloads/720p.mp4'))
parser.add_argument('--batch', action='store_true', help='Instead of processing individual frames')
parser.add_argument('--group', action='store_true', help='Don\'t output individual frames')
parser.add_argument('--completed', action='store_true', help='Output completed groups only')
args = parser.parse_args()

def print_frame_results(json):
    """Formats JSON output if a plate was detected.

    :param json: Python dict returned from AlprStream.process_frame()
    :return None: Prints plate results + confidence to console
    """
    if len(json['results']) != 0 and not args.group:
        print('{:-<79s}'.format('FRAME ({}) '.format(json['epoch_time'])))
        d = json['results'][0]
        print('\tPlate: {} ({:.2f})\n\tRegion: {} ({:.2f})'.format(
            d['plate'], d['confidence'], d['region'], d['region_confidence']
        ))

def print_batch_results(batch):
    """Wrapper function to print_frame_results for batches.

    :param batch: Python list returned from AlprStream.process_batch()
    :return None: Prints plate results + confidence to console
    """
    if len(batch) != 0:
        print_frame_results(batch[0])

def print_groups(groups, active=False, cache=None):
    """Format JSON output for completed plate group.

    :param list groups: Returned from AlprStream.pop_completed_groups_and_recognize_vehicle()
    :param bool active: Print active groups
    :param set cache: Already printed active groups
    :return set cache: With any new active groups added
    """

    def format_print(d, i=None, total=None):
        """
        Helper function for print_groups.

        :param dict d: JSON data for completed or active group.
        :param int i: Group number counter (only for active groups).
        :param int total: Number of active groups (only for active groups).
        :return: None, prints output.
        """
        if i is not None:
            header = 'ACTIVE GROUP {}/{} ({} - {}) '.format(i + 1, total, d['epoch_start'], d['epoch_end'])
            print('{:=<79s}'.format(header))
        else:
            header = 'COMPLETED GROUP ({} - {}) '.format(d['epoch_start'], d['epoch_end'])
            print('{:/<79s}'.format(header))
        print('\tBest Plate: {} ({:.2f})\n\tBest Region: {} ({:.2f})'.format(
            d['best_plate']['plate'],
            d['best_confidence'],
            d['best_region'],
            d['best_region_confidence']))
        if i is None:
            print('\tBody Type: {}\n\tColor: {}\n\tMake/Model: {}'.format(
                d['vehicle']['body_type'][0]['name'],
                d['vehicle']['color'][0]['name'],
                d['vehicle']['make_model'][0]['name']))

    total = len(groups)
    for i, d in enumerate(groups):
        if active:
            new = (d['epoch_start'], d['epoch_end'], d['best_plate']['plate'], d['best_region'])
            if new not in cache:
                format_print(d, i, total)
                cache.add(new)
        else:
            format_print(d)
    return cache

alpr_stream = AlprStream(10)
alpr = Alpr('us', '/etc/openalpr/openalpr.conf', '/usr/share/openalpr/runtime_data')
vehicle_classifier = VehicleClassifier('/etc/openalpr/openalpr.conf', '/usr/share/openalpr/runtime_data')
alpr_stream.connect_video_file(args.video, 0)
print('Pointer to stream instance: ', hex(alpr_stream.alprstream_pointer))
print('Results will load below when plates are detected...\n')

cache = set()
while alpr_stream.video_file_active() or alpr_stream.get_queue_size() > 0:
    if args.batch:
        print_batch_results(alpr_stream.process_batch(alpr))
    else:
        print_frame_results(alpr_stream.process_frame(alpr))
    if not args.completed:
        cache = print_groups(alpr_stream.peek_active_groups(), active=True, cache=cache)
    cache = print_groups(alpr_stream.pop_completed_groups_and_recognize_vehicle(vehicle_classifier))
