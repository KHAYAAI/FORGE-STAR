#include <stdio.h>
#include <string.h>
#include "forge_device.h"
#include "vectors.h"
/* vectors.h also carries frame vectors this test does not use */
static const void *unused_vec[] = {VEC_FRAME, VEC_LINK};
static int fails = 0;
#define CHECK(c, m) do { if (!(c)) { printf("FAIL: %s\n", m); fails++; } else printf("ok   %s\n", m); } while (0)
static forge_sf_t sat;
static int modem(void *user, const uint8_t *pkt, size_t len) {      /* stand-in for modem + satellite driver */
    forge_record_t r; (void)user;
    if (!forge_dev_decode_uplink(pkt, len, &r)) return 1;
    forge_sf_store(&sat, &r); return 0;
}
int main(void) {
    (void)unused_vec;
    forge_dev_t d; forge_dev_init(&d, VEC_NAMES[0], 48 * 3600, 600);   /* "pump-0000" */
    const char *p = "{\"flow\":1}";
    forge_dev_send(&d, VEC_RECS[0].t, -2412345, 2954321, (const uint8_t *)p, (uint16_t)strlen(p));   /* = acked key in VEC_ACK */
    forge_dev_send(&d, VEC_RECS[0].t + 60, -2412345, 2954321, (const uint8_t *)p, (uint16_t)strlen(p));
    forge_sf_init(&sat, 1);
    CHECK(forge_dev_on_pass(&d, VEC_RECS[0].t + 100, modem, NULL) == 2 && sat.count == 2, "pass: both readings reach the satellite");
    CHECK(forge_dev_on_pass(&d, VEC_RECS[0].t + 200, modem, NULL) == 0, "no re-send before min_resend_s");
    CHECK(forge_dev_on_pass(&d, VEC_RECS[0].t + 900, modem, NULL) == 2, "unacked readings re-sent on a later pass");
    CHECK(forge_dev_on_ack(&d, VEC_ACK, sizeof VEC_ACK) == 1 && d.count == 1, "ACK from the gateway (Python-made frame) clears the acked reading");
    CHECK(forge_dev_on_pass(&d, VEC_RECS[0].t + 49 * 3600, modem, NULL) == 0 && d.expired == 1 && d.count == 0, "readings older than max age expire");
    for (unsigned i = 0; i < FORGE_DEV_QUEUE + 3; i++) forge_dev_send(&d, i, 0, 0, (const uint8_t *)"x", 1);
    CHECK(d.count == FORGE_DEV_QUEUE && d.overflow == 3 && d.q[0].t_created == 3, "full queue drops the oldest reading");
    uint8_t pkt[64]; size_t n = forge_dev_encode_uplink(&d.q[0], pkt, sizeof pkt); pkt[5] ^= 1;
    forge_record_t r; CHECK(forge_dev_decode_uplink(pkt, n, &r) == 0, "corrupted uplink packet rejected");
    printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails);
    return fails != 0;
}
