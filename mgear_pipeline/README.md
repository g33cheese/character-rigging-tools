# mGear Pipeline Tools

Tools for mGear build preparation, skinning import (data management), and custom rig processing. 

This repository contains Maya Python tools developed to support character rigging workflows and pipeline automation. The examples demonstrate practical solutions for rigging pipeline tasks such as geometry referencing, rig data import and application, as well as show specific custom rig setup. 

## Tools

### Reference Asset Geometry

**File:** `reference_geo.py`

A Maya utility designed to run as the first mGear Pre Custom Step. The script derives the character asset name and variant from the Maya workspace folder, constructs the geometry file path, and references the geometry file path, and references the geometry into the scene.

**Features**

- Creates or verifies the expected Group/Main/Geometry hierarchy.
- References geometry using an asset-specific namespace.
- Parents the referenced Geo group under Geometry.
- Checks for an existing geometry node to avoid creating a duplicate reference.
- Logs operations and errors to assist with troubleshooting.

**Usage**

Run `reference_geo()` as the first mGear Pre Custom Step. By default, the function uses the current Maya workspace to determine the asset name, variant, and geometry file path. Optional arguments allow the caller to override the workspace path, asset name, and geometry file path.

**Requirements**

- Autodesk Maya
- A valid Maya workspace folder following the expected asset and variant naming convention
- Access to the corresponding geometry file

**Pipeline considerations**

The geometry path, namespace format, and database variation value have been sanitized for this portfolio example. They may need to be adapted to the conventions of a production pipeline.


### Import mGear Skin Pack

**File:** `import_skin_pack.py`

A Maya utility designed to run as a Post Custom Step after the control rig has been built. The script derives the character asset name and variant from the Maya workspace folder to locate and import the corresponding mGear skin pack.

**Features**

- Derives the character asset name and variant from the Maya workspace path.
- Attempts to import the default skin pack, falling back to a variant-specific skin pack if the default is unavailable.
- Logs import status and reports missing files or import failures.

**Usage**

Run `import_skin_pack()` as a mGear Post Custom Step. The function uses the current Maya workspace to determine the asset name, variant, and skin pack paths.

**Requirements**

- Autodesk Maya
- mGear plug-in, including mgear.core.skin
- Access to the corresponding .gSkinPack file

**Pipeline considerations**

The skin pack path, namespace format, and database variation value have been sanitized for this portfolio example. They may need to be adapted to the conventions of a production pipeline.


### Import ngSkinTools Layers

**File:** `import_ngskin_layers.py`

A Maya utility designed to run as an mGear Post Custom Step, after the control rig has been built and the mGear skin pack imported. Imports ngSkinTools layers from JSON files onto the corresponding geometry, providing the rigging artist with editable skin-weight layers for further refinement.

**Features**

- Derives the character asset name and variant from the Maya workspace path.
- Locates ngSkinTools layer files using default and variant-specific filename conventions.
- Identifies geometry under the specified RenderGeometry and VisualGeometry groups.
- Imports ngSkinTools layers using vertex ID-based transfer and the default influence mapping configuration.
- Logs missing geometry, missing layer files, and import failures.

**Usage**

Run import_ngskin_layers() as an mGear Post Custom Step, after import_skin_pack.py. The function searches the specified geometry groups and imports matching ngSkinTools layer files from the expected rig_data/ngSkin_ngSkinLayers directory.
Once skin-weight refinement is complete, re-export the finalized mGear skin weights. If the weights have already been finalized and re-exported, this step can be skipped.

**Requirements**

- Autodesk Maya
- ngSkinTools 2
- A skinCluster on the target geometry, created by running import_skin_pack.py first
- Corresponding geometry and ngSkinTools JSON layer files

**Pipeline considerations**

The geometry group names, namespace format, and skin-layer file paths have been sanitized for this portfolio example. They may need to be adapted to the conventions of a production pipeline. The production publishing process is responsible for deleting imported ngSkinTools layers.


### Custom Rig Setup

**File:** `custom_rig_setup.py`

A Maya utility designed to run as an mGear Post Custom Step after the guide template build has generated the base rig. The script adds custom rig components, control setups, and connections that extend the standard mGear build process.

**Features**

- Creates NPO (mGear's null node) groups, sub-controls, and gimbal controls.
- Reconnects spine IK controls through custom sub-controls.
- Sets up spine control scaling and UI control constraints.
- Adds IK arm and leg length adjustment attributes.
- Configures foot roll, finger and toe splay, and arm twist controls.
- Adjusts arm and leg roundness attribute limits.
- Creates and integrates hip and shoulder hydraulic driver systems.
- Sets joint labels for overlapping joints.

**Usage**

Run custom_rig_setup() as an mGear Post Custom Step, after the guide template build has generated the base rig. The function performs the custom setup operations required to extend the generated character rig.

**Requirements**

- Autodesk Maya
- PyMEL
- mGear plug-in, including mgear.rigbits
- Custom CreateVisAttrs module

**Pipeline considerations**

The rig node names, control names, attribute connections, and naming conventions have been sanitized for this portfolio example where applicable. The script is designed for a specific mGear character rig template and may need to be adapted to the structure and conventions of a production pipeline. It expects the relevant rig components to exist in the scene before execution.
