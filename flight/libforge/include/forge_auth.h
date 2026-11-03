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

#ifdef __cplusplus
}
#endif
#endif
