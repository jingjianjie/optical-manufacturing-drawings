# Integrated knowledge: no other skill installation required

|Former source topic|What is now in this package|Deliberately outside this package|
|---|---|---|
|Optical visual review|system_layout.py; actual mechanical outlines, CA dashed, subparts separated, ray failure truncation, manufacturing names from recipe|Optimizer G0/G1 schedule and project-specific diagnostic thresholds|
|ZOSAPI automation|api-alignment.md; zos_read/freeze_inputs/zos_export/compare_rays; enum/signature inspection, readback and serialized connection|General NSC detectors, optimizer operand library|
|Zemax coordinates|optical-concepts/geometry-and-notation; local/global/physical/modeling direction, GCRS, explicit index mapping|Full off-axis/reflection/coordinate-break design tools|
|Lens audit|Material+catalog+wavelength identity; standalone EFL vs system; cemented interface vs substrate; field/NA terminology|Claiming coupling performance or catalog acceptance from drawings|
|Optical design workflow|CT/ET/min thickness distinction; nominal geometry separate from production tolerances; do not optimize for a prettier drawing|Design optimization, multi-wavelength performance search|
|CAD DWG/DXF|cad/ contains its source helper, bridge and font/roundtrip guidance|Proprietary application installation, fonts and historical templates|

## Field, pupil and NA concepts relevant to drawings

Finite object height describes a physical field, while an angular field describes direction; entrance pupil diameter is not automatically a fiber core diameter or a mechanical outside diameter. NA is n·sin(theta) in a stated medium and at a stated physical end. Reverse modeling can simplify the description, but the physical fiber and measurement planes keep their identities. Record which end, field type, system aperture and material medium the specification refers to.

“Maximum usable fiber diameter/NA” may permit declared clipping, while “no-vignetting coupling” requires an explicit trace domain and criterion. Do not infer either from a few layout rays or geometric outlines. Drawing production preserves the approved definition and cites its verification; it does not silently replace it with a new optical acceptance test.

## Native CAD evidence

Prefer actual solid sections and analytic surface/units checks. STEP CARTESIAN_POINT includes construction/control points, so a bounding box over every point is not proof of lens OD or CT. Verify units, surface range, expected bodies, vertex positions and analytic radii where available; dummy planes need stated finite thickness. Manufacturing edge differences remain explicit.

## Visual checks

Use the same physical-surface list for drawing and ray plotting. Each sample stops at the first error or vignette; later finite intersections do not imply transmission. Check radius on the actual surface, not the largest beam in a whole group against that group's first CA. Label using the part map and source surface numbers, not unrelated auto-generated L numbers.

The former sources inform these concepts; only the necessary parts are consolidated here. This package does not import or load their SKILL.md files at runtime.
