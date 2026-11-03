/* libforge unit tests: byte-exact against the Python reference (vectors.h). */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "forge.h"
#include "vectors.h"

static int fails = 0;
#define CHECK(c, msg) do { if (!(c)) { printf("FAIL: %s (line %d)\n", msg, __LINE__); fails++; } else printf("ok   %s\n", msg); } while (0)

static void load(forge_record_t *r, int i) {
    memset(r, 0, sizeof *r);
    r->short_id = VEC_RECS[i].sid; r->t_created = VEC_RECS[i].t;
    r->lat_e5 = VEC_RECS[i].lat; r->lon_e5 = VEC_RECS[i].lon;
    r->payload_len = (uint16_t)strlen(VEC_RECS[i].payload);
    memcpy(r->payload, VEC_RECS[i].payload, r->payload_len);
}

int main(int argc, char **argv) {
    forge_record_t recs[VEC_NREC];
    for (int i = 0; i < VEC_NREC; i++) load(&recs[i], i);

    CHECK(forge_short_id(VEC_NAMES[0]) == VEC_RECS[0].sid, "short id = crc32(name) matches Python zlib.crc32");

    static uint8_t frame[FORGE_FRAME_MAX]; size_t used = 0;
    size_t flen = forge_frame_encode(frame, sizeof frame, VEC_SAT, VEC_SEQ, VEC_TDL, recs, VEC_NREC, 0, &used);
    CHECK(flen == sizeof VEC_FRAME && used == VEC_NREC, "frame length matches");
    CHECK(memcmp(frame, VEC_FRAME, sizeof VEC_FRAME) == 0, "frame bytes identical to Python");

    static uint8_t link[FORGE_LINK_MAX];
    size_t llen = forge_link_encode(link, sizeof link, VEC_FRAME, sizeof VEC_FRAME);
    CHECK(llen == sizeof VEC_LINK, "link block length matches");
    CHECK(memcmp(link, VEC_LINK, sizeof VEC_LINK) == 0, "link block (RS + randomiser + ASM) identical to Python");

    uint8_t pn[8] = {0}; forge_randomise(pn, 8);
    static const uint8_t pn_ref[8] = {0xFF, 0x48, 0x0E, 0xC0, 0x9A, 0x0D, 0x70, 0xBC};
    CHECK(memcmp(pn, pn_ref, 8) == 0, "PN sequence = CCSDS 131.0-B");

    /* store-and-forward: overflow accounting and draining */
    static forge_sf_t sf; forge_sf_init(&sf, 3);
    int stored = 0;
    for (unsigned i = 0; i < FORGE_SF_CAPACITY + 5; i++) { recs[0].t_created = 1790000000u + i; stored += forge_sf_store(&sf, &recs[0]); }
    CHECK(stored == (int)FORGE_SF_CAPACITY && sf.dropped == 5, "buffer full: excess messages counted as dropped");

    /* drain everything; optionally write link blocks for the Python cross-check */
    FILE *f = argc > 1 ? fopen(argv[1], "wb") : NULL;
    uint32_t total = 0, sent = 0, blocks = 0; size_t n;
    while ((n = forge_sf_next_link_block(&sf, 1790009999u, link, sizeof link, &sent)) > 0) {
        total += sent; blocks++;
        if (f) fwrite(link, 1, n, f);
    }
    if (f) fclose(f);
    CHECK(total == FORGE_SF_CAPACITY && sf.count == 0, "drain sends every stored record once");
    CHECK(blocks == sf.seq && blocks > 1, "one sequence number per link block");

    /* acks: decode the Python-made ACK frame, then drop acked records from a fresh store */
    forge_ack_key_t keys[8]; uint16_t gw = 0;
    int nk = forge_ack_decode(VEC_ACK, sizeof VEC_ACK, keys, 8, &gw);
    CHECK(nk == 2 && gw == 4 && keys[0].short_id == VEC_RECS[0].sid && keys[1].t_created == VEC_RECS[2].t, "ACK frame from Python decodes");
    static uint8_t bad[sizeof VEC_ACK]; memcpy(bad, VEC_ACK, sizeof bad); bad[20] ^= 1;
    CHECK(forge_ack_decode(bad, sizeof bad, keys, 8, &gw) == -1, "corrupted ACK rejected");
    forge_record_t r3[VEC_NREC]; for (int i = 0; i < VEC_NREC; i++) load(&r3[i], i);
    forge_sf_init(&sf, 3);
    for (int i = 0; i < VEC_NREC; i++) forge_sf_store(&sf, &r3[i]);
    forge_ack_decode(VEC_ACK, sizeof VEC_ACK, keys, 8, &gw);
    CHECK(forge_sf_apply_acks(&sf, keys, 2) == 2 && sf.count == 1 && sf.rec[sf.head].short_id == VEC_RECS[1].sid,
          "acked records dropped on board, others kept in order");

    /* integrity: a bit flip in stored memory is caught and the record is never sent */
    forge_sf_init(&sf, 3);
    for (int i = 0; i < VEC_NREC; i++) forge_sf_store(&sf, &r3[i]);
    sf.rec[(sf.head + 1) % FORGE_SF_CAPACITY].payload[2] ^= 0x10;        /* simulated single-event upset */
    CHECK(forge_sf_scrub(&sf) == 1 && sf.count == 2 && sf.corrupted == 1, "corrupted record detected and discarded");

    /* persistence: save, wipe, load -> identical downlink */
    static uint8_t img[FORGE_SF_CAPACITY * (FORGE_REC_HDR + FORGE_PAYLOAD_MAX) + 64];
    forge_sf_init(&sf, 9); sf.seq = 41;
    for (int i = 0; i < VEC_NREC; i++) forge_sf_store(&sf, &r3[i]);
    size_t ilen = forge_sf_save(&sf, img, sizeof img);
    static forge_sf_t restored;
    CHECK(ilen > 0 && forge_sf_load(&restored, img, ilen) == 1 && restored.count == VEC_NREC && restored.seq == 41 && restored.sat_id == 9,
          "store survives save/load (reboot)");
    static uint8_t a[FORGE_LINK_MAX], b[FORGE_LINK_MAX]; uint32_t sa, sb;
    size_t la = forge_sf_next_link_block(&sf, 1u, a, sizeof a, &sa), lb = forge_sf_next_link_block(&restored, 1u, b, sizeof b, &sb);
    CHECK(la == lb && memcmp(a, b, la) == 0, "restored store downlinks byte-identical blocks");
    img[30] ^= 1;
    CHECK(forge_sf_load(&restored, img, ilen) == 0, "corrupted save image rejected");

    printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails);
    return fails ? 1 : 0;
}
