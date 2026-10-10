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

Run `reference_geo()` as the first mGearPre Custom Step. By default, the function uses the current Maya workspace to determine the asset name, variant, and geometry file path. Optional arguments allow the caller to override the workspace path, asset name, and geometry file path.

**Requirements**

- Autodesk Maya
- A valid Maya workspace folder following the expected asset and variant naming convention
- Access to the corresponding geometry file

**Pipeline considerations**

The geometry path, namespace format, and database variation value have been sanitized for this portfolio example. They may need to be adapted to the conventions of a production pipeline.
