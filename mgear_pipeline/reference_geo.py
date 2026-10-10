'''
Reference character geometry into the current Maya scene.

Designed to run as the first mGear Pre Custom Step. Derives the character
asset name and variant from the Maya workspace folder, constructs the
geometry file path, and references the geometry into the scene.

Ensures the expected Group/Main/Geometry hierarchy exists and parents the
referenced Geo group under Geometry. Existing geometry references are
checked to avoid referencing the same geometry again.

The path, asset_name, and geo_path arguments allow callers to override
the workspace path, asset name, and geometry file path respectively.
The variant name is always derived from the workspace folder.
'''

# *********************************************************************
# content   = reference character geo
# version   = 1.5.0
# date      = 2025-06-03
#
# how to    = run function as first mGear Pre Custom Step
#
# author    = Garvey Chi (garveychi@gmail.com)
# *********************************************************************

import os
import logging
import traceback
from maya import cmds

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def ensure_node_parent(node, parent):
    '''
    Ensure that a node exists and is parented to the specified parent.

    Args:
        node (str): The name of the node to ensure.
        parent (str): The name of the parent node. If None, the node will be at the root.
    '''
    if cmds.objExists(node):
        parents = cmds.listRelatives(node, parent=True) or []
        if parent and parent not in parents:
            cmds.parent(node, parent)
            logging.info('Parented existing "{}" node to "{}".'.format(node, parent))
        else:
            logging.info('Asset node "{}" already exists and is correctly parented.'.format(node))
    else:
        if parent:
            cmds.group(name=node, empty=True, parent=parent)
            logging.info('Created asset node "{}", parented it to "{}".'.format(node, parent))
        else:
            cmds.group(name=node, empty=True)
            logging.info('Created asset node "{}" at the root.'.format(node))


def reference_geo(path=None, asset_name=None, geo_path=None):
    '''
    Reference asset geometry into the scene.

    Args:
        path (str): Root workspace path. If None, queries the current workspace.
        asset_name (str): Name of the asset. If None, extracts it from the workspace path.
        geo_path (str): Path to the geometry file. If None, constructs the default path.
    '''
    logging.info('Starting reference_geo function.')

    path = path or cmds.workspace(query=True, rootDirectory=True)    
    asset_full = os.path.basename(os.path.normpath(path))

    if not asset_name:        
        asset_name = asset_full.split('_')[-2]  # Extract asset name
    variant_name = asset_full.split('_')[-1]  # Extract variant name

    geo_path = geo_path or r'\\asset-server\show\assets\characters\model\{}_{}_model.mb'.format(asset_name, variant_name)
    logging.info('geo_path: {}'.format(geo_path))
    namespace = 'CHR_{}_{}_model'.format(asset_name, variant_name).replace('-', '_')
    logging.info('Using namespace: {}'.format(namespace))

    if not os.path.exists(geo_path):
        logging.error('Geometry file not found: {}'.format(geo_path))
        return

    # Ensure hierarchy
    master_node = 'Group'
    ensure_node_parent(master_node, None)
    ensure_node_parent('Main', master_node)
    ensure_node_parent('Geometry', master_node)

    # Reference the geometry
    try:
        geo_node = '{}:Geo'.format(namespace)
        if cmds.objExists(geo_node):
            # Check if geo_node is parented to 'Geometry'
            parents = cmds.listRelatives(geo_node, parent=True) or []
            if 'Geometry' not in parents:
                cmds.parent(geo_node, 'Geometry')
                logging.info('{} exists but was not parented to Geometry. Parented now.'.format(geo_node))
            else:
                logging.info('{} already exists and is correctly parented to Geometry. Skipping geometry reference.'.format(geo_node))
        else:
            logging.info('Referencing geometry from: {}'.format(geo_path))
            cmds.file(geo_path, reference=True, namespace=namespace, mergeNamespacesOnClash=False, preserveReferences=True, type='mayaBinary')
            cmds.parent(geo_node, 'Geometry')
            logging.info('Successfully referenced geometry and parented its Geo group to the Geometry node.')
            # Set database variant to 'DEFAULT'
            cmds.setAttr('{}:database.variation'.format(namespace), 'DEFAULT', type='string')
            logging.info('Set database variant to DEFAULT for namespace: {}'.format(namespace))
    except Exception as e:
        logging.error('Failed to reference geometry: {}\n{}'.format(e, traceback.format_exc()))


def main():
    reference_geo()


if __name__ == '__main__':
    main()