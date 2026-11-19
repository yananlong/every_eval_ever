# ECI handoff: W2 posterior

`W2/seed12345.nc` (210,605,531 bytes) is the W2 posterior. All W3 null and misfit replicates draw their true values from it. It is split into parts under 50 MB to fit GitHub's file limit.

Reassemble and verify it from the repository root:

```bash
cd eci-handoff/W2
sha256sum -c <(head -n -1 SHA256SUMS)            # check each part
cat seed12345.nc.part-* > seed12345.nc
sha256sum -c <(tail -n 1 SHA256SUMS)             # expect 88ab45bb...
```

Then copy it to `eci_work/v11/runs/W/W2/seed12345.nc`. See `docs/research/eci-prior-fit-checks/HANDOFF.md` on branch `research/consolidated-evidence-index`.
