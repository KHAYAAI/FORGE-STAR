#include "forge_orbit.h"
#include <math.h>

#define RE 6378.137
#define MU 398600.4418
#define J2 1.08262668e-3
#define OMEGA_E 7.2921159e-5

void forge_orbit_ecef(const forge_elements_t *el, double t, double out[3]) {
    const double a = RE + el->alt_km, n = sqrt(MU / (a * a * a));
    const double k = 1.5 * J2 * (RE / a) * (RE / a) * n;
    const double ci = cos(el->inc_rad), si = sin(el->inc_rad);
    const double dt = t - el->epoch;
    const double raan = el->raan_rad - k * ci * dt;
    const double u = el->u_rad + (n + k * (4.0 * ci * ci - 1.0)) * dt;
    const double x = a * (cos(raan) * cos(u) - sin(raan) * sin(u) * ci);
    const double y = a * (sin(raan) * cos(u) + cos(raan) * sin(u) * ci);
    const double z = a * sin(u) * si;
    const double th = el->gmst_rad + OMEGA_E * dt;
    out[0] = cos(th) * x + sin(th) * y;
    out[1] = -sin(th) * x + cos(th) * y;
    out[2] = z;
}

double forge_orbit_elevation(const forge_elements_t *el, double t, double lat, double lon) {
    double s[3];
    forge_orbit_ecef(el, t, s);
    const double up[3] = {cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat)};
    const double d[3] = {s[0] - RE * up[0], s[1] - RE * up[1], s[2] - RE * up[2]};
    const double r = sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
    return asin((d[0] * up[0] + d[1] * up[1] + d[2] * up[2]) / r);
}

int forge_orbit_gateway_in_view(const forge_elements_t *el, double t, const forge_gateway_t *g, int n) {
    for (int i = 0; i < n; i++)
        if (forge_orbit_elevation(el, t, g[i].lat_rad, g[i].lon_rad) >= g[i].mask_rad) return 1;
    return 0;
}

double forge_orbit_next_pass(const forge_elements_t *el, double t, const forge_gateway_t *g, int n,
                             double step, double horizon) {
    int prev = forge_orbit_gateway_in_view(el, t, g, n);
    for (double dt = step; dt <= horizon; dt += step) {
        const int now = forge_orbit_gateway_in_view(el, t + dt, g, n);
        if (now && !prev) return dt;
        prev = now;
    }
    return -1.0;
}
