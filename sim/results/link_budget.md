# Link budget (illustrative, 550 km)

Margin in dB at each elevation. Generated from `forgestar/linkbudget.py`.

| Link | 5° | 10° | 20° | 30° | 45° | 60° | 90° | Closes (3 dB) from |
|---|---|---|---|---|---|---|---|---|
| NB-IoT NTN uplink (device→sat), S-band | -12.0 | -9.1 | -2.6 | +3.6 | +10.8 | +15.7 | +19.3 | 29° |
| NB-IoT NTN downlink (sat→device), S-band | -20.6 | -17.8 | -11.2 | -5.0 | +2.2 | +7.1 | +10.7 | 47° |
| AIS receive (ship→sat), VHF | +8.8 | +10.6 | +14.0 | +16.7 | +19.6 | +21.5 | +22.9 | 0° |
| Feeder downlink (sat→gateway), X-band | +1.1 | +3.2 | +7.3 | +10.8 | +14.9 | +17.5 | +19.4 | 10° |
