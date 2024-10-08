#include <stdio.h>
#include <lzma.h>
#include <stdlib.h>

int mess_decompressor(const unsigned char *compressed_data, int input_size, unsigned char *out, int *decompressed_size) {
    lzma_stream strm = LZMA_STREAM_INIT;

    strm.next_in = compressed_data;
    strm.avail_in = input_size;
    strm.next_out = out;
    strm.avail_out = *decompressed_size;

    lzma_ret ret = lzma_auto_decoder(&strm, 500 * 1024 * 1024, 0);
    if (ret != LZMA_OK) {
        return 1;
    }

    ret = lzma_code(&strm, LZMA_FINISH);

    if (ret != LZMA_OK && ret != LZMA_STREAM_END) {
        lzma_end(&strm);
        return 1;
    }

    *decompressed_size = *decompressed_size - strm.avail_out;
    lzma_end(&strm);
    return 0;
}

