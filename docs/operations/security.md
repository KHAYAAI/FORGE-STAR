# Security and data protection (draft)

## What is protected, and how

| Asset | Threat | Control built | Still to do |
|---|---|---|---|
| **Satellite commanding** | Someone else commands the payload | HMAC-SHA256 on every command, per-satellite key, monotonic counter (replay protection), checked on board before dispatch (`CmdAuth`) | Command encryption (confidentiality); key upload procedure with the bus partner; protected key storage on the payload computer |
| **Downlinked data** | Corruption on the radio link | RS(255,223) CCSDS, CRC-32 per frame and per stored record, memory scrubbing | Link encryption if customers require confidentiality over the air |
| **Customer data at rest** | Unauthorised access | Data hosted in SA; per-customer API keys (hashed); customers only see their own devices (other devices return 404) | Disk encryption on hosts; database role separation |
| **Customer API** | Abuse, scraping, brute force | Per-key rate limit, request size cap, security headers, audit log, key revocation, TLS (Caddy) | SSO for staff consoles; WAF if exposed widely |
| **Platform** | Service compromise, data loss | No database/Kafka ports on the host in production; required secrets; nightly backups with retention; log rotation | Off-site backup copy (within SA); restore drill; monitoring and alerting on `/metrics` |
| **ThingsBoard** | Default credentials | Behind TLS; provisioning script | **Change demo tenant/sysadmin passwords before any real use** |

## POPIA checklist (South Africa)

- [ ] Identify which device data is personal information (e.g. ranger messaging, vehicle tracking tied to drivers).
- [ ] Appoint and register an Information Officer.
- [ ] Customer contracts: FORGE STAR as operator (processor) for customers; processing purposes and retention periods.
- [ ] Retention: TimescaleDB retention policy per customer (default to be set; e.g. 24 months).
- [ ] Data stays in SA: database, backups and gateways relay into SA (partner gateways abroad forward only).
- [ ] Breach procedure: notify the Information Regulator and affected parties.
- [ ] Access review: who can query customer data, logged through `api_audit`.

*Draft. Confirm with counsel; ICASA and government customers may add security accreditation requirements.*
