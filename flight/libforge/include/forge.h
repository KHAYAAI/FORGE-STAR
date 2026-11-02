/*
 * libforge: FORGE STAR payload store-and-forward core (C99, no malloc, no OS).
 *
 * Byte-for-byte compatible with the ground side in forgestar/frames.py (frame v1)
 * and forgestar/fec.py (link blocks: ASM + randomised RS(255,223) codewords).
 * Shared test vectors live in flight/libforge/test/vectors/ (generated from Python).
 */
#ifndef FORGE_H
#define FORGE_H
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define FORGE_FRAME_MAGIC    0xF5u
#define FORGE_FRAME_VERSION  1u
#define FORGE_FRAME_MAX      4096u
#define FORGE_FRAME_HDR      16u
#define FORGE_REC_HDR        18u
#define FORGE_PAYLOAD_MAX    200u
#define FORGE_RS_N           255u
#define FORGE_RS_K           223u
#define FORGE_LINK_MAX_CW    20u
#define FORGE_LINK_MAX       (4u + FORGE_LINK_MAX_CW * FORGE_RS_N)

/* ---- one stored device message ---- */
typedef struct {
    uint32_t short_id;      /* crc32 of the device name */
    uint32_t t_created;     /* unix seconds */
    int32_t  lat_e5;        /* latitude  x 1e5 */
    int32_t  lon_e5;        /* longitude x 1e5 */
    uint16_t payload_len;
    uint8_t  payload[FORGE_PAYLOAD_MAX];  /* compact JSON (CBOR later) */
} forge_record_t;

uint32_t forge_crc32(const uint8_t *data, size_t len);
uint32_t forge_short_id(const char *device_name);

/* Encode records[first..first+count) into one v1 frame, stopping before FORGE_FRAME_MAX.
 * Returns bytes written (0 on error); *used = records consumed. */
size_t forge_frame_encode(uint8_t *out, size_t out_cap, uint16_t sat_id, uint32_t seq, uint32_t t_downlink,
                          const forge_record_t *records, size_t count, int more_follow, size_t *used);

/* ---- link layer ---- */
/* RS(255,223), CCSDS parameters and CCSDS dual-basis symbols (interoperable with libfec encode_rs_ccsds). */
void   forge_rs_encode(const uint8_t data[FORGE_RS_K], uint8_t parity[FORGE_RS_N - FORGE_RS_K]);
void   forge_randomise(uint8_t *buf, size_t len);   /* CCSDS PN, restarts at 0 for each call */
/* Wrap a frame into ASM + randomised RS codewords. Returns bytes written, 0 on error. */
size_t forge_link_encode(uint8_t *out, size_t out_cap, const uint8_t *frame, size_t frame_len);

/* ---- onboard store-and-forward buffer (ring, fixed capacity) ---- */
#ifndef FORGE_SF_CAPACITY
#define FORGE_SF_CAPACITY 512u
#endif
typedef struct {
    forge_record_t rec[FORGE_SF_CAPACITY];
    uint32_t head, count, dropped;
    uint32_t seq;         /* next frame sequence number */
    uint16_t sat_id;
} forge_sf_t;

void   forge_sf_init(forge_sf_t *sf, uint16_t sat_id);
/* Store one message. Returns 1 if stored, 0 if the buffer was full (counted in dropped). */
int    forge_sf_store(forge_sf_t *sf, const forge_record_t *r);
/* Produce the next downlink link block from the oldest stored records.
 * Returns link-block bytes written (0 when empty); records sent are removed. */
size_t forge_sf_next_link_block(forge_sf_t *sf, uint32_t t_downlink, uint8_t *out, size_t out_cap,
                                uint32_t *records_sent);

#ifdef __cplusplus
}
#endif
#endif
