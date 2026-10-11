''''
Connect facial blendshapes to a MetaHuman face rig in Maya.

Identifies the MetaHuman face rig, head geometry, blendshape targets,
and corresponding face controls. Creates or reuses a blendShape
deformer and connects its weight attributes to the appropriate control
translations based on target naming conventions.

Resets eligible face control attributes to their default values and
sets the face GUI follow-head control after the connections are made.
Missing scene elements and unsupported target names are logged.
'''

# ****************************************************************
# content  = connect face blendshapes to MetaHuman face rig
# version  = 1.3.0
# date     = 2026-07-20
#
# how to   = run this script to connect face blend shapes to the rig
#
# author   = Garvey Chi (garveychi@gmail.com)
# ****************************************************************

import logging

from maya import cmds

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

head_geo = 'head_001_GEO'
head_blendshape = 'head_BLS'


# Check that the MetaHuman face rig exists in the scene
def check_metahuman_face_rig():
    '''
    Checks if the MetaHuman face rig exists in the Maya scene.

    Returns:
        bool: True if the MetaHuman face rig is found, False otherwise.
    '''
    face_rig = cmds.ls('headGui_grp', type='transform')
    if not face_rig:
        logging.error('MetaHuman face rig not found in the scene.')
        return False
    logging.info('MetaHuman face rig found: {}'.format(face_rig[0]))
    return True


def get_blendshape_nodes():
    '''
    Retrieves all blendshape nodes in the Maya scene and add to a list.

    Returns:
        list: A list of blendshape node names.
    '''
    return cmds.ls('MSH_*', type='transform') or []


def get_face_controls():
    '''
    Retrieves all list of all MetaHuman controls in the scene.

    Returns:
        list: A list of MetaHuman control names in the scene.
    '''
    excluded = {'CTRL_faceGUI', 'CTRL_faceTweakersGUI', 'CTRL_faceAndEyesAimFollowHeadGUI'}
    controls = cmds.ls('CTRL_*', type='transform') or []
    return [ctrl for ctrl in controls if ctrl not in excluded]


def set_face_controls_to_default():
    '''
    Sets all MetaHuman face controls to their default values.
    '''
    if not check_metahuman_face_rig():
        logging.error('Cannot set face controls to default values because the MetaHuman face rig is not found.')
        return
    else:
        logging.info('MetaHuman face rig found. Proceeding to set face controls to default values.')
        # Set face controls to default values
        logging.info('Setting face controls to default values...')
        for ctrl in get_face_controls():
            # Check to see that attributes are keyable before setting to default values
            for attr in ['translateX', 'translateY']:
                plug = '{}.{}'.format(ctrl, attr)
                if not cmds.attributeQuery(attr, node=ctrl, exists=True):
                    continue
                if not cmds.getAttr(plug, keyable=True):
                    continue
                if cmds.getAttr(plug, lock=True):
                    logging.info('Skipping locked attribute: {}'.format(plug))
                    continue
                if cmds.listConnections(plug, source=True, destination=False):
                    logging.info('Skipping connected attribute: {}'.format(plug))
                    continue
                cmds.setAttr(plug, 0)

        # Set the face GUI follow head control to 1
        follow_head_attr = 'CTRL_faceGUIfollowHead.translateX'
        if cmds.objExists(follow_head_attr):
            if cmds.getAttr(follow_head_attr, lock=True):
                logging.info('Skipping locked attribute: {}'.format(follow_head_attr))
            elif cmds.listConnections(follow_head_attr, source=True, destination=False):
                logging.info('Skipping connected attribute: {}'.format(follow_head_attr))
            else:
                cmds.setAttr(follow_head_attr, 1)
        else:
            logging.warning('Attribute not found: {}'.format(follow_head_attr))
    logging.info('Default values set for all MetaHuman face controls.')


def connect_blendshapes_to_metahuman(blendshape_nodes=None):
    '''
    Connects the provided blendshape nodes to the MetaHuman face rig.
    '''
    # Check if the MetaHuman face rig exists
    if not check_metahuman_face_rig():
        logging.error('MetaHuman face rig not found. Cannot connect blendshapes.')
        return

    logging.info('Connecting blendshape nodes to MetaHuman face rig...')

    if not cmds.objExists(head_geo):
        logging.error('Head geometry not found: {}'.format(head_geo))
        return

    target_blendshapes = blendshape_nodes if blendshape_nodes is not None else get_blendshape_nodes()
    if not target_blendshapes:
        logging.warning('No blendshape targets found for head geometry: {}'.format(head_geo))
        return

    # Create the blendshape deformer once if missing, otherwise reuse existing.
    if cmds.objExists(head_blendshape):
        blendshape_deformer = [head_blendshape]
        logging.info('Using existing blendshape deformer: {}'.format(head_blendshape))
    else:
        logging.info('No blendshape deformer found for {}. Creating new deformer...'.format(head_geo))
        cmds.select(clear=True)
        cmds.select(target_blendshapes)
        cmds.select(head_geo, add=True)
        blendshape_deformer = cmds.blendShape(name=head_blendshape, frontOfChain=True)
        logging.info('Blendshape deformer created: {}'.format(blendshape_deformer[0]))

    # Create connections between blendshape weight attributes and MetaHuman rig controls.
    logging.info('Connecting blendshape weight attributes to MetaHuman rig controls...')
    for target in target_blendshapes:
        parts = target.split('_')
        if len(parts) < 4:
            logging.warning('Skipping target with unsupported naming: {}'.format(target))
            continue

        axis_token = parts[-2].lower()
        suffix = parts[-1].lower()
        core = parts[1:-2]
        if not core:
            logging.warning('Skipping target with unsupported naming: {}'.format(target))
            continue

        axis_map = {'x': 'X', 'y': 'Y'}
        if axis_token not in axis_map:
            logging.warning('Skipping target with unsupported axis token "{}": {}'.format(axis_token, target))
            continue

        if suffix not in {'pos', 'neg'}:
            logging.warning('Skipping target with unsupported suffix "{}": {}'.format(suffix, target))
            continue

        face_ctrl = 'CTRL_{}'.format('_'.join(core))
        src_attr = '{}.translate{}'.format(face_ctrl, axis_map[axis_token])
        dst_attr = '{}.{}'.format(blendshape_deformer[0], target)

        if not cmds.objExists(face_ctrl):
            logging.warning('Control not found for target {}: {}'.format(target, face_ctrl))
            continue
        if not cmds.objExists(dst_attr):
            logging.warning('Blendshape weight attribute not found: {}'.format(dst_attr))
            continue

        if suffix == 'pos':
            # Clamp the positive range to 0-1 so negative control values do not bleed into this weight.
            clamp_name = '{}_{}_pos_CLM'.format(face_ctrl, axis_map[axis_token].lower())
            clamp_node = clamp_name if cmds.objExists(clamp_name) else cmds.shadingNode(
                'clamp', asUtility=True, name=clamp_name
            )
            cmds.setAttr('{}.minR'.format(clamp_node), 0)
            cmds.setAttr('{}.maxR'.format(clamp_node), 1)
            cmds.connectAttr(src_attr, '{}.inputR'.format(clamp_node), force=True)
            cmds.connectAttr('{}.outputR'.format(clamp_node), dst_attr, force=True)
        else:
            # Invert the control translation, then clamp 0-1 so positive control values do not bleed into this weight.
            multdiv_name = '{}_{}_invert_MLD'.format(face_ctrl, axis_map[axis_token].lower())
            multdiv_node = multdiv_name if cmds.objExists(multdiv_name) else cmds.shadingNode(
                'multiplyDivide', asUtility=True, name=multdiv_name
            )
            channel = axis_map[axis_token]
            cmds.setAttr('{}.input2{}'.format(multdiv_node, channel), -1)
            cmds.connectAttr(src_attr, '{}.input1{}'.format(multdiv_node, channel), force=True)

            clamp_name = '{}_{}_neg_CLM'.format(face_ctrl, axis_map[axis_token].lower())
            clamp_node = clamp_name if cmds.objExists(clamp_name) else cmds.shadingNode(
                'clamp', asUtility=True, name=clamp_name
            )
            cmds.setAttr('{}.minR'.format(clamp_node), 0)
            cmds.setAttr('{}.maxR'.format(clamp_node), 1)
            cmds.connectAttr('{}.output{}'.format(multdiv_node, channel), '{}.inputR'.format(clamp_node), force=True)
            cmds.connectAttr('{}.outputR'.format(clamp_node), dst_attr, force=True)

        logging.info('Connected blendshape node {} to control {}'.format(target, face_ctrl))


def main():
    '''
    Main entry point to run the blendshape connection process.
    '''
    logging.info('Starting blendshape connection process...')
    connect_blendshapes_to_metahuman()
    logging.info('Blendshape connection process completed.')
    

if __name__ == '__main__':
    main()
    set_face_controls_to_default()

