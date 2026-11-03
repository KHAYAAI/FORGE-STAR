/* Onboard pass prediction: circular orbit + J2 secular drift + Earth rotation.
 * Same model as forgestar/orbits.py (checked against SGP4). Elements are uplinked by operators. */
#ifndef FORGE_ORBIT_H
#define FORGE_ORBIT_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    double epoch;     /* unix seconds at which the elements hold */
    double alt_km;    /* circular altitude */
    double inc_rad, raan_rad, u_rad;   /* inclination, RAAN, argument of latitude at epoch */
    double gmst_rad;  /* Earth rotation angle at epoch */
} forge_elements_t;

typedef struct { double lat_rad, lon_rad, mask_rad; } forge_gateway_t;

/* Earth-fixed position (km) at unix time t */
void forge_orbit_ecef(const forge_elements_t *el, double t, double out[3]);
/* Elevation (rad) of the satellite from a ground site */
double forge_orbit_elevation(const forge_elements_t *el, double t, double lat_rad, double lon_rad);
/* 1 if any gateway sees the satellite above its mask at time t */
int forge_orbit_gateway_in_view(const forge_elements_t *el, double t, const forge_gateway_t *gws, int n);
/* Seconds from t until the next gateway pass starts (searching up to horizon_s in step_s steps); -1 if none */
double forge_orbit_next_pass(const forge_elements_t *el, double t, const forge_gateway_t *gws, int n,
                             double step_s, double horizon_s);

#ifdef __cplusplus
}
#endif
#endif
