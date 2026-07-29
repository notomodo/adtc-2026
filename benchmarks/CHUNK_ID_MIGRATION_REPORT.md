# Chunk ID migration report

Old dump: `benchmarks/chunks_sme.txt` (47 chunks, positional integer ids)
New index: `benchmarks/migration_index` (47 chunks, stable string ids)

**Verification: PASSED.** Every mapped chunk's text is byte-identical between the old dump and the new chunks.jsonl.

## Per-document ranges

| document | old id range | new id range | n_chunks |
|---|---|---|---|
| General_Terms_for_Sellers_and_Buyers.pdf | [0, 21] | 1df1cd8d:0 .. 1df1cd8d:21 | 22 |
| Privacy_Policy.pdf | [22, 35] | 21d0ee2c:0 .. 21d0ee2c:13 | 14 |
| Return_Policy.pdf | [36, 38] | f232e5d3:0 .. f232e5d3:2 | 3 |
| Seek_Support.pdf | [39, 39] | a72cadc9:0 .. a72cadc9:0 | 1 |
| Sellers_Terms_and_Conditions.pdf | [40, 46] | 9a6d80d1:0 .. 9a6d80d1:6 | 7 |

## Sample mappings (first 5, last 5)

- `0` -> `1df1cd8d:0`
- `1` -> `1df1cd8d:1`
- `2` -> `1df1cd8d:2`
- `3` -> `1df1cd8d:3`
- `4` -> `1df1cd8d:4`
- `42` -> `9a6d80d1:2`
- `43` -> `9a6d80d1:3`
- `44` -> `9a6d80d1:4`
- `45` -> `9a6d80d1:5`
- `46` -> `9a6d80d1:6`

## What this changes if adopted

- Every `gold_chunks`/`retrieved` reference in the question sets (`data/questions/*.json`) and every benchmark result keyed by a positional id would need remapping through `chunk_id_migration_map.json`.
- `benchmarks/chunks_sme.txt`'s positional dump format and its corpus-fingerprint gate would be superseded by `benchmarks/migration_index/manifest.json` + `chunks.jsonl` (which carries its own per-document identity via doc_sha256, not a whole-corpus fingerprint).
- **Not done here.** Question sets are NOT rewritten by this script.
