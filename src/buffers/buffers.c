#include <ultra64.h>

#include "buffers.h"
#include "audio/psp_audio_cfg.h"

#ifndef NO_SEGMENTED_MEMORY
ALIGNED8 u8 gDecompressionHeap[0xD000]; /* (MIO0 textures: the port has no segments, so it is not used) */
#endif
/* The audio heap is written by the Media Engine (the audio runs there): 64-byte aligned and a whole number of 64-byte cache lines, so no
 * cache line is shared with other data (see tools/psp/me_linkfile.py). */
#define AUDIO_HEAP_ALIGN64(size) (((size) + 63) & ~63)
#if defined(VERSION_EU) || defined(VERSION_SH)
u8 gAudioHeap[AUDIO_HEAP_ALIGN64(DOUBLE_SIZE_ON_64_BIT(0x31200) - 0x3800 + PSP_AUDIO_LUIGI_BANK_MEM + PSP_AUDIO_LUIGI_SEQ_MEM + PSP_AUDIO_INIT_EXTRA)]
    __attribute__((aligned(64)));
#else
u8 gAudioHeap[AUDIO_HEAP_ALIGN64(DOUBLE_SIZE_ON_64_BIT(0x31200 + PSP_AUDIO_HEAP_EXTRA + PSP_AUDIO_INIT_EXTRA))] __attribute__((aligned(64)));
#endif

ALIGNED8 u8 gIdleThreadStack[0x800];
ALIGNED8 u8 gThread3Stack[0x2000];
ALIGNED8 u8 gThread4Stack[0x2000];
ALIGNED8 u8 gThread5Stack[0x2000];
#ifdef VERSION_SH
ALIGNED8 u8 gThread6Stack[0x2000];
#endif
// 0x400 bytes
ALIGNED8 u8 gGfxSPTaskStack[SP_DRAM_STACK_SIZE8];
// 0xc00 bytes for f3dex, 0x900 otherwise
ALIGNED8 u8 gGfxSPTaskYieldBuffer[OS_YIELD_DATA_SIZE];
// 0x200 bytes
ALIGNED8 struct SaveBuffer gSaveBuffer;
// 0x190a0 bytes
struct GfxPool gGfxPools[GFX_NUM_POOLS];


// Yield buffer for audio, 0x400 bytes. Stubbed out post-JP since the audio
// task never yields.
#ifdef VERSION_JP
ALIGNED8 u8 gAudioSPTaskYieldBuffer[OS_YIELD_AUDIO_SIZE];
#endif

// Probably Thread 2 stack space. Unreferenced, and stubbed out with f3dex to
// avoid an overflowing .buffers segment.
#if !defined(F3DEX_GBI_SHARED) && !defined(VERSION_EU)
ALIGNED8 u8 gUnusedThread2Stack[0x1400];
#endif
