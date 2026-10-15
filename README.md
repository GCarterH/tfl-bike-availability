# TfL bike availability

Typical Santander Cycles availability across London, learned from TfL's live BikePoint feed.

The file `profiles.json` on the [`data`](../../tree/data) branch is updated every 5 minutes:

    https://raw.githubusercontent.com/GeorgeCC-hardware/tfl-bike-availability/data/profiles.json

For every docking station it holds the average bikes, e-bikes and free docks for each 15-minute
slot of the week (London time). Rows are
`[dow, slot, samples, bikes×10, ebikes×10, docks×10, empty %, full %]`, with `dow` 0 = Sunday.

`scripts/update.py` adds one sample. It runs on a home server; the GitHub Actions workflow is a
manual fallback.

Powered by TfL Open Data. Contains OS data © Crown copyright and database rights.
