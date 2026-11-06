# Third-party dependencies and asset provenance

The MIT license covers this repository's source, documentation and newly generated example assets. Dependencies retain their own terms; none of their binaries or source distributions is vendored here. Installing requirements downloads them from their providers. Keep upstream notices when distributing those dependencies.

|Dependency|Role|Upstream license/source|
|---|---|---|
|NumPy|Geometry arrays|[BSD-3-Clause](https://github.com/numpy/numpy/blob/main/LICENSE.txt)|
|ezdxf|DXF entities and drawing frontend|[MIT](https://github.com/mozman/ezdxf/blob/master/LICENSE)|
|Matplotlib|Vector PDF and layout|[Matplotlib license](https://matplotlib.org/stable/project/license.html)|
|fontTools|Glyph coverage|[MIT](https://github.com/fonttools/fonttools/blob/main/LICENSE)|
|Pillow|Image handling|[HPND](https://github.com/python-pillow/Pillow/blob/main/LICENSE)|
|pypdf|PDF merge/inspection|[BSD-3-Clause](https://github.com/py-pdf/pypdf/blob/main/LICENSE)|
|pypdfium2 / PDFium|Render final PDF proofs|[Apache-2.0 or BSD-3-Clause; PDFium and bundled third-party notices](https://pypdfium2-team.github.io/pypdfium2/readme.html#licensing)|
|ZOSPy|Optional live ZOSAPI|[MIT](https://github.com/MREYE-LUMC/ZOSPy/blob/main/LICENSE)|
|ACadSharp|Optional DWG bridge|[MIT](https://github.com/DomCR/ACadSharp/blob/master/LICENSE)|
|cadquery-ocp / Open CASCADE|Optional native STEP reading|[Upstream licensing](https://github.com/CadQuery/OCP)|
|OpticStudio / ZOSAPI|External licensed application|Separate vendor installation/license; not redistributed|

The default PDF path uses Matplotlib + pypdf + PDFium. It does not require PyMuPDF. PyMuPDF's AGPL/commercial licensing is documented at [its official site](https://pymupdf.readthedocs.io/en/latest/about.html); replacing the backend later warrants reviewing dependency terms again.

## Assets

`make_template.py` creates the generic A4 grid from primitives; `symbol_blocks.py` creates arrow and circle-cross blocks. They read no historical CAD or screenshot. `make_example.py` creates fictitious glass names and a synthetic prescription. These generated assets are included under this repository's MIT license. Their notation is an example convention, not a claim of compliance with an optical drawing standard.

`docs/previews/` contains the generated synthetic four-page PDF and its rendered PNG previews. No real prescription is used. The PDF uses vector glyph outlines, not a bundled font program; local rendering used Noto Sans SC under its font license. No font file is included. These previews illustrate the workflow, not an approved manufacturing order.

Historical customer/company drawings, extracted DWG/DWT templates, screenshots, real designs, agent logs and fonts were deliberately excluded. Select fonts with rights appropriate to your use; a local dependency snapshot does not confer redistribution rights. The CAD helper source and manufacturing pipeline were consolidated from the author's working toolset and are included here under MIT; external skill installations are not runtime dependencies.
