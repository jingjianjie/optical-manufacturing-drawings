# Environment and portable configuration

Offline tools usePython 3.10+ plus requirements.txt; tested environment uses3.11. Install in a virtual environment; run scripts from any working directory using their actual path. No fixed drive, username, interpreter location or agent installation path is assumed.

- Font: `--font PATH` on init/freeze_project, or `OPTICAL_DRAWING_FONT`. Select a CJK font covering the actual text/symbols. The file is copied for local reproducibility and registered with ezdxf. project.json uses relative paths. No font is distributed in this source package or automatically in manufacturing ZIPs.
- Live API: Windows, licensed OpticStudio and requirements-zos.txt. `OPTICSTUDIO_DIRECTORY` optionally selects an installation; otherwise ZOSPy discovery is used. Script connection is standalone with a Windows named mutex and finally-disconnect. GUI/license conflicts are reported; unrelated processes are not terminated.
- Native viewer exports may not be available in older OpticStudio. Use package system_layout.py instead of depending on viewer screenshots or another skill.
- STEP sections: install requirements-step.txt. `--ocp-path` is optional if OCP is already importable. This is a read-only plane section at global x=0, shown in z/y, not a general arbitrary-coordinate CAD inspector.
- Optional DWG: .NET8 and ACadSharp3.8.35, installed by the CadBridge project. DXF workflow does not require this bridge or AutoCAD.

The initial frozen-manifest records local audit paths and runtime versions. These are private project artifacts, not part of the public skill release. Use release.py's allowlist for public source distribution; do not publish .pdfout directories.
