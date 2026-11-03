#!/bin/sh
# Nightly logical backup of the FORGE STAR database, kept KEEP_DAYS days.
set -eu
while true; do
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  pg_dump -h timescaledb -U forge -d forgestar -Fc -f "/backups/forgestar-$ts.dump.tmp" \
    && mv "/backups/forgestar-$ts.dump.tmp" "/backups/forgestar-$ts.dump" \
    && echo "backup ok: forgestar-$ts.dump"
  find /backups -name 'forgestar-*.dump' -mtime "+${KEEP_DAYS:-14}" -delete
  sleep 86400
done
