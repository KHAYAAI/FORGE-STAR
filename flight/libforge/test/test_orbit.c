#include <math.h>
#include <stdio.h>
#include "forge_orbit.h"
#include "orbit_vectors.h"
static int fails = 0;
#define CHECK(c, m) do { if (!(c)) { printf("FAIL: %s\n", m); fails++; } else printf("ok   %s\n", m); } while (0)
int main(void) {
    const double D = M_PI / 180.0;
    forge_elements_t el = {0.0, 550.0, 45.0 * D, 0.0, 0.0, 0.0};
    double worst = 0, worst_el = 0;
    for (int i = 0; i < OV_N; i++) {
        double p[3]; forge_orbit_ecef(&el, OV_T[i], p);
        double d = sqrt(pow(p[0] - OV_POS[i][0], 2) + pow(p[1] - OV_POS[i][1], 2) + pow(p[2] - OV_POS[i][2], 2));
        if (d > worst) worst = d;
        double e = forge_orbit_elevation(&el, OV_T[i], -25.89 * D, 27.69 * D) / D;
        if (fabs(e - OV_EL_DEG[i]) > worst_el) worst_el = fabs(e - OV_EL_DEG[i]);
    }
    printf("     max position difference vs Python: %.3g km, elevation %.3g deg\n", worst, worst_el);
    CHECK(worst < 1e-6 && worst_el < 1e-6, "C propagator matches forgestar/orbits.py over 3 days");
    forge_gateway_t gw = {-25.89 * D, 27.69 * D, 10.0 * D};
    double nxt = forge_orbit_next_pass(&el, 0.0, &gw, 1, 10.0, 2 * 86400.0);
    CHECK(nxt > 0 && nxt < 2 * 86400.0, "next gateway pass found within 2 days");
    CHECK(forge_orbit_gateway_in_view(&el, nxt + 30.0, &gw, 1) == 1, "gateway in view just after predicted pass start");
    printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails);
    return fails != 0;
}
