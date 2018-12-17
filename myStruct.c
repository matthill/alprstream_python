#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>

// Define structures ---------------------------------------------------------

typedef struct 
{
    bool image_available;
    bool queue_empty;
    unsigned char jpeg_bytes; // this is a std::vector in Cpp version
    int64_t frame_epoch_time_ms;
    int64_t frame_number;
    char* results; // techincally type AlprResults and converted to JSON
} RF;

typedef struct
{
    bool image_available;
    char* jpeg_bytes;
    int64_t jpeg_bytes_size;
    int64_t frame_epoch_time_ms;
    int64_t frame_number;
    char* results_str;
} AlprStreamRF;

// Init functions ------------------------------------------------------------


// Create RecognizedFrame rf (would be done by Alpr instance)
RecognizedFrame rf =
{
    true,
    false,
    char[] { 0x00, 0x11, 0x22 },
    int64_t 1234,
    int64_t 0,
    char[] {}
}


/*
AlprStreamRecognizedFrame* make_responsestruct(RecognizedFrame& rf) 
{
    AlprStreamRecognizedFrame* response = 
};
*/

// Transform rf into AlprStreamRecognizedFrame asrf
// Return asrf from process_frame()

TestStruct* init_struct(bool image_available, char* jpeg_bytes, int64_t jpeg_bytes_size, int64_t frame_epoch_time_ms, int64_t frame_number, char* results_str) 
{
    TestStruct* p;
    TestStruct initial = {image_available, jpeg_bytes, jpeg_bytes_size, frame_epoch_time_ms, frame_number, results_str};
    p = malloc(sizeof(TestStruct));
    *p = initial;
    return p;
}
