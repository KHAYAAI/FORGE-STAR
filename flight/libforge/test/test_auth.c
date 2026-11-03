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
    printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails);
    return fails != 0;
}
