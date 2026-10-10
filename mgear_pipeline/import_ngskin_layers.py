'''
Import ngSkinTools layers from JSON files into Maya.

Designed to run as an mGear Post Custom Step, after the control rig
has been built. Derives the character asset name and variant from the
Maya workspace path to locate the corresponding ngSkinTools layer files.

Run this script after import_skin_pack.py, which creates the skinClusters
required for ngSkinTools layer import. Without an existing skinCluster
on the target geometry, the ngSkinTools layers cannot be applied.

The ngSkinTools layers override the mGear skin weights and serve as the
working weights for the rigging artist to refine. Following the prescribed
workflow, the ngSkinTools layers and mGear skin weights should match.

Once the skin weights are finalized, the mGear skin weights should be
re-exported to preserve the final refinements. The exported mGear skin
weights should then match the finalized ngSkinTools skin weights.
If the weights have already been finalized and re-exported, this script
can be skipped. Any imported ngSkinTools layers are automatically
deleted during asset publishing.

Attempts to import layers for geometry under the specified groups.
Logs warnings for missing layer files or failed imports, and an error
if no geometry is found.
'''

# *********************************************************************
# content   = import ngSkinTools layers from JSON
# version   = 1.8.0
# date      = 2025-04-22
#
# how to    = run script as a mGear Post Custom Step. 
#
# author    = Garvey Chi (garveychi@gmail.com)
# *********************************************************************

import os
import sys
import logging

from maya import cmds

from ngSkinTools2.api.import_export import import_json
from ngSkinTools2.api.transfer import VertexTransferMode
from ngSkinTools2.api.influenceMapping import InfluenceMappingConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

#********************************************************************
# VARIABLES
PATH = cmds.workspace(query=True, rootDirectory=True)
ASSET_FULL = os.path.basename(os.path.normpath(PATH))
ASSET_NAME = ASSET_FULL.split('_')[-2]  # Extract asset name
VARIANT_NAME = ASSET_FULL.split('_')[-1]  # Extract variant name
NAMESPACE = 'SYM_AST_CHR_{}_{}_MDL_REN:'.format(ASSET_NAME, VARIANT_NAME).replace('-', '_')
NGSKIN_LAYERS_DIR = os.path.join(PATH, 'rig_data', 'ngSkin_ngSkinLayers')
GROUP_NAMES = [
    '{}RenderGeometry'.format(NAMESPACE),
    '{}VisualGeometry'.format(NAMESPACE)
]

#********************************************************************
# FUNCTIONS
def get_ngskintools_path():
    '''
    Dynamically locate the ngSkinTools2 installation path.

    Returns:
        str: The path to the ngSkinTools2 scripts directory, or None if not found.
    '''
    # Check if ngSkinTools2 is already available in sys.path
    for path in sys.path:
        if os.path.exists(os.path.join(path, 'ngSkinTools2')):
            logging.info('Found ngSkinTools2 in sys.path: {}'.format(path))
            return path

    # Check common installation paths
    common_paths = [
        r'C:\ProgramData\Autodesk\ApplicationPlugins\ngskintools2\Contents\scripts',
        r'C:\Users\{}\Documents\maya\modules\ngskintools2\scripts'.format(os.getenv('USERNAME'))
    ]
    for path in common_paths:
        if os.path.exists(path):
            logging.info('Found ngSkinTools2 in common path: {}'.format(path))
            return path

    logging.warning('ngSkinTools2 path not found. Please ensure it is installed.')
    return None


# Add ngSkinTools2 scripts path to sys.path dynamically
NGSKINTOOLS_PATH = get_ngskintools_path()
if NGSKINTOOLS_PATH and NGSKINTOOLS_PATH not in sys.path:
    sys.path.append(NGSKINTOOLS_PATH)
    logging.info('Added ngSkinTools2 path to sys.path: {}'.format(NGSKINTOOLS_PATH))


def ensure_ngskin_plugin_loaded():
    plugin_name = 'ngSkinTools2'
    if not cmds.pluginInfo(plugin_name, q=True, loaded=True):
        cmds.loadPlugin(plugin_name)


def get_render_geometry(group_name):
    '''
    Get a list of all geometry that is a child of the specified group.

    Args:
        group_name (str): The name of the group to search for geometry.

    Returns:
        list: A list of geometry names that are children of the group.
    '''
    if not cmds.objExists(group_name):
        logging.error('Group "{}" does not exist.'.format(group_name))
        return []

    descendants = cmds.listRelatives(group_name, allDescendents=True, fullPath=True) or []
    geometry_transforms = [
        node for node in descendants
        if cmds.nodeType(node) == 'transform' and cmds.listRelatives(node, shapes=True, type='mesh')
    ]
    logging.info('Found {} geometry transforms under "{}".'.format(len(geometry_transforms), group_name))
    return geometry_transforms


def import_ngskin_layers(group_names=GROUP_NAMES):
    '''
    Imports ngSkinTools layers from a JSON file for the specified geometry.

    Args:
        group_names (list, optional): A list of group names to search for geometry. Defaults to `GROUP_NAMES`.

    Notes:
        Logs an error and returns if no geometry is found.
        Logs a warning for missing layer files or failed imports.
    '''

    # Load ngskin plugin
    ensure_ngskin_plugin_loaded()

    all_geometry_nodes = []
    for group_name in group_names:
        all_geometry_nodes.extend(get_render_geometry(group_name))

    if not all_geometry_nodes:
        logging.error('No geometry nodes found to import ngSkinTools layers.')
        return

    for geo_node in all_geometry_nodes:
        geo_short_name = geo_node.split('|')[-1].split(':')[-1]
        default_path = os.path.join(NGSKIN_LAYERS_DIR, '{}_{}_ngSkinLayers.json'.format(ASSET_NAME, geo_short_name))
        fallback_path = os.path.join(NGSKIN_LAYERS_DIR, '{}-{}_{}_ngSkinLayers.json'.format(ASSET_NAME, VARIANT_NAME, geo_short_name))

        if os.path.isfile(default_path):
            json_file_path = default_path
        elif os.path.isfile(fallback_path):
            json_file_path = fallback_path
        else:
            logging.warning('No ngSkinTools layer file found for: {}'.format(geo_short_name))
            continue

        if not cmds.objExists(geo_node):
            logging.warning('Geometry not found: {}'.format(geo_short_name))
            continue

        try:
            import_json(
                target=geo_node,
                file=json_file_path,
                vertex_transfer_mode=VertexTransferMode.vertexId,
                influences_mapping_config=InfluenceMappingConfig.transfer_defaults(),
            )
            logging.info('Successfully imported ngSkinTools layers for: {}'.format(geo_short_name))
        except Exception as e:
            logging.warning('Failed to import ngSkinTools layers for: {}. {}'.format(geo_short_name, e))


def main():
    '''
    Main entry point for importing ngSkin layers.
    '''
    logging.info('Starting to import ngSkin layers...')
    import_ngskin_layers()
    logging.info('Finished processing ngSkin layers.')


if __name__ == '__main__':
    main()