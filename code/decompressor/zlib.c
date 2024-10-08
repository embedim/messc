#include <zlib.h>
#include <stdlib.h>
#include <stdio.h>

int mess_decompressor(const unsigned char *compressed_data, int compressed_size,
                            unsigned char *decompressed_data, int *decompressed_size)
{
    uLongf  buffer_size = compressed_size * 10;
    int result = uncompress(decompressed_data, &buffer_size, compressed_data, compressed_size);

    if (result != Z_OK) {
        return result;
    }

    *decompressed_size = buffer_size;
    return 0;
}
