#include <stdio.h>
#include <string.h>
#include "forge_auth.h"
static int fails = 0;
#define CHECK(c, m) do { if (!(c)) { printf("FAIL: %s\n", m); fails++; } else printf("ok   %s\n", m); } while (0)
static void hex(const uint8_t *b, char *o) { for (int i = 0; i < 32; i++) sprintf(o + 2 * i, "%02x", b[i]); }
int main(void) {
    uint8_t out[32]; char h[65];
    forge_sha256((const uint8_t *)"abc", 3, out); hex(out, h);
    CHECK(strcmp(h, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") == 0, "SHA-256(abc) = FIPS 180-4 vector");
    forge_hmac_sha256((const uint8_t *)"Jefe", 4, (const uint8_t *)"what do ya want for nothing?", 28, out); hex(out, h);
    CHECK(strcmp(h, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843") == 0, "HMAC-SHA256 = RFC 4231 test case 2");
    /* sign + verify, replay, tamper */
    const uint8_t key[16] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
    uint8_t cmd[8 + 4 + 32] = {0, 0, 0, 0, 0, 0, 0x05, 0x00, 0, 0, 0, 7};
    forge_hmac_sha256(key, 16, cmd, 12, cmd + 12);
    uint32_t last = 0; size_t plen = 0;
    CHECK(forge_auth_verify(key, 16, cmd, sizeof cmd, &last, &plen) == FORGE_AUTH_OK && plen == 8 && last == 7, "valid command accepted");
    CHECK(forge_auth_verify(key, 16, cmd, sizeof cmd, &last, &plen) == FORGE_AUTH_REPLAY, "replayed command rejected");
    cmd[7] ^= 1; last = 0;
    CHECK(forge_auth_verify(key, 16, cmd, sizeof cmd, &last, &plen) == FORGE_AUTH_BAD_TAG, "tampered command rejected");
    /* ChaCha20: RFC 8439 section 2.4.2 test vector */
    uint8_t k[32], nonce[12] = {0, 0, 0, 0, 0, 0, 0, 0x4a, 0, 0, 0, 0};
    for (int i = 0; i < 32; i++) k[i] = (uint8_t)i;
    char pt[] = "Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, sunscreen would be it.";
    forge_chacha20_xor(k, nonce, 1, (uint8_t *)pt, sizeof pt - 1);
    static const uint8_t ct16[16] = {0x6e, 0x2e, 0x35, 0x9a, 0x25, 0x68, 0xf9, 0x80, 0x41, 0xba, 0x07, 0x28, 0xdd, 0x0d, 0x69, 0x81};
    CHECK(memcmp(pt, ct16, 16) == 0, "ChaCha20 = RFC 8439 test vector");
    printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails);
    return fails != 0;
}
