'''
Import mGear ASCII skin pack into Maya scene.

Designed to run as a mGear Post Custom Step, after the control rig
has been built. Derives the character asset name and variant from the 
Maya workspace path to locate the corresponding skin pack.

Attempts to import the skin pack from the primary path, with a
variant-specific fallback path if the primary file is unavailable.
The import is handled by mGear's skin pack utility.

Import errors are logged if the skin pack cannot be found or the
import operation fails.
'''

# *********************************************************************
# content   = import mGear skinPack 
# version   = 1.4.0
# date      = 2025-04-22
#
# how to    = run function as a mGear Post Custom Step
#
# author    = Garvey Chi (garveychi@gmail.com)
# *********************************************************************

import os
import logging

import maya.cmds as cmds
import mgear.core.skin as skin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

#********************************************************************
# VARIABLES
PATH = cmds.workspace(query=True, rootDirectory=True)
ASSET_FULL = os.path.basename(os.path.normpath(PATH))
ASSET_NAME = ASSET_FULL.split('_')[-2]  # Extract asset name
VARIANT_NAME = ASSET_FULL.split('_')[-1]  # Extract variant name
SKINPACK_PATH = os.path.join(PATH, 'rig_data', 'mGear_skinpack', '{}.gSkinPack'.format(ASSET_NAME))
FALLBACK_SKINPACK = os.path.join(PATH, 'rig_data', 'mGear_skinpack', '{}-{}.gSkinPack'.format(ASSET_NAME, VARIANT_NAME))
#********************************************************************
# FUNCTION
def import_skin_pack():
    '''
    Imports the character's mGear skin pack into Maya.

    Notes:
        Attempts to import the default skin pack first, then uses a
        variant-specific fallback if the default is unavailable. 
        Logs an error if neither file exists or the import fails.
    '''
    file_path = SKINPACK_PATH
    if not os.path.isfile(file_path):
        logging.warning('Skin pack not found at primary path: {}'.format(file_path))
        if os.path.isfile(FALLBACK_SKINPACK):
            logging.info('Found fallback skin pack: {}'.format(FALLBACK_SKINPACK))
            file_path = FALLBACK_SKINPACK
        else:
            logging.error('Skin pack file does not exist at either path:\n - {}\n - {}'.format(SKINPACK_PATH, FALLBACK_SKINPACK))
            return False
    try:
        skin.importSkinPack(file_path)
        logging.info('Successfully imported skin pack: {}'.format(os.path.basename(file_path)))
        return True
    except Exception as e:
        logging.error('Failed to import skin pack: {}'.format(e))
        return False


def main():
    '''
    Main entry point to run the skin pack import.
    '''
    logging.info('Starting skin pack import for asset')

    if import_skin_pack():
        logging.info('Skin pack import completed for asset')
    else:
        logging.error('Skin pack import failed for asset')


if __name__ == '__main__':
    main()