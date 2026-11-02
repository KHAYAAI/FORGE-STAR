# Link budget (illustrative, 550 km)

Margin in dB at each elevation. Generated from `forgestar/linkbudget.py`.

| Link | 5° | 10° | 20° | 30° | 45° | 60° | 90° | Closes (3 dB) from |
|---|---|---|---|---|---|---|---|---|
| NB-IoT NTN uplink (device→sat), S-band | -7.7 | -4.8 | +1.7 | +7.9 | +15.1 | +20.0 | +23.6 | 22° |
| NB-IoT NTN downlink (sat→device), S-band | -16.3 | -13.5 | -6.9 | -0.7 | +6.5 | +11.4 | +15.0 | 37° |
| AIS receive (ship→sat), VHF | +8.8 | +10.6 | +14.0 | +16.7 | +19.6 | +21.5 | +22.9 | 0° |
| Feeder downlink (sat→gateway), X-band | +3.4 | +5.3 | +9.0 | +12.1 | +15.5 | +17.8 | +19.4 | 4° |
