# -*- coding: utf-8 -*-
import ctypes
import json
import platform
from threading import Lock

mutex = Lock()

# We need to do things slightly differently for Python 2 vs. 3
# ... because the way str/unicode have changed to bytes/str
if platform.python_version_tuple()[0] == "2":
    # Using Python 2
    bytes = str
    _PYTHON_3 = False
else:
    # Assume using Python 3+
    unicode = str
    _PYTHON_3 = True

def _convert_to_charp(string):
    # Prepares function input for use in c-functions as char*
    if type(string) == unicode:
        return string.encode("UTF-8")
    elif type(string) == bytes:
        return string

def _convert_from_charp(charp):
    # Prepares char* output from c-functions into Python strings
    if _PYTHON_3 and type(charp) == bytes:
        return charp.decode("UTF-8")
    else:
        return charp

class AlprStreamRecognizedFrameC(ctypes.Structure):
    _fields_ = [("image_available",     ctypes.c_bool),
                ("jpeg_bytes",          ctypes.c_char_p),
                ("jpeg_bytes_size",     ctypes.c_longlong),
                ("frame_epoch_time_ms", ctypes.c_longlong),
                ("frame_number",        ctypes.c_longlong),
                ("results_str",         ctypes.c_char_p)]

class AlprStreamRecognizedBatchC(ctypes.Structure):
    _fields_ = [("results_size",  ctypes.c_int),
                ("results_array", ctypes.c_void_p),
                ("batch_results", ctypes.c_char_p)]

class AlprStream:
    def __init__(self, frame_queue_size, use_motion_detection=1):
        """
        Initializes an AlprStream instance in memory.
        :param frame_queue_size: The size of the video buffer to be filled by incoming video frames
        :param use_motion_detection: Whether or not to enable motion detection on this stream
        """

        # platform.system() calls popen which is not threadsafe on Python 2.x
        mutex.acquire()
        try:
            # Load the .dll for Windows and the .so for Unix-based
            if platform.system().lower().find("windows") != -1:
                self._alprstreampy_lib = ctypes.cdll.LoadLibrary("libalprstream.dll")
            elif platform.system().lower().find("darwin") != -1:
                self._alprstreampy_lib = ctypes.cdll.LoadLibrary("libalprstream.dylib")
            else:
                self._alprstreampy_lib = ctypes.cdll.LoadLibrary("libalprstream.so.3")
        except OSError as e:
            nex = OSError("Unable to locate the ALPRStream library. Please make sure that ALPRStream is properly "
                          "installed on your system and that the libraries are in the appropriate paths.")
            if _PYTHON_3:
                nex.__cause__ = e
            raise nex

        self.is_loaded = False

        self._initialize_func = self._alprstreampy_lib.alprstream_init
        self._initialize_func.restype = ctypes.c_void_p
        self._initialize_func.argtypes = [ctypes.c_uint, ctypes.c_uint]

        self._dispose_func = self._alprstreampy_lib.alprstream_cleanup
        self._dispose_func.argtypes = [ctypes.c_void_p]
        self._dispose_func.restype = ctypes.c_bool

        self._get_queue_size_func = self._alprstreampy_lib.alprstream_get_queue_size
        self._get_queue_size_func.restype = ctypes.c_uint
        self._get_queue_size_func.argtypes = [ctypes.c_void_p]

        self._connect_video_stream_url_func = self._alprstreampy_lib.alprstream_connect_video_stream_url
        self._connect_video_stream_url_func.restype = ctypes.c_void_p
        self._connect_video_stream_url_func.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

        self._disconnect_video_stream_func = self._alprstreampy_lib.alprstream_disconnect_video_stream
        self._disconnect_video_stream_func.restype = ctypes.c_void_p
        self._disconnect_video_stream_func.argtypes = [ctypes.c_void_p]

        self._connect_video_file_func = self._alprstreampy_lib.alprstream_connect_video_file
        self._connect_video_file_func.restype = ctypes.c_void_p
        self._connect_video_file_func.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint]

        self._disconnect_video_file_func = self._alprstreampy_lib.alprstream_disconnect_video_file
        self._disconnect_video_file_func.restype = ctypes.c_void_p
        self._disconnect_video_file_func.argtypes = [ctypes.c_void_p]

        self._video_file_active_func = self._alprstreampy_lib.alprstream_video_file_active
        self._video_file_active_func.restype = ctypes.c_uint
        self._video_file_active_func.argtypes = [ctypes.c_void_p]

        self._process_frame_func = self._alprstreampy_lib.alprstream_process_frame
        self._process_frame_func.restype = ctypes.POINTER(AlprStreamRecognizedFrameC)
        self._process_frame_func.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        self._free_frame_response_func = self._alprstreampy_lib.alprstream_free_frame_response
        self._free_frame_response_func.restype = ctypes.POINTER(AlprStreamRecognizedFrameC)
        self._free_frame_response_func.argtypes = [ctypes.c_void_p]

        self._push_frame_encoded_func = self._alprstreampy_lib.alprstream_push_frame
        self._push_frame_encoded_func.restype = ctypes.c_uint
        self._push_frame_encoded_func.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_longlong, ctypes.c_uint]

        self._push_frame_func = self._alprstreampy_lib.alprstream_push_frame
        self._push_frame_func.restype = ctypes.c_uint
        self._push_frame_func.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]

        self._process_batch_func = self._alprstreampy_lib.alprstream_process_batch
        self._process_batch_func.restype = ctypes.POINTER(AlprStreamRecognizedBatchC)
        self._process_batch_func.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        self._free_batch_response_func = self._alprstreampy_lib.alprstream_free_batch_response
        self._free_batch_response_func.restype = ctypes.c_void_p
        self._free_batch_response_func.argtypes = [ctypes.POINTER(AlprStreamRecognizedBatchC)]

        self._pop_completed_groups_func = self._alprstreampy_lib.alprstream_pop_completed_groups
        self._pop_completed_groups_func.restype = ctypes.c_void_p
        self._pop_completed_groups_func.argtypes = [ctypes.c_void_p]

        self._free_response_string_func = self._alprstreampy_lib.alprstream_free_response_string
        self._free_response_string_func.argtypes = [ctypes.c_void_p]

        self._peek_active_groups_func = self._alprstreampy_lib.alprstream_peek_active_groups
        self._peek_active_groups_func.restype = ctypes.c_char_p
        self._peek_active_groups_func.argtypes = [ctypes.c_void_p]

        self._combine_grouping_func = self._alprstreampy_lib.alprstream_combine_grouping
        self._combine_grouping_func.restype = ctypes.c_void_p
        self._combine_grouping_func.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        self._set_uuid_format_func = self._alprstreampy_lib.alprstream_set_uuid_format
        self._set_uuid_format_func.restype = ctypes.c_void_p
        self._set_uuid_format_func.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

        self._set_env_parameters_func = self._alprstreampy_lib.alprstream_set_env_parameters
        self._set_env_parameters_func.restype = ctypes.c_void_p
        self._set_env_parameters_func.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]

        self._set_detection_mask_encoded_func = self._alprstreampy_lib.alprstream_set_detection_mask
        self._set_detection_mask_encoded_func.restype = ctypes.c_void_p
        self._set_detection_mask_encoded_func.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_longlong]

        self._set_detection_mask_func = self._alprstreampy_lib.alprstream_set_detection_mask
        self._set_detection_mask_func.restype = ctypes.c_void_p
        self._set_detection_mask_func.argypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_int, ctypes.c_int, ctypes.c_int]

        self._set_jpeg_compression_func = self._alprstreampy_lib.alprstream_set_jpeg_compression
        self._set_jpeg_compression_func.restype = ctypes.c_void_p
        self._set_jpeg_compression_func.argtypes = [ctypes.c_void_p, ctypes.c_int]

        self._set_encode_jpeg_func = self._alprstreampy_lib.alprstream_set_encode_jpeg
        self._set_encode_jpeg_func.restype = ctypes.c_void_p
        self._set_encode_jpeg_func.argtypes = [ctypes.c_void_p, ctypes.c_int]

        self.alprstream_pointer = self._initialize_func(frame_queue_size, use_motion_detection)

    def initialize(self, frame_queue_size, use_motion_detection=True):
        self.alprstream_init(frame_queue_size, use_motion_detection)
        self.is_loaded = True

    def get_queue_size(self):
        """
        Check the size of the video buffer
        :return: The total number of images waiting to be processed on the video buffer
        """
        size = self._get_queue_size_func(self.alprstream_pointer)
        return size

    def connect_video_stream_url(self, url, gstreamer_pipeline_format=""):
        """
        Spawns a thread that connects to the specified RTSP/MJPEG URL The thread continually fills the processing queue with images from the stream
        :param: url: the full URL to be used to connect to the video stream
        :param: gstreamer_pipeline_format: An optional override for the GStreamer format. Use {url} for a marker to substitude the url value
        """
        url = _convert_to_charp(url)
        gstreamer_pipeline_format = _convert_to_charp(gstreamer_pipeline_format)
        self._connect_video_stream_url_func(self.alprstream_pointer, url, gstreamer_pipeline_format)

    def disconnect_video_stream(self):
        """
        Disconnect the video stream if you no longer wish for it to push frames to the video buffer.
        """
        self._disconnect_video_stream_func(self.alprstream_pointer)

    def connect_video_file(self, video_file_path, video_start_time):
        """
        Spawns a thread that fills the processing queue with frames from a video file The thread will slow down to make sure that it does not overflow the queue The “video_start_time” is used to us with the epoch start time of of the video
        :param video_file_path: The location on disk to the video file.
        :param video_start_time: The start time of the video in epoch ms. This time is used as an offset for identifying the epoch time for each frame in the video
        """
        video_file_path = _convert_to_charp(video_file_path)
        self._connect_video_file_func(self.alprstream_pointer, video_file_path, video_start_time)

    def disconnect_video_file(self):
        """
        If you wish to stop the video, calling this function will remove it from the stream
        """
        self._disconnect_video_file_func(self.alprstream_pointer)

    def video_file_active(self):
        """
        Check the status of the video file thread
        :return: True if currently active, false if inactive or complete
        """
        status = self._video_file_active_func(self.alprstream_pointer)
        return status

    def get_stream_url(self):
        """
        Get the stream URL.
        :return: the stream URL that is currently being used to stream
        """
        url = self._get_stream_url_func(self.alprstream_pointer)
        url = _convert_to_charp(url)
        return url

    def get_video_file_fps(self):
        """
        Get the frames per second for the video file.
        return: Get the frames per second for the video file.
        """
        frames = self._get_video_file_fps_func(self.alprstream_pointer)
        return frames

    def push_frame(self, pixelData, bytesPerPixel, imgWidth, imgHeight, frame_epoch_time=-1):
        """
        Push raw image data onto the video input buffer.
        :param pixelData: raw image bytes for BGR channels
        :param bytesPerPixel: Number of bytes for each pixel (e.g., 3)
        :param imgWidth: Width of the image in pixels
        :param imgHeight: Height of the image in pixels
        :param frame_epoch_time: The time when the image was captured. If not specified current time will be used
        :return: The video input buffer size after adding this image
        """
        pixelData = _convert_to_charp(pixelData)
        videoBufferSize = self._push_frame_func(self.alprstream_pointer, pixelData, bytesPerPixel, imgWidth, imgHeight,
                                                frame_epoch_time)
        return videoBufferSize

    def set_encode_jpeg(self, always_return_jpeg):
        """
        By default, OpenALPR only encodes/returns a JPEG image if a plate is found
        this setting forces the JPEG encoder to always encode or never encode.
        Encoding a JPEG has some performance impact.  When processing on GPU,
        the encoding happens on CPU background threads.  Disabling this setting
        (if the JPEG images are not used) will reduce CPU usage.
        If always_return_jpeg is set to never, vehicle recognition will not function correctly
        :param always_return_jpeg:0=Never, 1=On Found Plates, 2=Alway
        :return:
        """
        return self._set_encode_jpeg_func(self.alprstream_pointer, always_return_jpeg)

    def _convert_char_ptr_to_json(self, char_ptr):
        json_data = ctypes.cast(char_ptr, ctypes.c_char_p).value
        json_data = _convert_from_charp(json_data)
        response_obj = json.loads(json_data)
        self._free_response_string_func(ctypes.c_void_p(char_ptr))
        return response_obj

    def _convert_bytes_to_json(self, bytes):
        return json.loads(bytes.decode('utf-8'))

    def pop_completed_groups(self):
        """
        If there are any groups that are complete, they will be returned in an array
        and removed from the grouping queue
        @return a vector containing all completed plate groups
        :return:
        """
        ptr = self._pop_completed_groups_func(self.alprstream_pointer)
        json_result = self._convert_char_ptr_to_json(ptr)
        
        return json_result

    def peek_active_groups(self):
        """
        Checks the grouping list for active groups.  Calling this function does not
        remove any entries from the grouping queue.
        @return a full list of all currently active groups.
        :return:
        """
        bytes = self._peek_active_groups_func(self.alprstream_pointer)
        results = self._convert_bytes_to_json(bytes)
        return results

    def combine_grouping(self, other_stream):
        """
        Combine plate grouping across cameras.  This is useful if one or more cameras are
        looking at roughly the same (i.e., from different angles), and you want to combine the group results.
        @param other_stream another AlprStream pointer for the grouping to be combined
        :return:
        """
        return self._combine_grouping_func(self.alprstream_pointer, other_stream)

    def set_uuid_format(self, format):
        """
        Sets the format used for generating UUIDs.  Default is "{time}-{random}"
        Valid options are:
        {time} - epoch_ms time the image was received
        {frame} - Frame number (starts at 0)
        {camera}, {company_uuid}, {agent_uid} - Any of the values specified in set_env_parameters
        {random} - a 16 character random string
        :param format: A string containing the UUID format
        :return:
        """
        format = _convert_to_charp(format)
        self.set_uuid_format_func(self.alprstream_pointer, format)

    def process_frame(self, alpr_instance):
        struct_response = self._process_frame_func(self.alprstream_pointer, alpr_instance.alpr_pointer)
        results = self._convert_bytes_to_json(struct_response.contents.results_str)
        self._free_frame_response_func(struct_response)
        return results

    def process_batch(self, alpr_instance):
        """
        Process the image at the front of the queue and return the individual results.
        This function is most useful when using GPU acceleration.  Processing frames in
        a batch more efficiently uses GPU resources.
        You should make sure that the video buffer size for this AlprStream object is
        greater than or equal to the configured GPU batch size (in openalpr.conf).
        :param: alpr The Alpr instance that you wish to use for processing the images
        :return: An array of the results for all recognized frames that were processed
        """
        struct_response = self._process_batch_func(self.alprstream_pointer, alpr_instance.alpr_pointer)
        results = self._convert_bytes_to_json(struct_response.contents.batch_results)
        self._free_batch_response_func(struct_response)
        return results

    def __del__(self):
        if self.is_loaded:
            self.is_loaded = False
            self._dispose_func(self.alprstream_pointer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_loaded:
            self.is_loaded = False
            self._dispose_func(self.alprstream_pointer)
