/* Command authentication for the FORGE STAR payload: HMAC-SHA256 with a monotonic counter.
 * Signed command = <F´ command packet> <u32 counter, big-endian> <32-byte HMAC-SHA256(key, packet || counter)>.
 * The satellite accepts a command only if the HMAC matches and counter > last accepted counter. */
#ifndef FORGE_AUTH_H
#define FORGE_AUTH_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

#define FORGE_AUTH_TAG 32u
#define FORGE_AUTH_TRAILER (4u + FORGE_AUTH_TAG)

void forge_sha256(const uint8_t *data, size_t len, uint8_t out[32]);
void forge_hmac_sha256(const uint8_t *key, size_t key_len, const uint8_t *msg, size_t len, uint8_t out[32]);

typedef enum { FORGE_AUTH_OK = 0, FORGE_AUTH_SHORT = 1, FORGE_AUTH_BAD_TAG = 2, FORGE_AUTH_REPLAY = 3 } forge_auth_result_t;

/* Verify a signed command. On success *payload_len = length without the trailer and *last_counter is advanced. */
forge_auth_result_t forge_auth_verify(const uint8_t *key, size_t key_len, const uint8_t *signed_cmd, size_t len,
                                      uint32_t *last_counter, size_t *payload_len);

/* ---- confidentiality: ChaCha20 (RFC 8439), encrypt-then-MAC ----
 * Encrypted command = packet[0..4) in clear (F´ packet type, the deframer routes on it)
 *                     || ChaCha20(k_enc, nonce = 8 zero bytes || u32 counter, block 1)(packet[4..))
 *                     || u32 counter || HMAC-SHA256(k_mac, ciphertext || counter)
 * k_enc = HMAC(master, "forge-enc"), k_mac = HMAC(master, "forge-mac"). */
void forge_chacha20_xor(const uint8_t key[32], const uint8_t nonce[12], uint32_t block, uint8_t *buf, size_t len);
void forge_auth_derive(const uint8_t *master, size_t len, uint8_t k_enc[32], uint8_t k_mac[32]);
/* Verify + decrypt in place. On success the plaintext packet is at cmd[0..*payload_len). */
forge_auth_result_t forge_auth_open(const uint8_t k_enc[32], const uint8_t k_mac[32], uint8_t *cmd, size_t len,
                                    uint32_t *last_counter, size_t *payload_len);

#ifdef __cplusplus
}
#endif
#endif
