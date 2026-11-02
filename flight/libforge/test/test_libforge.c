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

    printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails);
    return fails ? 1 : 0;
}
