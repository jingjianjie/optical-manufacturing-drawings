# Sanitized ZOS parser sample

`sanitized-shuffled.zos` and its text export `sanitized-shuffled.zmx` are deliberately nonfunctional parser/load samples generated in a **new OpticStudio system**. No private design was loaded or copied. Real curvature, glass, thickness, comments, design fields, optimization targets and manufacturing identity are not retained.

- Ten fictitious radii are deterministically shuffled; their order has no correspondence with a private prescription.
- All object-to-surface and inter-surface thicknesses are zero. IMAGE has no following physical interval; OpticStudio saves its trailing thickness as an infinity sentinel.
- All materials are empty (air), surface comments and author are empty, field X/Y are zero, ray aiming is off, and no original merit function or configurations are copied.
- System aperture is **entrance pupil diameter 0.1 mm**; STOP semi-diameter is **0.05 mm**. This specifies diameter versus radius explicitly.
- A positive **0.55 µm wavelength with unit weight** remains as a software placeholder. Environmental/runtime defaults are fresh application defaults, not source design conditions.

This sample is useful for opening ZOS/ZMX, reading surfaces, testing indexing and handling zero intervals. It is **not a usable optical design or a manufacturing drawing example**. For meaningful offline drawing examples, use `scripts/make_example.py`, which generates separate synthetic glass geometry.

Regenerate on Windows with licensed OpticStudio and ZOSPy:

```sh
python scripts/make_sanitized_zos.py --out samples
```

The generated ZOS/ZMX sample is included under the repository MIT license. Proprietary software is needed to open native ZOS; no OpticStudio executable or glass catalog is distributed. `sanitization.json` records the checked values and hashes without local source paths.
