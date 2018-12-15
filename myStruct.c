#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>

typedef struct 
{
    bool image_available;
    char* jpeg_bytes;
    int64_t jpeg_bytes_size;
    int64_t frame_epoch_time_ms;
    int64_t frame_number;
    char* results_str;
} TestStruct;

TestStruct* init_struct(bool image_available, char* jpeg_bytes, int64_t jpeg_bytes_size, int64_t frame_epoch_time_ms, int64_t frame_number, char* results_str) 
{
    TestStruct* p;
    TestStruct initial = {image_available, jpeg_bytes, jpeg_bytes_size, frame_epoch_time_ms, frame_number, results_str};
    p = malloc(sizeof(TestStruct));
    *p = initial;
    return p;
}
