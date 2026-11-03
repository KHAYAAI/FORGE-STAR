/* SHA-256 (FIPS 180-4), HMAC (RFC 2104) and command verification. Small, portable, no malloc. */
#include "forge_auth.h"
#include <string.h>

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

#define ROR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

typedef struct { uint32_t h[8]; uint8_t buf[64]; size_t n; uint64_t bits; } sha_t;

static void sha_block(sha_t *s, const uint8_t *p) {
    uint32_t w[64], a, b, c, d, e, f, g, h;
    for (int i = 0; i < 16; i++) w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 | (uint32_t)p[4 * i + 2] << 8 | p[4 * i + 3];
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = ROR(w[i - 15], 7) ^ ROR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = ROR(w[i - 2], 17) ^ ROR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    a = s->h[0]; b = s->h[1]; c = s->h[2]; d = s->h[3]; e = s->h[4]; f = s->h[5]; g = s->h[6]; h = s->h[7];
    for (int i = 0; i < 64; i++) {
        uint32_t t1 = h + (ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i];
        uint32_t t2 = (ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
        h = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
    }
    s->h[0] += a; s->h[1] += b; s->h[2] += c; s->h[3] += d; s->h[4] += e; s->h[5] += f; s->h[6] += g; s->h[7] += h;
}

static void sha_init(sha_t *s) {
    static const uint32_t iv[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    memcpy(s->h, iv, sizeof iv); s->n = 0; s->bits = 0;
}

static void sha_update(sha_t *s, const uint8_t *p, size_t len) {
    s->bits += (uint64_t)len * 8u;
    while (len) {
        size_t take = 64 - s->n < len ? 64 - s->n : len;
        memcpy(s->buf + s->n, p, take); s->n += take; p += take; len -= take;
        if (s->n == 64) { sha_block(s, s->buf); s->n = 0; }
    }
}

static void sha_final(sha_t *s, uint8_t out[32]) {
    uint64_t bits = s->bits;
    uint8_t pad = 0x80, z = 0, len[8];
    sha_update(s, &pad, 1);
    while (s->n != 56) sha_update(s, &z, 1);
    for (int i = 0; i < 8; i++) len[i] = (uint8_t)(bits >> (56 - 8 * i));
    sha_update(s, len, 8);
    for (int i = 0; i < 8; i++) { out[4 * i] = (uint8_t)(s->h[i] >> 24); out[4 * i + 1] = (uint8_t)(s->h[i] >> 16); out[4 * i + 2] = (uint8_t)(s->h[i] >> 8); out[4 * i + 3] = (uint8_t)s->h[i]; }
}

void forge_sha256(const uint8_t *data, size_t len, uint8_t out[32]) {
    sha_t s; sha_init(&s); sha_update(&s, data, len); sha_final(&s, out);
}

void forge_hmac_sha256(const uint8_t *key, size_t key_len, const uint8_t *msg, size_t len, uint8_t out[32]) {
    uint8_t k[64] = {0}, ipad[64], opad[64], inner[32];
    if (key_len > 64) forge_sha256(key, key_len, k); else memcpy(k, key, key_len);
    for (int i = 0; i < 64; i++) { ipad[i] = (uint8_t)(k[i] ^ 0x36); opad[i] = (uint8_t)(k[i] ^ 0x5c); }
    sha_t s;
    sha_init(&s); sha_update(&s, ipad, 64); sha_update(&s, msg, len); sha_final(&s, inner);
    sha_init(&s); sha_update(&s, opad, 64); sha_update(&s, inner, 32); sha_final(&s, out);
}

forge_auth_result_t forge_auth_verify(const uint8_t *key, size_t key_len, const uint8_t *cmd, size_t len,
                                      uint32_t *last_counter, size_t *payload_len) {
    if (len < FORGE_AUTH_TRAILER + 8u) return FORGE_AUTH_SHORT;
    size_t signed_len = len - FORGE_AUTH_TAG;                       /* packet || counter */
    uint8_t tag[32];
    forge_hmac_sha256(key, key_len, cmd, signed_len, tag);
    uint8_t diff = 0;                                               /* constant-time compare */
    for (unsigned i = 0; i < FORGE_AUTH_TAG; i++) diff |= (uint8_t)(tag[i] ^ cmd[signed_len + i]);
    if (diff) return FORGE_AUTH_BAD_TAG;
    const uint8_t *c = cmd + signed_len - 4;
    uint32_t counter = (uint32_t)c[0] << 24 | (uint32_t)c[1] << 16 | (uint32_t)c[2] << 8 | c[3];
    if (counter <= *last_counter) return FORGE_AUTH_REPLAY;
    *last_counter = counter;
    *payload_len = len - FORGE_AUTH_TRAILER;
    return FORGE_AUTH_OK;
}

/* ---------------- ChaCha20 (RFC 8439) ---------------- */
#define ROTL(x, n) (((x) << (n)) | ((x) >> (32 - (n))))
#define QR(a, b, c, d) a += b; d ^= a; d = ROTL(d, 16); c += d; b ^= c; b = ROTL(b, 12); \
                       a += b; d ^= a; d = ROTL(d, 8);  c += d; b ^= c; b = ROTL(b, 7);
static uint32_t le32(const uint8_t *p) { return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24; }

static void chacha_block(const uint32_t in[16], uint8_t out[64]) {
    uint32_t x[16];
    memcpy(x, in, sizeof x);
    for (int i = 0; i < 10; i++) {
        QR(x[0], x[4], x[8], x[12]) QR(x[1], x[5], x[9], x[13]) QR(x[2], x[6], x[10], x[14]) QR(x[3], x[7], x[11], x[15])
        QR(x[0], x[5], x[10], x[15]) QR(x[1], x[6], x[11], x[12]) QR(x[2], x[7], x[8], x[13]) QR(x[3], x[4], x[9], x[14])
    }
    for (int i = 0; i < 16; i++) {
        uint32_t v = x[i] + in[i];
        out[4 * i] = (uint8_t)v; out[4 * i + 1] = (uint8_t)(v >> 8); out[4 * i + 2] = (uint8_t)(v >> 16); out[4 * i + 3] = (uint8_t)(v >> 24);
    }
}

void forge_chacha20_xor(const uint8_t key[32], const uint8_t nonce[12], uint32_t block, uint8_t *buf, size_t len) {
    uint32_t st[16] = {0x61707865, 0x3320646e, 0x79622d32, 0x6b206574};
    for (int i = 0; i < 8; i++) st[4 + i] = le32(key + 4 * i);
    st[12] = block; st[13] = le32(nonce); st[14] = le32(nonce + 4); st[15] = le32(nonce + 8);
    uint8_t ks[64];
    for (size_t off = 0; off < len; off += 64) {
        chacha_block(st, ks); st[12]++;
        for (size_t i = 0; i < 64 && off + i < len; i++) buf[off + i] ^= ks[i];
    }
}

void forge_auth_derive(const uint8_t *master, size_t len, uint8_t k_enc[32], uint8_t k_mac[32]) {
    forge_hmac_sha256(master, len, (const uint8_t *)"forge-enc", 9, k_enc);
    forge_hmac_sha256(master, len, (const uint8_t *)"forge-mac", 9, k_mac);
}

forge_auth_result_t forge_auth_open(const uint8_t k_enc[32], const uint8_t k_mac[32], uint8_t *cmd, size_t len,
                                    uint32_t *last_counter, size_t *payload_len) {
    uint32_t last = *last_counter;
    forge_auth_result_t r = forge_auth_verify(k_mac, 32, cmd, len, &last, payload_len);  /* MAC over ciphertext first */
    if (r != FORGE_AUTH_OK) return r;
    const uint8_t *c = cmd + *payload_len;
    uint8_t nonce[12] = {0, 0, 0, 0, 0, 0, 0, 0, c[0], c[1], c[2], c[3]};
    if (*payload_len < 4) return FORGE_AUTH_SHORT;
    forge_chacha20_xor(k_enc, nonce, 1, cmd + 4, *payload_len - 4);   /* packet type (4 bytes) is sent in clear */
    *last_counter = last;
    return FORGE_AUTH_OK;
}
