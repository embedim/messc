#pragma once
#include "stdio.h"

#ifdef MESSC
    #include "mess_position.h"
    extern int mess_decompressor();
    static int run_init_mess() {
        int size;
        mess_decompressor(MESS_COMPRESSED_ARRAY, MESS_SIZE_COMPRESED_ARRAY, MESS_DECOMPRESSED_ARRAY, &size);
        return size;
    }
#endif

#ifdef MESSC
    #define MESS_DEFINE() char MESS_DECOMPRESSED_ARRAY[MESS_SIZE_ORIGIN_ARRAY +1]
    #define MESS_INIT() run_init_mess()
#else 
    #define MESS_DEFINE()
    #define MESS_INIT()
#endif



