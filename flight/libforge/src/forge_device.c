#include "forge_device.h"
#include <string.h>

static void p16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)(v >> 8); p[1] = (uint8_t)v; }
static void p32(uint8_t *p, uint32_t v) { p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16); p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v; }
static uint32_t g32(const uint8_t *p) { return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3]; }

void forge_dev_init(forge_dev_t *d, const char *name, uint32_t max_age_s, uint32_t min_resend_s) {
    memset(d, 0, sizeof *d);
    d->short_id = forge_short_id(name);
    d->max_age_s = max_age_s;
    d->min_resend_s = min_resend_s;
}

static void remove_at(forge_dev_t *d, uint32_t i) {
    for (uint32_t j = i + 1; j < d->count; j++) { d->q[j - 1] = d->q[j]; d->sent_at[j - 1] = d->sent_at[j]; d->tries[j - 1] = d->tries[j]; }
    d->count--;
}

int forge_dev_send(forge_dev_t *d, uint32_t t, int32_t lat, int32_t lon, const uint8_t *payload, uint16_t len) {
    if (len > FORGE_PAYLOAD_MAX) return 0;
    if (d->count == FORGE_DEV_QUEUE) { remove_at(d, 0); d->overflow++; }
    forge_record_t *r = &d->q[d->count];
    memset(r, 0, sizeof *r);
    r->short_id = d->short_id; r->t_created = t; r->lat_e5 = lat; r->lon_e5 = lon; r->payload_len = len;
    memcpy(r->payload, payload, len);
    d->sent_at[d->count] = 0; d->tries[d->count] = 0;
    d->count++;
    return 1;
}

size_t forge_dev_encode_uplink(const forge_record_t *r, uint8_t *out, size_t cap) {
    size_t n = FORGE_REC_HDR + r->payload_len + 4u;
    if (cap < n || r->payload_len > FORGE_PAYLOAD_MAX) return 0;
    p32(out, r->short_id); p32(out + 4, r->t_created); p32(out + 8, (uint32_t)r->lat_e5); p32(out + 12, (uint32_t)r->lon_e5);
    p16(out + 16, r->payload_len); memcpy(out + 18, r->payload, r->payload_len);
    p32(out + 18 + r->payload_len, forge_crc32(out, 18u + r->payload_len));
    return n;
}

int forge_dev_decode_uplink(const uint8_t *pkt, size_t len, forge_record_t *out) {
    if (len < FORGE_REC_HDR + 4u) return 0;
    uint16_t pl = (uint16_t)((pkt[16] << 8) | pkt[17]);
    if (pl > FORGE_PAYLOAD_MAX || len != FORGE_REC_HDR + pl + 4u) return 0;
    if (forge_crc32(pkt, len - 4) != g32(pkt + len - 4)) return 0;
    memset(out, 0, sizeof *out);
    out->short_id = g32(pkt); out->t_created = g32(pkt + 4); out->lat_e5 = (int32_t)g32(pkt + 8); out->lon_e5 = (int32_t)g32(pkt + 12);
    out->payload_len = pl; memcpy(out->payload, pkt + 18, pl);
    return 1;
}

uint32_t forge_dev_on_pass(forge_dev_t *d, uint32_t now, forge_dev_tx_fn tx, void *user) {
    uint8_t pkt[FORGE_REC_HDR + FORGE_PAYLOAD_MAX + 4];
    uint32_t sent = 0;
    for (uint32_t i = 0; i < d->count;) {
        if (d->max_age_s && now > d->q[i].t_created + d->max_age_s) { remove_at(d, i); d->expired++; continue; }
        if (d->sent_at[i] == 0 || now >= d->sent_at[i] + d->min_resend_s) {
            size_t n = forge_dev_encode_uplink(&d->q[i], pkt, sizeof pkt);
            if (n && tx(user, pkt, n) == 0) { d->sent_at[i] = now; d->tries[i]++; d->transmissions++; sent++; }
        }
        i++;
    }
    return sent;
}

uint32_t forge_dev_on_ack(forge_dev_t *d, const uint8_t *f, size_t len) {
    forge_ack_key_t keys[128]; uint16_t gw;
    int n = forge_ack_decode(f, len, keys, 128, &gw);
    if (n <= 0) return 0;
    uint32_t removed = 0;
    for (uint32_t i = 0; i < d->count;) {
        int hit = 0;
        for (int k = 0; k < n && !hit; k++) hit = keys[k].short_id == d->q[i].short_id && keys[k].t_created == d->q[i].t_created;
        if (hit) { remove_at(d, i); removed++; } else i++;
    }
    d->acked += removed;
    return removed;
}
