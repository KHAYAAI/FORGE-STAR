# SGP4 cross-check of forgestar.orbits

Same initial mean elements, 550 km, 3 days. Position difference vs SGP4 (J2–J4; drag when B* > 0).

| Inclination | Drag (B*) | Plane (cross-track) max | Phasing (along-track) max | Equivalent altitude offset | Verdict |
|---|---|---|---|---|---|
| 45.0° | 0 | 2.8 km | 90 s | -1.6 km | plane matches: coverage stats valid |
| 97.6° | 0 | 1.0 km | 168 s | +3.0 km | plane matches: coverage stats valid |
| 50.0° | 0 | 2.5 km | 44 s | -0.8 km | plane matches: coverage stats valid |
| 45.0° | 0.0001 | 2.8 km | 90 s | -1.6 km | plane matches: coverage stats valid |

Phasing drift is the two models defining "550 km" differently (Keplerian vs SGP4 Kozai mean motion), equivalent to the altitude offset shown. It moves pass times, not coverage geometry.
Drag changes phasing over weeks, which is why fleet operations use SGP4/Orekit with fresh TLEs. Coverage statistics depend on geometry, not exact phasing, so they are unaffected.
