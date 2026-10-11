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


### MetaHuman Facial Blendshape Connections

**File:** `connect_face_blends.py`

A Maya Python utility designed to connect facial blendshape targets to a MetaHuman face rig. The script identifies the head geometry, blendshape targets, and corresponding facial controls, then creates or reuses a blendShape deformer and establishes connections based on target naming conventions.

**Features**

- Verifies the presence of the MetaHuman face rig and expected head geometry.
- Identifies facial blendshape targets and derives their corresponding control names from naming conventions.
- Creates a blendShape deformer or reuses an existing one.
- Connects facial control translations to blendShape weights for positive and negative movement along the X and Y axes.
- Uses clamp and multiplyDivide utility nodes to isolate movement direction and limit blendShape weights to a range of 0–1.
- Resets eligible facial control translation attributes to their default values while preserving locked or connected attributes.
- Sets the face GUI follow-head control to its expected default value.
- Logs connection operations, missing scene elements, unsupported naming conventions, and errors to assist with troubleshooting..

**Usage**

Run `connect_face_blends.py` in Maya with the MetaHuman face rig and corresponding blendshape targets loaded in the scene. The script automatically identifies supported targets, creates or reuses the head_BLS blendShape deformer, and connects the targets to their corresponding facial controls. After the connection process, facial control attributes are reset to their default values.

**Requirements**

- Autodesk Maya
- A MetaHuman face rig containing the expected headGui_grp and facial controls
- Blendshape targets named using the expected MSH_ prefix and naming convention, including the control identifier, axis (x or y), and direction suffix (pos or neg)

**Pipeline considerations**

The script uses predefined geometry and deformer names and relies on consistent naming conventions to map blendshape targets to facial controls. The positive and negative movement connections use utility nodes to prevent control values from affecting the opposite directional target. Scene naming conventions and target mappings may need to be adapted for other MetaHuman assets or production pipelines.


