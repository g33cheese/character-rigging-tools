# Facial Rigging Tools

Tools for facial rigging corrective and blendshape setup.

This repository contains Maya Python tools developed to support facial rigging corrective workflow automation. The examples demonstrate practical solutions for creating and managing corrective blendshapes, processing sculpted deformations, and integrating corrective shapes into facial rigs. They showcase workflows for corrective delta extraction, automated control connections, and deformation refinement.

## Tools

### Facial Corrective Blendshape Setup

**File:** `face_correctives.py`

A Maya Python tool developed to manage the facial corrective blendshape workflow for a character rig. The script creates posed corrective shapes from a base face mesh, exports them for sculpting, imports the sculpted results, and integrates the resulting deformation deltas into the rig.

**Features**

- Reads corrective definitions from a JSON configuration file, including control mappings, activation values, axes, mirroring, and enable states.
- Creates posed corrective shapes by setting rig control attributes and duplicating the base geometry.
- Exports posed corrective shapes to a Maya Binary file for external sculpting.
- Imports sculpted corrective shapes and organizes them using consistent naming conventions.
- Extracts deformation deltas by comparing sculpted shapes against their original posed shapes.
- Creates a blendShape deformer and connects corrective weights to the corresponding rig control attributes.
- Organizes and hides corrective working groups after setup.
- Logs workflow operations, missing dependencies, and errors to assist with troubleshooting.

**Usage**

Run `main(geo)` in Maya, passing the name of the base face geometry. The workflow creates and exports posed correctives, imports the sculpted results, extracts deformation deltas, and connects the corrective blendshapes to the facial rig. Set skip_export=True to skip the export step when posed corrective shapes have already been prepared.

**Requirements**

- Autodesk Maya
- A facial rig with the expected corrective control attributes
- A base face mesh with matching topology across the neutral, posed, and sculpted shapes
- A rigData folder containing face_correctives.json
- A sculpted corrective file named sculpted_face_correctives.mb, created through the external sculpting step

**Pipeline considerations**

The workflow relies on consistent naming conventions to match posed shapes, sculpted shapes, blendShape targets, and rig controls. The corrective definitions and file paths are expected to follow the structure used by the original production pipeline. The sculpting stage is performed externally; this script handles preparation, file exchange, delta extraction, and rig integration.


