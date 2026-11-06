# Self-contained system layout

```sh
python scripts/system_layout.py --zos design.zos --mechanical mechanical.json --out layout.png --save-snapshot layout-data.json
python scripts/system_layout.py --snapshot layout-data.json --mechanical mechanical.json --out layout-replay.png
```

Live mode reads the source API using zos_read.session, captures five meridional pupil samples per field at the primary wavelength, and closes the connection. Radial and Rectangular field normalization are supported. Rays are truncated on first invalid/error/vignetted surface; ray data absent from an offline snapshot is explicitly identified.

The current renderer supports centered, untilted Standard spherical/plane surfaces, positive optical path thickness and the provided mechanical recipe. It rejects unsupported transforms or surface types rather than drawing an invented layout. With a recipe it displays individual substrate outlines and recipe part names; without it the mechanical-radius/clear+chip outline is a simplified optical baseline. Solid fill is mechanical body, dashed curves show clear aperture; plots use equal axis scale and GetGlobalMatrix's reference origin.

The PNG supports structural inspection, not performance certification. Read material/surface data via API, and retain native STEP/DXF as independent geometry evidence. Do not infer vignetting acceptance from the small plotted sample.
