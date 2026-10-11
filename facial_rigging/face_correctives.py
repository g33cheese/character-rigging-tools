'''
Set up facial corrective blendshapes for a Maya character rig.

Manages the corrective workflow, from creating and exporting posed
corrective shapes for sculpting to importing sculpted shapes and
integrating them into the facial rig. Uses a JSON configuration file
to define corrective controls, activation values, axes, mirroring,
and enable states.

Extracts deformation deltas by comparing the sculpted shapes against
their original posed shapes, then creates a blendShape node and
connects its weights to the corresponding rig control attributes.

Organizes and hides the corrective working groups after setup.
Workflow operations and errors are logged throughout the process.
'''

# *********************************************************************
# content   = Sets up corrective blendshapes for tippett face rig.
#             Manages the entire corrective workflow
#             (create → export → sculpt → import → setup)
#
# version   = 2.6.0
# date      = 2026-02-17
#
# how to    = run function to set up corrective blendshapes for tippett face rig
#
# author    = Garvey Chi (garveychi@gmail.com)
# *********************************************************************

import os
import json
import logging

from maya import cmds

from maya.api import OpenMaya as om2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def rig_data_path():
    '''
    Get the path to the rigData folder.
    
    Returns:
        str: The path to the rigData folder.
    '''
    path = cmds.workspace(query=True, rootDirectory=True)
    parent_path = os.path.dirname(os.path.normpath(path)) + os.sep
    rig_data_folder_path = '{}rigData'.format(parent_path)
    return rig_data_folder_path


def read_correctives_data():
    '''
    Read corrective shape information from the rigData JSON file.

    Returns:
        dict: A dictionary containing corrective shape information, or None if the file could not be read.
    '''
    file_path = os.path.join(rig_data_path(), 'face_correctives.json')
    if not os.path.isfile(file_path):
        logging.error('Corrective shape information file not found: {}'.format(file_path))
        return None

    try:
        with open(file_path, 'r') as f:
            correctives_data = json.load(f)
        logging.info('Successfully read corrective shape information from: {}'.format(file_path))
        return correctives_data
    except Exception as e:
        logging.error('Failed to read corrective shape information: {}'.format(e))
        return None


def create_correctives(geo=None):
    '''
    Create correctives for sculpting

    Args:
        geo (str): The name of the base geometry for which to create correctives.
    '''
    if not geo:
        logging.warning('Base geometry not provided. Cannot create correctives.')
        return

    if not cmds.objExists('correctives_grp'):
        try:
            corrective_group = cmds.group(empty=True, name='correctives_grp')
            logging.info('Created correctives group: correctives_grp')
        except Exception as e:
            logging.error('Failed to create correctives group: {}'.format(e))
            return
    else:
        corrective_group = 'correctives_grp'
        logging.info('Correctives group already exists in the scene. Skipping creation.')

    correctives_data = read_correctives_data()
    if not correctives_data:
        return

    # Create corrective shapes based on JSON data
    for corrective_name, values in correctives_data.items():
        control_name = values.get('control')
        on_value = values.get('on_value')
        axis = values.get('axis')
        mirror = values.get('mirror')
        enable = values.get('enable')

        try:
            # If enable is False, skip creation of corrective shape
            if not enable:
                logging.info('Corrective {} is not enabled. Skipping creation.'.format(corrective_name))
                continue

            # Enable is True
            trans_attr = 't{}'.format(axis)
            if mirror:
                # Create both L and R versions
                if corrective_name.startswith('L_'):
                    left_name = corrective_name
                    right_name = corrective_name.replace('L_', 'R_', 1)
                elif corrective_name.startswith('R_'):
                    right_name = corrective_name
                    left_name = corrective_name.replace('R_', 'L_', 1)
                else:
                    # If no side prefix, default to creating L_ and R_ variants
                    left_name = 'L_{}'.format(corrective_name)
                    right_name = 'R_{}'.format(corrective_name)

                for name in (left_name, right_name):
                    # Determine the correct control name based on which side we're creating
                    base_control = correctives_data[corrective_name]['control']
                    if name.startswith('L_'):
                        side_control = base_control.replace('CTRL_R_', 'CTRL_L_')
                    else:  # R_ side
                        side_control = base_control.replace('CTRL_L_', 'CTRL_R_')

                    cmds.setAttr('{}.{}'.format(side_control, trans_attr), on_value)  # Set control value to on_value
                    corrective_target = cmds.duplicate(geo, name=name)[0]
                    cmds.parent(corrective_target, corrective_group)
                    cmds.setAttr('{}.{}'.format(side_control, trans_attr), 0)  # Reset control value to 0
                    logging.info('Created corrective shape: {}'.format(corrective_target))
            else:
                # No mirror requested; create single target
                cmds.setAttr('{}.{}'.format(control_name, trans_attr), on_value)  # Set control value to on_value
                corrective_target = cmds.duplicate(geo, name=corrective_name)[0]
                cmds.parent(corrective_target, corrective_group)
                cmds.setAttr('{}.{}'.format(control_name, trans_attr), 0)  # Reset control value to 0
                logging.info('Created corrective shape: {}'.format(corrective_target))

        except Exception as e:
            logging.error('Failed to create corrective shape {}: {}'.format(corrective_name, e))


def export_correctives():
    '''
    Export corrective shapes to the rigData folder.
    '''
    corrective_grp_name = 'correctives_grp'
    posed_grp_name = 'posed_grp'

    # Check for corrective shapes to export
    correctives = cmds.ls('{}|*'.format(corrective_grp_name), type='transform')
    if not correctives:
        logging.warning('No corrective shapes found in the scene to export.')
        return

    # Export file
    export_path = os.path.join(rig_data_path(), 'export_face_shapes.mb')
    try:
        cmds.select(correctives, replace=True)
        cmds.file(export_path, force=True, options='v=0', type='mayaBinary', exportSelected=True)

        if not os.path.isfile(export_path):
            logging.error('Export file was not created: {}'.format(export_path))
            return

        logging.info('Successfully exported corrective shapes to: {}'.format(export_path))
    except Exception as e:
        logging.error('Failed to export corrective shapes: {}'.format(e))
        return

    # Rename group and shapes after successful export
    if cmds.objExists(posed_grp_name):
        logging.warning("'{}' already exists. Skipping rename.".format(posed_grp_name))
        return

    try:
        cmds.rename(corrective_grp_name, posed_grp_name)

        # Rename shapes from _BS to _POSE suffix
        for corrective in cmds.listRelatives(posed_grp_name, children=True, type='transform') or []:
            new_name = corrective.replace('_BS', '_POSE')
            if new_name != corrective:
                cmds.rename(corrective, new_name)

        logging.info('Renamed posed corrective shapes with _POSE suffix.')
    except Exception as e:
        logging.error('Failed to rename corrective groups/shapes: {}'.format(e))


def import_correctives():
    '''
    Import corrective shapes from the rigData folder. 
    '''
    corrective_group = 'correctives_grp'
    posed_grp_name = 'posed_grp'
    sculpted_grp_name = 'sculpted_grp'

    # Rename existing correctives_grp to posed_grp if it hasn't been renamed yet
    # (handles case where export was skipped)
    if cmds.objExists(corrective_group) and not cmds.objExists(posed_grp_name):
        try:
            cmds.rename(corrective_group, posed_grp_name)

            # Rename shapes from _BS to _POSE suffix
            for corrective in cmds.listRelatives(posed_grp_name, children=True, type='transform') or []:
                new_name = corrective.replace('_BS', '_POSE')
                if new_name != corrective:
                    cmds.rename(corrective, new_name)

            logging.info('Renamed correctives_grp to posed_grp with _POSE suffix.')
        except Exception as e:
            logging.error('Failed to rename correctives_grp to posed_grp: {}'.format(e))
            return

    # Import sculpted correctives only
    sculpted_path = os.path.join(rig_data_path(), 'sculpted_face_correctives.mb')

    if not os.path.isfile(sculpted_path):
        logging.error('Sculpted correctives file not found: {}'.format(sculpted_path))
        logging.error('Please create sculpted_face_correctives.mb by sculpting the corrective shapes.')
        return

    import_path = sculpted_path

    if cmds.objExists(sculpted_grp_name):
        try:
            cmds.delete(sculpted_grp_name)
        except Exception as e:
            logging.error('Failed to delete existing {}: {}'.format(sculpted_grp_name, e))
            return

    # Import file
    try:
        cmds.file(import_path, i=True)
        logging.info('Imported corrective shapes from: {}'.format(import_path))
    except Exception as e:
        logging.error('Failed to import corrective shapes: {}'.format(e))
        return

    if not cmds.objExists(corrective_group):
        logging.error("Import did not create '{}'. Import may have failed.".format(corrective_group))
        return

    # Rename group
    try:
        cmds.rename(corrective_group, sculpted_grp_name)
    except Exception as e:
        logging.error('Failed to rename {} to {}: {}'.format(corrective_group, sculpted_grp_name, e))
        return

    # Rename shapes from _BS to _SCULPT suffix
    try:
        for corrective in cmds.listRelatives(sculpted_grp_name, children=True, type='transform') or []:
            new_name = corrective.replace('_BS', '_SCULPT')
            if new_name != corrective:
                cmds.rename(corrective, new_name)
        logging.info("Successfully imported and renamed shapes with '_SCULPT' suffix.")
    except Exception as e:
        logging.error('Failed to rename shapes after import: {}'.format(e))


def get_mfn_mesh(mesh_name):
    '''
    Get MFnMesh object from mesh name'

    Args:
        mesh_name (str): The name of the mesh to get the MFnMesh object for.

    Returns:
        om2.MFnMesh: The MFnMesh object corresponding to the given mesh name.
    '''
    selection_list = om2.MSelectionList()
    selection_list.add(mesh_name)
    dag_path = selection_list.getDagPath(0)
    return om2.MFnMesh(dag_path)


def extract_delta(neutral_mesh, sculpted_shape, posed_shape):
    '''
    Extract delta shapes from sculpted and posed shapes.

    Args:
        neutral_mesh (str): The name of the neutral/base mesh.
        sculpted_shape (str): The name of the sculpted corrective shape.
        posed_shape (str): The name of the posed corrective shape.

    Returns:
        str: The name of the newly created delta shape.
    '''
    # Create delta shape with clean name (remove _SCULPT suffix)
    base_name = sculpted_shape.replace('_SCULPT', '')
    delta_shape = cmds.duplicate(neutral_mesh, name=base_name)[0]

    # Get MFnMesh for each
    neutral_mfn = get_mfn_mesh(neutral_mesh)
    sculpted_mfn = get_mfn_mesh(sculpted_shape)
    posed_mfn = get_mfn_mesh(posed_shape)
    delta_mfn = get_mfn_mesh(delta_shape)

    neutral_points = neutral_mfn.getPoints(om2.MSpace.kObject)
    sculpted_points = sculpted_mfn.getPoints(om2.MSpace.kObject)
    posed_points = posed_mfn.getPoints(om2.MSpace.kObject)

    # Calculate delta: neutral + (sculpted - posed)
    delta_points = om2.MPointArray([
        om2.MPoint(n.x + (s.x - p.x), n.y + (s.y - p.y), n.z + (s.z - p.z))
        for n, s, p in zip(neutral_points, sculpted_points, posed_points)
    ])

    delta_mfn.setPoints(delta_points, om2.MSpace.kObject)
    return delta_shape


def setup_correctives(geo=None):
    '''
    Setup corrective blendshapes on the face rig

    Args:
        geo (str): The name of the base geometry for which to set up correctives.
    '''
    if not geo:
        logging.warning('Base geometry not provided. Cannot extract deltas.')
        return

    posed_group = 'posed_grp'
    sculpted_group = 'sculpted_grp'

    if cmds.objExists('deltas_grp'):
        cmds.delete('deltas_grp')
    delta_group = cmds.group(empty=True, name='deltas_grp')

    # Check for existence of sculpted and posed groups
    if not cmds.objExists(sculpted_group) or not cmds.objExists(posed_group):
        logging.error('Sculpted and/or posed groups not found in the scene. Cannot set up correctives.')
        return

    # Create delta shapes for each corrective
    delta_shapes = []
    delta_map = {}  # Track which correctives have deltas

    for sculpt_shape in cmds.listRelatives(sculpted_group, children=True, type='transform') or []:
        posed_shape_name = sculpt_shape.replace('_SCULPT', '_POSE')

        if not cmds.objExists(posed_shape_name):
            logging.warning('Posed shape not found for sculpted shape {}. Skipping delta extraction.'.format(sculpt_shape))
            delta_map[sculpt_shape] = None
            continue

        delta_shape = extract_delta(geo, sculpt_shape, posed_shape_name)
        cmds.parent(delta_shape, delta_group)
        delta_shapes.append(delta_shape)
        delta_map[sculpt_shape] = delta_shape
        logging.info('Created delta shape: {}'.format(delta_shape))

    blendshape_name = 'body_blendshape'

    if not delta_shapes:
        logging.error('No delta shapes created. Cannot set up blendshape node.')
        return

    # Create blendShape node with all delta shapes as targets
    bs_node = cmds.blendShape(delta_shapes, geo, name=blendshape_name, frontOfChain=True, origin='world')[0]
    logging.info('Created blendshape node: {} with {} targets'.format(bs_node, len(delta_shapes)))

    # Read correctives data and connect to control attributes
    correctives_data = read_correctives_data()
    if not correctives_data:
        logging.error('Failed to read correctives data. Cannot connect blendshape weights.')
        return

    # Connect corrective shapes to control attributes
    for corrective_name, values in correctives_data.items():
        control_name = values.get('control')
        on_value = values.get('on_value')
        axis = values.get('axis')
        mirror = values.get('mirror')
        enable = values.get('enable')

        if not enable:
            logging.info('Corrective {} is not enabled. Skipping connection.'.format(corrective_name))
            continue

        # Determine corrective names to connect
        corrective_names_to_connect = []

        if mirror:
            # Handle mirrored correctives - create L and R versions
            if corrective_name.startswith('L_'):
                left_name = corrective_name.replace('_BS', '')
                right_name = corrective_name.replace('L_', 'R_', 1).replace('_BS', '')
            elif corrective_name.startswith('R_'):
                right_name = corrective_name.replace('_BS', '')
                left_name = corrective_name.replace('R_', 'L_', 1).replace('_BS', '')
            else:
                # If no side prefix, default to creating L_ and R_ variants
                left_name = 'L_{}'.format(corrective_name).replace('_BS', '')
                right_name = 'R_{}'.format(corrective_name).replace('_BS', '')

            # Connect L side
            left_control = control_name.replace('CTRL_R_', 'CTRL_L_')
            corrective_names_to_connect.append((left_name, left_control))

            # Connect R side
            right_control = control_name.replace('CTRL_L_', 'CTRL_R_')
            corrective_names_to_connect.append((right_name, right_control))
        else:
            # No mirror - C side corrective
            corr_name = corrective_name.replace('_BS', '')
            corrective_names_to_connect.append((corr_name, control_name))

        # Connect each corrective to its control
        trans_attr = 't{}'.format(axis)
        for corr_name, ctrl_name in corrective_names_to_connect:
            control_attr = '{}.{}'.format(ctrl_name, trans_attr)

            if not cmds.objExists(control_attr):
                logging.warning(
                    'Control attribute {} not found for corrective {}. Skipping connection.'.format(control_attr, corr_name))
                continue

            if on_value == -1:
                try:
                    mult_node = cmds.createNode('multiplyDivide', name='{}_invert'.format(ctrl_name.replace('CTRL_', '')))
                    cmds.setAttr('{}.input2X'.format(mult_node), -1)
                    cmds.connectAttr(control_attr, '{}.input1X'.format(mult_node), force=True)
                    cmds.connectAttr('{}.outputX'.format(mult_node), '{}.{}'.format(blendshape_name, corr_name), force=True)
                    logging.info(
                        'Connected {} to blendshape weight {} with multiply node due to negative on_value.'.format(control_attr, corr_name))
                except Exception as e:
                    logging.error(
                        'Failed to connect {} to blendshape weight {} with multiply node: {}'.format(control_attr, corr_name, e))
            else:
                try:
                    cmds.connectAttr(control_attr, '{}.{}'.format(blendshape_name, corr_name), force=True)
                    logging.info('Connected {} to blendshape weight {}'.format(control_attr, corr_name))
                except Exception as e:
                    logging.error('Failed to connect {} to blendshape weight {}: {}'.format(control_attr, corr_name, e))

    # Clean up
    if cmds.objExists('posed_grp') and cmds.objExists('sculpted_grp') and cmds.objExists('deltas_grp'):
        if not cmds.objExists('correctives_grp'):
            cleanup_grp = cmds.group(empty=True, name='correctives_grp')
            cmds.parent('posed_grp', cleanup_grp)
            cmds.parent('sculpted_grp', cleanup_grp)
            cmds.parent('deltas_grp', cleanup_grp)
            cmds.setAttr('{}.visibility'.format(cleanup_grp), 0)
            logging.info('Organized corrective groups under correctives_grp and hid them.')

    logging.info('Successfully set up corrective blendshapes.')


def main(geo=None, skip_export=False):
    '''
    Main function to run the full corrective workflow

    Args:
        geo (str): Name of the base geometry mesh (e.g., 'skin_C_body_0001_GEPS')
        skip_export (bool): If True, skips the export_correctives step (default: False)
    '''
    if not geo:
        logging.error('No geometry name provided. Please specify geo parameter.')
        return

    create_correctives(geo=geo)
    if not skip_export:
        export_correctives()
    import_correctives()
    setup_correctives(geo=geo)


if __name__ == '__main__':
    main()  # Replace 'geo' with the actual name of the base geometry mesh when running

