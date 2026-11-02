/* libforge implementation. See include/forge.h. */
#include "forge.h"
#include <string.h>

/* ---------------- CRC-32 (IEEE, same as zlib.crc32) ---------------- */
uint32_t forge_crc32(const uint8_t *data, size_t len) {
    uint32_t c = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; i++) {
        c ^= data[i];
        for (int k = 0; k < 8; k++) c = (c >> 1) ^ (0xEDB88320u & (uint32_t)(-(int32_t)(c & 1u)));
    }
    return c ^ 0xFFFFFFFFu;
}

uint32_t forge_short_id(const char *name) { return forge_crc32((const uint8_t *)name, strlen(name)); }

static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)(v >> 8); p[1] = (uint8_t)v; }
static void put32(uint8_t *p, uint32_t v) { p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16); p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v; }

/* ---------------- frame v1 ---------------- */
size_t forge_frame_encode(uint8_t *out, size_t cap, uint16_t sat_id, uint32_t seq, uint32_t t_dl,
                          const forge_record_t *recs, size_t count, int more, size_t *used) {
    size_t limit = cap < FORGE_FRAME_MAX ? cap : FORGE_FRAME_MAX;
    size_t off = FORGE_FRAME_HDR, n = 0;
    if (limit < FORGE_FRAME_HDR + 4) return 0;
    while (n < count) {
        const forge_record_t *r = &recs[n];
        size_t need = FORGE_REC_HDR + r->payload_len;
        if (r->payload_len > FORGE_PAYLOAD_MAX) return 0;
        if (off + need + 4 > limit) break;
        put32(out + off, r->short_id); put32(out + off + 4, r->t_created);
        put32(out + off + 8, (uint32_t)r->lat_e5); put32(out + off + 12, (uint32_t)r->lon_e5);
        put16(out + off + 16, r->payload_len);
        memcpy(out + off + 18, r->payload, r->payload_len);
        off += need; n++;
    }
    if (n < count) more = 1;
    out[0] = FORGE_FRAME_MAGIC; out[1] = FORGE_FRAME_VERSION; put16(out + 2, sat_id); put32(out + 4, seq);
    put32(out + 8, t_dl); put16(out + 12, (uint16_t)n); put16(out + 14, more ? 1u : 0u);
    put32(out + off, forge_crc32(out, off));
    if (used) *used = n;
    return off + 4;
}

/* ---------------- GF(2^8), RS(255,223) CCSDS parameters ---------------- */
#define PRIM 0x187u
#define FCR  112u
#define GENB 11u
#define NSYM (FORGE_RS_N - FORGE_RS_K)
static uint8_t gf_exp[512], gf_log[256], gpoly[NSYM + 1];
static int gf_ready = 0;

static uint8_t gmul(uint8_t a, uint8_t b) { return (a && b) ? gf_exp[gf_log[a] + gf_log[b]] : 0; }

static void gf_init(void) {
    unsigned x = 1;
    for (int i = 0; i < 255; i++) { gf_exp[i] = (uint8_t)x; gf_log[x] = (uint8_t)i; x <<= 1; if (x & 0x100u) x ^= PRIM; }
    for (int i = 255; i < 512; i++) gf_exp[i] = gf_exp[i - 255];
    /* g(x) = prod (x + beta^j), j = FCR..FCR+31, beta = alpha^11; stored highest degree first */
    uint8_t g[NSYM + 1] = {1}; int deg = 0;
    for (unsigned j = FCR; j < FCR + NSYM; j++) {
        uint8_t root = gf_exp[(GENB * j) % 255u];
        g[deg + 1] = 0;
        for (int i = deg + 1; i > 0; i--) g[i] = (uint8_t)(g[i] ^ gmul(root, g[i - 1]));  /* lowest-first multiply */
        deg++;
    }
    /* g[] is highest degree first; g[0] = 1 (monic). Matches GPOLY in forgestar/fec.py. */
    for (unsigned i = 0; i <= NSYM; i++) gpoly[i] = g[i];
    gf_ready = 1;
}

void forge_rs_encode(const uint8_t data[FORGE_RS_K], uint8_t par[NSYM]) {
    if (!gf_ready) gf_init();
    memset(par, 0, NSYM);
    for (unsigned i = 0; i < FORGE_RS_K; i++) {
        uint8_t fb = (uint8_t)(data[i] ^ par[0]);
        memmove(par, par + 1, NSYM - 1); par[NSYM - 1] = 0;
        if (fb) for (unsigned k = 0; k < NSYM; k++) par[k] ^= gmul(fb, gpoly[k + 1]);
    }
}

/* CCSDS pseudo-randomiser: h(x)=x^8+x^7+x^5+x^3+1, all-ones seed; output r0, feedback r0^r3^r5^r7 */
void forge_randomise(uint8_t *buf, size_t len) {
    uint8_t r[8] = {1, 1, 1, 1, 1, 1, 1, 1};
    for (size_t i = 0; i < len; i++) {
        uint8_t b = 0;
        for (int k = 0; k < 8; k++) {
            b = (uint8_t)((b << 1) | r[0]);
            uint8_t fb = (uint8_t)(r[0] ^ r[3] ^ r[5] ^ r[7]);
            memmove(r, r + 1, 7); r[7] = fb;
        }
        buf[i] ^= b;
    }
}

size_t forge_link_encode(uint8_t *out, size_t cap, const uint8_t *frame, size_t flen) {
    size_t n_cw = (flen + 3 + FORGE_RS_K - 1) / FORGE_RS_K;
    size_t total = 4 + n_cw * FORGE_RS_N;
    if (n_cw > FORGE_LINK_MAX_CW || total > cap || flen > 0xFFFFu) return 0;
    static const uint8_t asm_marker[4] = {0x1A, 0xCF, 0xFC, 0x1D};
    memcpy(out, asm_marker, 4);
    uint8_t blk[FORGE_RS_K];
    size_t src = 0;
    for (size_t c = 0; c < n_cw; c++) {
        size_t o = 0;
        memset(blk, 0, sizeof blk);
        if (c == 0) { blk[0] = (uint8_t)(flen >> 8); blk[1] = (uint8_t)flen; blk[2] = (uint8_t)n_cw; o = 3; }
        size_t take = flen - src < FORGE_RS_K - o ? flen - src : FORGE_RS_K - o;
        memcpy(blk + o, frame + src, take); src += take;
        uint8_t *cw = out + 4 + c * FORGE_RS_N;
        memcpy(cw, blk, FORGE_RS_K);
        forge_rs_encode(blk, cw + FORGE_RS_K);
    }
    forge_randomise(out + 4, n_cw * FORGE_RS_N);
    return total;
}

/* ---------------- store-and-forward ring buffer ---------------- */
void forge_sf_init(forge_sf_t *sf, uint16_t sat_id) { memset(sf, 0, sizeof *sf); sf->sat_id = sat_id; }

int forge_sf_store(forge_sf_t *sf, const forge_record_t *r) {
    if (sf->count >= FORGE_SF_CAPACITY || r->payload_len > FORGE_PAYLOAD_MAX) { sf->dropped++; return 0; }
    sf->rec[(sf->head + sf->count) % FORGE_SF_CAPACITY] = *r;
    sf->count++;
    return 1;
}

size_t forge_sf_next_link_block(forge_sf_t *sf, uint32_t t_dl, uint8_t *out, size_t cap, uint32_t *sent) {
    static uint8_t frame[FORGE_FRAME_MAX];
    static forge_record_t batch[64];
    if (sent) *sent = 0;
    if (sf->count == 0) return 0;
    size_t n = sf->count < 64 ? sf->count : 64;
    for (size_t i = 0; i < n; i++) batch[i] = sf->rec[(sf->head + i) % FORGE_SF_CAPACITY];
    size_t used = 0;
    size_t flen = forge_frame_encode(frame, sizeof frame, sf->sat_id, sf->seq, t_dl, batch, n,
                                     sf->count > n, &used);
    if (flen == 0 || used == 0) return 0;
    /* a frame of up to 4096 bytes needs 19 codewords: fits FORGE_LINK_MAX */
    size_t llen = forge_link_encode(out, cap, frame, flen);
    if (llen == 0) return 0;
    sf->head = (sf->head + (uint32_t)used) % FORGE_SF_CAPACITY;
    sf->count -= (uint32_t)used;
    sf->seq++;
    if (sent) *sent = (uint32_t)used;
    return llen;
}
