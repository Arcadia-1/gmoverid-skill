# gm/ID Physical Validation Reference

This document describes the five-point self-test run by `validate_gmoverid.py`
to verify that a gm/ID characterization table is physically consistent with
semiconductor theory.  No EDA tool comparison or internet access is needed —
the tests rely entirely on fundamental physics valid at room temperature (~300 K).

Run the self-test from the project working directory:

    python validate_gmoverid.py [model] [L_um]
    python validate_gmoverid.py                    # default: nmos180 @ 180 nm
    python validate_gmoverid.py nmos45hp 0.045
    python validate_gmoverid.py pmos180  0.36

---

## Test 1 — Weak-Inversion Limit (the 1/Ut Test)

**What it checks:** the peak gm/ID value stored at the top of the lookup table.

**Physics:** In weak inversion (subthreshold) drain current follows an
exponential law, so gm/ID approaches its theoretical ceiling:

```
gm/ID_max = 1 / (n · Ut)
```

where `Ut = kT/q ≈ 25.85 mV` at 300 K and `n` is the slope factor (1.2–1.5
for modern bulk CMOS).  Substituting the extremes:

```
n = 1.2  →  gm/ID_max = 32.2 V^-1
n = 1.5  →  gm/ID_max = 25.8 V^-1
```

**Pass criterion:** `25.0 ≤ peak gm/ID ≤ 32.0 V^-1`

**Failure interpretation:**

| Symptom | Likely cause |
|---------|-------------|
| Peak > 32 | Vgs sweep extends into noise-dominated Id ≈ 0 region; gm finite-difference becomes unreliable; tighten `id_thresh` in `sweep_vgs` |
| Peak < 25 | Sweep does not reach weak inversion; lower the starting Vgs or relax `id_thresh` |
| Peak ≈ 50 | gm extracted at essentially zero Id; add a minimum-Id guard (`id_thresh > 0`) before computing gmid |

---

## Test 2 — ID/W Monotonicity

**What it checks:** the normalized current density Id/W decreases strictly
and monotonically as gm/ID increases from strong to weak inversion.

**Physics:** As Vgs is lowered from above-threshold toward subthreshold,
the transistor is progressively turned off.  Drain current falls
exponentially; Id/W therefore decreases monotonically.  No physical
mechanism inside the saturation region can cause Id/W to reverse and rise.
Any non-monotone step is a numerical artefact.

**Pass criterion:** zero non-monotone steps across the full lookup table.

**Failure interpretation:**

| Symptom | Likely cause |
|---------|-------------|
| 1–5 violations | Ngspice Vgs step too coarse near the gm/ID peak; increase NPTS in `sweep_vgs` |
| Many violations | Noise in raw wrdata or gm extraction near Id cutoff; check the `.lis` file |
| Violations only at low gmid | Strong-inversion noise from short-channel DIBL; acceptable if count < 3 |

---

## Test 3 — Channel-Length Doubling Scaling

**What it checks:** at gm/ID = 15 V^-1, doubling L produces the expected
changes in both intrinsic gain (gm·ro) and transit frequency (fT).

**Physics:**

*Intrinsic gain:* Channel-length modulation gives `gds ≈ λ·Id` with
`λ ∝ 1/L`, so `ro = 1/gds ∝ L`.  At fixed gm/ID and Id, gm is constant,
therefore:

```
gm·ro(2L) / gm·ro(L) ≈ 1.5 – 5×   (node-dependent; closer to 2× for long-channel)
```

Advanced nodes (< 45 nm) show weaker scaling because DIBL and velocity
saturation dominate; longer-channel devices approach the ideal ×2.

*Transit frequency:* Gate capacitance `Cgg ≈ (2/3)·Cox·W·L + Cov·W`,
so at constant W and gm:

```
fT(2L) / fT(L) ≈ 0.15 – 0.70×
```

The range is wide because overlap/fringing capacitance (independent of L)
softens the ideal 1/L dependence.

**Pass criteria:**

| Quantity | Acceptable ratio |
|----------|-----------------|
| `gmro(2L) / gmro(L)` | ≥ 1.5 (no upper cap — see note) |
| `fT(2L) / fT(L)` | 0.15 – 0.70 |

> **Note on the gain ratio upper cap:** for 180 nm bulk CMOS the ratio is
> typically 1.8–3×.  For HP minimum-L nodes (e.g. 45 nm, L = 45 nm → 90 nm),
> DIBL dominates at minimum L and collapses gmro to ~5–8; doubling L moves
> the device far from the DIBL-dominated regime, raising gmro by 8–15×.
> This large ratio is **physically correct and expected** — it is not a model
> error.  Removing the upper cap lets the test focus solely on whether the
> model responds to L at all (ratio must be > 1.5).

**Failure interpretation:**

| Symptom | Likely cause |
|---------|-------------|
| Gain ratio < 1.5 | Model ignores CLM (λ = 0 or first-order model) |
| fT ratio > 0.70 | Overlap capacitance dominates — acceptable for sub-45 nm |
| fT ratio < 0.15 | Cgg growing faster than expected; check tox or cgso/cgdo in MODEL_INFO |

---

## Test 4 — fT × gm/ID Peak in Mid-Inversion

**What it checks:** the position of the maximum of the product `fT · (gm/ID)`.

**Physics:** The product captures both speed and efficiency simultaneously:

```
fT × (gm/ID) = [gm / (2π·Cgg)] × (gm/Id) = gm² / (2π·Cgg·Id)
```

- Strong inversion (low gm/ID): fT is high, but gm/ID is low → moderate product.
- Weak inversion (high gm/ID): gm/ID is high, but fT falls exponentially → product collapses.

The peak therefore lands in the **mid-inversion (moderate inversion)** region,
typically gm/ID ≈ 10–15 V^-1 for bulk CMOS.

**Pass criterion:** peak of `fT · (gm/ID)` at `8 ≤ gm/ID ≤ 18 V^-1`

**Failure interpretation:**

| Symptom | Likely cause |
|---------|-------------|
| Peak near gm/ID ≈ 5 | fT over-estimated in strong inversion; cgso/cgdo under-estimated |
| Peak near gm/ID ≈ 22 | Vgs sweep does not extend far enough into subthreshold; fT stays high in weak inversion — possible Cgg extraction error |

---

## Test 5 — Vds Sensitivity

**What it checks:** gm·ro at gm/ID = 10 changes by at least 10 % when Vds
is stepped from 0.25·VDD to 0.75·VDD.

**Physics:** In short-channel MOSFETs, raising Vds intensifies channel-length
modulation and DIBL, modifying ro and hence gm·ro.  Near the triode–saturation
boundary (low Vds ≈ Vdsat), gds is large and falling rapidly; deep in
saturation, CLM slowly raises gds again.  A physically realistic BSIM model
must reflect a significant Vds dependence of gm·ro across this range.

**Pass criterion:** `|gmro(0.75·VDD) / gmro(0.25·VDD) − 1| ≥ 8 %`

> **Note on the threshold:** HP minimum-L nodes have inherently low gmro (5–10),
> so even a real CLM response produces small percentage swings.  The threshold
> is set at 8 % to accommodate this without masking models that truly ignore CLM.

The test is direction-agnostic: gmro may be higher or lower at high Vds
depending on how close the low-Vds point is to Vdsat.

**Failure interpretation:**

| Symptom | Likely cause |
|---------|-------------|
| Change < 10 % | First-order model with no CLM; gm·ro is useless as a design metric |
| Change > 80 % | Low-Vds point (0.25·VDD) is below Vdsat — transistor in triode, not saturation; reduce gm/ID or raise Vds_lo |

---

## Quick Reference: Pass Thresholds

| Test | Quantity checked | Pass range |
|------|-----------------|-----------|
| 1 | Peak gm/ID [V^-1] | 25 – 32 |
| 2 | Non-monotone steps in Id/W | 0 |
| 3a | gmro(2L) / gmro(L) | ≥ 1.5 (no upper cap) |
| 3b | fT(2L) / fT(L) | 0.15 – 0.70 |
| 4 | gm/ID at peak of fT·(gm/ID) [V^-1] | 8 – 18 |
| 5 | |gmro(0.75·VDD)/gmro(0.25·VDD) − 1| | ≥ 8 % |
