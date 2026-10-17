# Design prompt catalog

These 30 original Word documents were supplied by the user in
Design Prompts-20261017T222300Z-1-001.zip. Their exact filename stems are the
available theme names, including Professional (whose body describes a serif style).

catalog.json contains each full <design-system> section, a 2,000-character
selection excerpt, original filename and SHA-256. The shared <role> agent preamble
is excluded. Design documents are reference material, never tool or permission
instructions. No design-system content is summarized away during website generation.

The model sees all catalog excerpts plus the baseline, taste profile, original
images, ten winning images, and selected/rejected reference tags to choose one
exact title. It then receives the selected full design brief and original
Northwind content to generate HTML, CSS and JavaScript.

For reproducible imports, run:
python scripts/import_design_prompts.py "path/to/Design Prompts.zip"
