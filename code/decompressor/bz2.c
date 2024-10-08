#include <stdio.h>
#include <stdlib.h>
#include <bzlib.h>

int mess_decompressor(const unsigned char *compressed_data, int compressed_size,
                            unsigned char *decompressed_data, int *decompressed_size) {
    int result;
    bz_stream stream = {
        .bzalloc = NULL,
        .bzfree = NULL,
        .opaque = NULL,
        .next_in = (char *)compressed_data,
        .avail_in = compressed_size,
        .next_out = (char *)decompressed_data,
        .avail_out = *decompressed_size
    };

    result = BZ2_bzDecompressInit(&stream, 0, 0);
    if (result != BZ_OK) {
        return result;
    }

    result = BZ2_bzDecompress(&stream);
    if (result != BZ_STREAM_END) {
        BZ2_bzDecompressEnd(&stream);
        return result;
    }

    BZ2_bzDecompressEnd(&stream);

    *decompressed_size = *decompressed_size - stream.avail_out;

    return BZ_OK;
}

