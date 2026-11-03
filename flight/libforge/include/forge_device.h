/* FORGE STAR device SDK (C99, no malloc): what runs on a customer's field device.
 *
 *   forge_dev_init()            once, with the device name (its short id = crc32(name))
 *   forge_dev_send()            queue a reading
 *   forge_dev_on_pass()         when the NB-IoT NTN modem reports a satellite in view: transmits
 *                               every unacknowledged reading (re-send until acked)
 *   forge_dev_on_ack()          feed ACK frames the satellite relays: acked readings leave the queue
 *
 * Uplink packet (one reading) = record encoding of forgestar/frames.py + CRC-32:
 *   u32 short id | u32 t_created | i32 lat*1e5 | i32 lon*1e5 | u16 len | payload | u32 crc
 * The satellite's NB-IoT driver decodes it with forge_dev_decode_uplink() and stores it. */
#ifndef FORGE_DEVICE_H
#define FORGE_DEVICE_H
#include "forge.h"
#ifdef __cplusplus
extern "C" {
#endif

#ifndef FORGE_DEV_QUEUE
#define FORGE_DEV_QUEUE 64u
#endif

typedef struct {
    forge_record_t q[FORGE_DEV_QUEUE];
    uint32_t sent_at[FORGE_DEV_QUEUE];   /* last transmission time (0 = never) */
    uint32_t tries[FORGE_DEV_QUEUE];
    uint32_t count;
    uint32_t short_id;
    uint32_t max_age_s;                  /* give up on readings older than this */
    uint32_t min_resend_s;               /* do not re-send the same reading more often than this */
    uint32_t acked, expired, overflow, transmissions;
} forge_dev_t;

/* Called by forge_dev_on_pass for each packet to transmit; return 0 if the modem accepted it. */
typedef int (*forge_dev_tx_fn)(void *user, const uint8_t *pkt, size_t len);

void   forge_dev_init(forge_dev_t *d, const char *device_name, uint32_t max_age_s, uint32_t min_resend_s);
/* Queue a reading. When the queue is full the oldest reading is dropped (counted in overflow). */
int    forge_dev_send(forge_dev_t *d, uint32_t t_created, int32_t lat_e5, int32_t lon_e5, const uint8_t *payload, uint16_t len);
/* Satellite in view: (re)transmit pending readings. Returns packets handed to the modem. */
uint32_t forge_dev_on_pass(forge_dev_t *d, uint32_t now, forge_dev_tx_fn tx, void *user);
/* ACK frame relayed by the satellite. Returns readings removed from the queue. */
uint32_t forge_dev_on_ack(forge_dev_t *d, const uint8_t *ack_frame, size_t len);

size_t forge_dev_encode_uplink(const forge_record_t *r, uint8_t *out, size_t cap);
int    forge_dev_decode_uplink(const uint8_t *pkt, size_t len, forge_record_t *out);   /* 1 = valid */

#ifdef __cplusplus
}
#endif
#endif
