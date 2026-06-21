# GeoIP database (offline, optional)

Abilithic Recon enriches IPs with country/city/ASN **fully offline**. The
database file is not committed (it can be large / licensed). The app still works
without it - geolocation columns are simply left empty.

## Recommended: DB-IP Lite (free, CC-BY, no account)

1. Download the free MMDB files from https://db-ip.com/db/download/ip-to-city-lite
   and https://db-ip.com/db/download/ip-to-asn-lite
2. Rename and place them here:
   - `dbip-city-lite.mmdb`
   - `dbip-asn-lite.mmdb`

## Alternative: MaxMind GeoLite2 (free, requires a MaxMind account)

Place `GeoLite2-City.mmdb` and/or `GeoLite2-ASN.mmdb` in this folder.

The build (PyInstaller spec) bundles whatever `.mmdb` files are present here.

> Attribution: if you ship DB-IP Lite, include the DB-IP attribution per its
> CC-BY license. For GeoLite2, follow MaxMind's license terms.
