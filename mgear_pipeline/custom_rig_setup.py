'''
Custom rig setup for mGear character rigs.

Designed to run as an mGear Post Custom Step, after the guide template
build has generated the base rig. Adds rig customizations and connections
that are not handled by the standard mGear build process.

The setup includes:
- Add NPO groups, sub-controls, and gimbal controls.
- Reconnect spine IK controls through custom sub-controls.
- Set up control scale attributes and UI control constraints.
- Add IK arm and leg length adjustment attributes.
- Set up foot roll, splay, and arm twist controls.
- Adjust arm and leg roundness attribute limits.
- Create and integrate hip and shoulder hydraulic driver systems.
- Set joint labels for overlapping joints.

Uses mGear rig components and naming conventions, along with custom
Maya nodes, attributes, constraints, and connections to extend the
generated rig.

Logging is used throughout the setup to report operations and assist
with troubleshooting.
'''

# *********************************************************************
# content   = custom rig setup not handled in mGear's guide template
#             build is created here
# version   = 2.6.0
# date      = 2025-04-16
#
# how to    = run function as a mGear Post Custom Step
#
# author    = Garvey Chi (garveychi@gmail.com)
# *********************************************************************

import logging

from maya import cmds
from pymel import core as pm

from mgear import rigbits

from CreateVisAttrs import VisibilityAttributes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ********************************************************************
# CONSTANTS
JNT_LABELS = {
    'arm_{}0_0_jnt': 10,  # Shoulder
    'arm_{}0_5_jnt': 11,  # Elbow
    'arm_{}0_end_jnt': 12,  # Wrist
    'leg_{}0_0_jnt': 2,  # Hip
    'leg_{}0_4_jnt': 3,  # Knee
    'leg_{}0_end_jnt': 4,  # Ankle
    'metaIndex_{}0_0_jnt': 19,  # Index Finger
    'metaMiddle_{}0_0_jnt': 20,  # Middle Finger
    'metaPinky_{}0_0_jnt': 21,  # Pinky Finger
}

SIDE_LEFT = 1
SIDE_RIGHT = 2


# ********************************************************************
# FUNCTIONS
def set_joint_labels():
    '''
    Set mGear joint labels for overlapping joints.
    '''
    for side in ['L', 'R']:
        side_val = SIDE_LEFT if side == 'L' else SIDE_RIGHT
        for jnt_template, label_val in JNT_LABELS.items():
            jnt_name = jnt_template.format(side)
            if cmds.objExists(jnt_name):
                logging.info('Setting label for joint: {}'.format(jnt_name))
                cmds.setAttr('{}.type'.format(jnt_name), label_val)
                cmds.setAttr('{}.side'.format(jnt_name), side_val)
            else:
                logging.warning('Joint does not exist: {}'.format(jnt_name))


def unlock_and_lock_attrs(node, attrs, lock):
    '''
    Unlocks or locks specified attributes on a given node.

    Args:
        node (str): The name of the Maya node.
        attrs (list): A list of attribute names to unlock or lock
            (e.g., ['tx', 'ty', 'tz']).
        lock (bool): Whether to lock (True) or unlock (False) the attributes.
    '''
    for attr in attrs:
        cmds.setAttr('{}.{}'.format(node, attr), lock=lock)


def create_sub_control(con, sub_con_name):
    '''
    Creates a sub-control for a given control and replaces its shape.

    Args:
        con (str): The name of the parent control.
        sub_con_name (str): The desired name for the newly created sub-control.

    Warns:
        Issues a Maya warning if control creation or shape replacement fails.
    '''
    try:
        pm_con = pm.PyNode(con)
        pm.select(pm_con)
        rigbits.createCTL(type='square', child=True)

        all_children = pm_con.getChildren(type='transform')
        if not all_children:
            cmds.warning(
                'Failed to identify the newly created sub-control for {}'.format(con)
            )
            return

        new_sub_con = all_children[-1]
        new_sub_con.rename(sub_con_name)

        control_buffer_name = '{}_controlBuffer'.format(sub_con_name)
        if not cmds.objExists(control_buffer_name):
            cmds.warning(
                'Control buffer {} does not exist for {}'.format(
                    control_buffer_name, sub_con_name
                )
            )
            return

        control_buffer = pm.PyNode(control_buffer_name)
        if not control_buffer.getShapes():
            cmds.warning(
                'Control buffer {} has no shapes'.format(control_buffer)
            )
            return

        cmds.select(control_buffer.name(), new_sub_con.name())
        rigbits.replaceShape()

    except Exception as e:
        cmds.warning('Failed to create sub-control for {}: {}'.format(con, e))


def create_gimbal_control(con, gimbal_con_name, scale_factor=1.1):
    '''
    Creates a gimbal control for a given control and replaces its shape.

    Args:
        con (str): The name of the parent control.
        gimbal_con_name (str): The desired name for the newly created
            gimbal control.

    Warns:
        Issues a Maya warning if control creation or shape replacement fails.
    '''
    try:
        pm_con = pm.PyNode(con)
        pm.select(pm_con)
        rigbits.createCTL(type='circle', child=False)

        parent = pm_con.getParent()
        if not parent:
            cmds.warning(
                'Failed to identify the newly created gimbal-control for {}'.format(
                    con
                )
            )
            return

        new_gimbal_con = parent
        new_gimbal_con.rename(gimbal_con_name)

        # Copy Rotate Order from Control
        con_rotate_order = pm_con.rotateOrder.get()
        new_gimbal_con.rotateOrder.set(con_rotate_order)

        control_buffer_name = '{}_controlBuffer'.format(gimbal_con_name)
        if not cmds.objExists(control_buffer_name):
            cmds.warning(
                'Control buffer {} does not exist for {}! Create default shape'.format(
                    control_buffer_name, gimbal_con_name
                )
            )

            cmds.select(pm_con.name(), new_gimbal_con.name())
            rigbits.replaceShape()

            shapes = new_gimbal_con.getShapes(noIntermediate=True)
            crv_shape = shapes[0]

            cvs = crv_shape.cv[:]
            bbox = new_gimbal_con.getBoundingBox(space='world')
            center = (bbox.min() + bbox.max()) * 0.5

            # Scale CVs
            for cv in cvs:
                pos = cv.getPosition(space='world')
                offset = pos - center
                new_pos = center + offset * scale_factor
                cv.setPosition(new_pos, space='world')

        else:
            control_buffer = pm.PyNode(control_buffer_name)
            if not control_buffer.getShapes():
                cmds.warning(
                    'Control buffer {} has no shapes'.format(control_buffer)
                )
                return

            cmds.select(control_buffer.name(), new_gimbal_con.name())
            rigbits.replaceShape()

    except Exception as e:
        cmds.warning(
            'Failed to create gimbal-control for {}: {}'.format(con, e)
        )


def get_connected_attribute(source_attr, destination_attr_base):
    '''
    Dynamically retrieves the connected attribute for a given source attribute.

    Args:
        source_attr (str): The source attribute(e.g.,
            'spine_C0_ik1_ctl.worldMatrix[0]').
        destination_attr_base (str): The base name of the destination
            attribute (e.g., 'inputs').

    Returns:
        str or None: The full name of the connected destination attribute
            (e.g., 'mgear_curveCns32.inputs[3]'), or None if not found.
    '''
    connections = (
        cmds.listConnections(source_attr, plugs=True, destination=True) or []
    )
    for connection in connections:
        if destination_attr_base in connection:
            return connection
    return None


def create_instance_curve(curve_name, divider_attr_name, divider_name,
                          attributes=None):
    '''
    Creates a curve to be used as an instance and adds specified
    attributes to it.

    This function generates a NURBS curve with the given name, deletes
    its construction history, and adds custom attributes to its shape
    node. It is typically used to create a shared attribute setup for
    rig controls.

    Args:
        curve_name (str): The name of the curve to create.
        divider_attr_name (str): The name of the divider attribute to add.
        divider_name (str): The name of the divider.
        attributes (list): A list of attribute names
            (strings) to add to the curve's shape node.

    Returns:
        str: The name of the created curve.

    Raises:
        RuntimeError: If the curve creation or attribute addition fails.
    '''
    try:
        logging.info('Creating instance curve: {}'.format(curve_name))

        crv = cmds.circle(name=curve_name)
        cmds.delete(crv, constructionHistory=True)
        shape_name = '{}Shape'.format(crv[0])

        vis_attrs = VisibilityAttributes()
        vis_attrs.add_separator(shape_name, divider_attr_name, divider_name)
        logging.info('Added separator to shape: {}'.format(shape_name))

        for attr in attributes:
            cmds.addAttr(
                shape_name,
                longName=attr,
                attributeType='float',
                defaultValue=0,
            )
            cmds.setAttr('{}.{}'.format(shape_name, attr), keyable=True)
            logging.info(
                'Added attribute: {} to shape: {}'.format(attr, shape_name)
            )

        logging.info(
            'Successfully created instance curve: {}'.format(curve_name)
        )
        return crv[0]

    except Exception as e:
        logging.error(
            'Failed to create instance curve: {}. Error: {}'.format(
                curve_name, e
            )
        )
        raise RuntimeError(
            'Failed to create instance curve: {}'.format(curve_name)
        )


def add_instance_to_control(curve, controls=None):
    '''
    Adds an instance of a curve to a control in order to share attributes.

    Args:
        curve (str): The name of the curve to be instanced.
        controls (list): A list of control names to which the instance will be added.
    '''
    
    if controls is None:
        controls = []

    for ctl in controls:
        try:
            # Create an instance of the curve
            curve_instance = cmds.instance(
                curve, name='{}_instance'.format(ctl)
            )[0]

            # Parent the shape of the curve instance to the control
            curve_shape = cmds.listRelatives(
                curve_instance, shapes=True, fullPath=True
            )
            if not curve_shape:
                cmds.warning(
                    'No shape found for curve instance: {}'.format(
                        curve_instance
                    )
                )
                return

            cmds.parent(curve_shape[0], ctl, shape=True, relative=True)

            # Delete the curve instance transform node
            cmds.delete(curve_instance)

            logging.info(
                'Successfully added instance of {} to controls: {}'.format(curve, controls)
            )
        except Exception as e:
            cmds.warning(
                'Failed to add instance of {} to {}: {}'.format(curve, ctl, e)
            )


def setup_splay(appendage, side, in_node, out_node, instance_crv_shape, aux_in_node=None):
    '''
    Sets up the Splay attributes for a given limb and appendage.
    '''

    logging.info(
        'Setting up Splay attributes for nodes: {} and {}'.format(
            in_node, out_node
        )
    )

    # Use the provided instance_crv_shape argument
    required_nodes = [in_node, out_node, instance_crv_shape]
    missing_nodes = [n for n in required_nodes if not cmds.objExists(n)]
    if missing_nodes:
        logging.error(
            'Missing required nodes: {}. Aborting Splay setup for: {} {}'.format(
                missing_nodes, appendage, side
            )
        )
        return

    # Unlock attributes for Splay setup
    unlock_nodes = [in_node, out_node]
    if aux_in_node is not None:
        unlock_nodes.insert(0, aux_in_node)
    for node in unlock_nodes:
        try:
            cmds.setAttr('{}.ry'.format(node), keyable=True, lock=False)
            logging.info(
                'Unlocked rotateY attribute for node: {}'.format(node)
            )
        except Exception as e:
            logging.warning(
                'Failed to unlock attribute for {}: {}'.format(node, e)
            )

    # Create or reuse reverse node
    reverse_node_name = 'rev_{}SplayOut_{}0'.format(appendage, side)
    if not cmds.objExists(reverse_node_name):
        try:
            reverse_node = cmds.shadingNode(
                'reverse', asUtility=True, name=reverse_node_name
            )
            logging.info('Created reverse node: {}'.format(reverse_node))
        except Exception as e:
            logging.error(
                'Failed to create reverse node {}: {}'.format(
                    reverse_node_name, e
                )
            )
            return
    else:
        reverse_node = reverse_node_name
        logging.info('Using existing reverse node: {}'.format(reverse_node))

    # Connect attributes if not already connected
    try:
        splay_attr = '{}.{}Splay'.format(instance_crv_shape, appendage)
        in_node_attr = '{}.ry'.format(in_node)
        reverse_input = '{}.inputY'.format(reverse_node)
        reverse_output = '{}.outputY'.format(reverse_node)
        out_node_attr = '{}.ry'.format(out_node)

        # Connect Splay to aux_in_node if it exists
        if aux_in_node is not None:
            aux_in_node_attr = '{}.ry'.format(aux_in_node)
            if not cmds.isConnected(splay_attr, aux_in_node_attr):
                cmds.connectAttr(splay_attr, aux_in_node_attr, force=True)
                logging.info(
                    'Connected {} to {}'.format(splay_attr, aux_in_node_attr)
                )
            else:
                logging.info(
                    '{} already connected to {}'.format(
                        splay_attr, aux_in_node_attr
                    )
                )

        # Connect Splay to in_node
        if not cmds.isConnected(splay_attr, in_node_attr):
            cmds.connectAttr(splay_attr, in_node_attr, force=True)
            logging.info('Connected {} to {}'.format(splay_attr, in_node_attr))
        else:
            logging.info(
                '{} already connected to {}'.format(splay_attr, in_node_attr)
            )

        # Connect Splay to reverse input
        if not cmds.isConnected(splay_attr, reverse_input):
            cmds.connectAttr(splay_attr, reverse_input, force=True)
            logging.info(
                'Connected {} to {}'.format(splay_attr, reverse_input)
            )
        else:
            logging.info(
                '{} already connected to {}'.format(splay_attr, reverse_input)
            )

        # Connect reverse output to out_node
        if not cmds.isConnected(reverse_output, out_node_attr):
            cmds.connectAttr(reverse_output, out_node_attr, force=True)
            logging.info(
                'Connected {} to {}'.format(reverse_output, out_node_attr)
            )
        else:
            logging.info(
                '{} already connected to {}'.format(
                    reverse_output, out_node_attr
                )
            )

        logging.info(
            'Connected {} Splay attributes for side: {}'.format(
                appendage.capitalize(), side
            )
        )

    except Exception as e:
        logging.error(
            'Failed to connect {} Splay attributes for side {}: {}'.format(
                appendage.capitalize(), side, e
            )
        )

    logging.info(
        '{} Splay attribute setup completed successfully.'.format(
            appendage.capitalize()
        )
    )


def setup_ik_length_attr():
    '''
    Sets up IK arm/leg length attributes.
    '''
    logging.info('Setting up IK arm/leg length attributes...')
    vis_attrs = VisibilityAttributes()
    ik_controls = {
        'armUI_L0_ctl': 'mgear_ikfk2Bone1',
        'armUI_R0_ctl': 'mgear_ikfk2Bone2',
        'legUI_L0_ctl': 'mgear_ikfk2Bone3',
        'legUI_R0_ctl': 'mgear_ikfk2Bone4',
    }

    for ctl, mgear_node in ik_controls.items():
        part = ctl[:3]
        side = ctl[6:8]

        logging.info(
            'Processing control: {} with mGear node: {}'.format(
                ctl, mgear_node
            )
        )

        # Add separator
        try:
            vis_attrs.add_separator(
                ctl, 'lengthScale_lengthScale', 'LENGTH_SCALE'
            )
            logging.info('Added separator to {}'.format(ctl))
        except Exception as e:
            logging.warning('Failed to add separator to {}: {}'.format(ctl, e))
            continue

        # Add length attributes
        try:
            cmds.addAttr(
                ctl,
                longName='{}_lengthUpper'.format(part),
                niceName='Length Upper',
                attributeType='float',
                defaultValue=1,
            )
            cmds.addAttr(
                ctl,
                longName='{}_lengthLower'.format(part),
                niceName='Length Lower',
                attributeType='float',
                defaultValue=1,
            )
            cmds.setAttr('{}.{}_lengthUpper'.format(ctl, part), keyable=True)
            cmds.setAttr('{}.{}_lengthLower'.format(ctl, part), keyable=True)
            logging.info('Added length attributes to {}'.format(ctl))
        except Exception as e:
            logging.warning(
                'Failed to add length attributes to {}: {}'.format(ctl, e)
            )
            continue

        # Create and setup utility nodes
        try:
            mult_div_upr_node = cmds.shadingNode(
                'multiplyDivide',
                asUtility=True,
                name='{}LengthUpper_{}_multDiv'.format(part, side),
            )
            mult_div_lwr_node = cmds.shadingNode(
                'multiplyDivide',
                asUtility=True,
                name='{}LengthLower_{}_multDiv'.format(part, side),
            )
            logging.info(
                'Created utility nodes: {}, {}'.format(
                    mult_div_upr_node, mult_div_lwr_node
                )
            )

            length_upper_value = cmds.getAttr('{}.lengthA'.format(mgear_node))
            length_lower_value = cmds.getAttr('{}.lengthB'.format(mgear_node))
            cmds.setAttr(
                '{}.input2X'.format(mult_div_upr_node), length_upper_value
            )
            cmds.setAttr(
                '{}.input2X'.format(mult_div_lwr_node), length_lower_value
            )
            logging.info(
                'Set default length values for {}: Upper={}, Lower={}'.format(
                    ctl, length_upper_value, length_lower_value
                )
            )

            cmds.connectAttr(
                '{}.{}_lengthUpper'.format(ctl, part),
                '{}.input1X'.format(mult_div_upr_node),
                force=True,
            )
            cmds.connectAttr(
                '{}.outputX'.format(mult_div_upr_node),
                '{}.lengthA'.format(mgear_node),
                force=True,
            )
            cmds.connectAttr(
                '{}.{}_lengthLower'.format(ctl, part),
                '{}.input1X'.format(mult_div_lwr_node),
                force=True,
            )
            cmds.connectAttr(
                '{}.outputX'.format(mult_div_lwr_node),
                '{}.lengthB'.format(mgear_node),
                force=True,
            )
            logging.info('Connected length attributes for {}'.format(ctl))
        except Exception as e:
            logging.warning(
                'Failed to set up utility nodes for {}: {}'.format(ctl, e)
            )


def correct_arm_twist():
    '''
    Corrects the arm twist by creating and positioning start,
    mid, and end twist groups for each side.
    '''
    for side in ['L0', 'R0']:
        arm_root_path = cmds.listRelatives(
            'arm_{}_fk0_npo'.format(side), parent=True, fullPath=True
        )[0]

        host_control = 'armUI_{}_ctl'.format(side)

        # Create NPO group
        npo_start_twist = cmds.group(
            em=True, name='arm_{}_start_twist_npo'.format(side)
        )
        # Create Auto group
        auto_start_twist = cmds.group(
            em=True,
            name='arm_{}_start_twist_auto'.format(side),
            parent=npo_start_twist,
        )
        # Create Main group
        start_twist = cmds.group(
            em=True,
            name='arm_{}_start_twist'.format(side),
            parent=auto_start_twist,
        )

        # Create NPO group
        npo_mid_twist = cmds.group(
            em=True, name='arm_{}_mid_twist_npo'.format(side)
        )
        # Create Auto group
        auto_mid_twist = cmds.group(
            em=True,
            name='arm_{}_mid_twist_auto'.format(side),
            parent=npo_mid_twist,
        )
        # Create Main group
        mid_twist = cmds.group(
            em=True,
            name='arm_{}_mid_twist'.format(side),
            parent=auto_mid_twist,
        )

        # Create NPO group
        npo_end_twist = cmds.group(
            em=True, name='arm_{}_end_twist_npo'.format(side)
        )
        # Create Auto group
        auto_end_twist = cmds.group(
            em=True,
            name='arm_{}_end_twist_auto'.format(side),
            parent=npo_end_twist,
        )
        # Create Main group
        end_twist = cmds.group(
            em=True,
            name='arm_{}_end_twist'.format(side),
            parent=auto_end_twist,
        )

        # Match Positions
        cmds.matchTransform(
            [npo_start_twist, 'arm_{}_armRollRef0_jnt'.format(side)]
        )
        cmds.parent(npo_start_twist, 'arm_{}_armRollRef0_jnt'.format(side))

        cmds.matchTransform([npo_mid_twist, 'arm_{}_ctrn_loc'.format(side)])
        cmds.parent(npo_mid_twist, 'arm_{}_mid_cns'.format(side))

        cmds.matchTransform(
            [npo_end_twist, 'arm_{}_forearmRollRef0_jnt'.format(side)]
        )
        cmds.parent(npo_end_twist, 'arm_{}_aux_npo'.format(side))

        # Delete current IKHandles
        delete_list = [
            'arm_{}_armTwist'.format(side),
            'arm_{}_forearmTwist'.format(side),
        ]
        cmds.delete(delete_list)

        # Get Twist Chains
        upper_arm_chain = cmds.ls('arm_{}_armTwist*_jnt'.format(side))
        lower_arm_chain = cmds.ls('arm_{}_forearmTwist*_jnt'.format(side))

        # Upper Arm Twist IK
        handle, effector = cmds.ikHandle(
            n='arm_{}_armTwist'.format(side),
            solver='ikSplineSolver',
            ccv=False,
            startJoint=upper_arm_chain[0],
            endEffector=upper_arm_chain[-1],
            curve='arm_{}_armTwist_crv'.format(side),
            freezeJoints=False,
            simplifyCurve=False,
        )
        cmds.parent(handle, arm_root_path)
        cmds.setAttr('{}.visibility'.format(handle), 0)

        # Set ikHandle attributes
        cmds.setAttr('{}.dTwistControlEnable'.format(handle), True)
        cmds.setAttr('{}.dWorldUpType'.format(handle), 4)
        cmds.setAttr('{}.dWorldUpAxis'.format(handle), 3)
        cmds.setAttr('{}.dWorldUpVectorZ'.format(handle), 1)
        cmds.setAttr('{}.dWorldUpVectorY'.format(handle), 0)
        cmds.setAttr('{}.dWorldUpVectorEndZ'.format(handle), 1)
        cmds.setAttr('{}.dWorldUpVectorEndY'.format(handle), 0)

        # Connect Start and End Twist Transforms
        cmds.connectAttr(
            '{}.worldMatrix[0]'.format(start_twist),
            '{}.dWorldUpMatrix'.format(handle),
        )
        cmds.connectAttr(
            '{}.worldMatrix[0]'.format(mid_twist),
            '{}.dWorldUpMatrixEnd'.format(handle),
        )

        # Lower Arm Twist IK
        handle, effector = cmds.ikHandle(
            n='arm_{}_forearmTwist'.format(side),
            solver='ikSplineSolver',
            ccv=False,
            startJoint=lower_arm_chain[0],
            endEffector=lower_arm_chain[-1],
            curve='arm_{}_forearmTwist_crv'.format(side),
            freezeJoints=False,
            simplifyCurve=False,
        )
        cmds.parent(handle, arm_root_path)
        cmds.setAttr('{}.visibility'.format(handle), 0)

        # Set ikHandle attributes
        cmds.setAttr('{}.dTwistControlEnable'.format(handle), True)
        cmds.setAttr('{}.dWorldUpType'.format(handle), 4)
        cmds.setAttr('{}.dWorldUpAxis'.format(handle), 3)
        cmds.setAttr('{}.dWorldUpVectorZ'.format(handle), 1)
        cmds.setAttr('{}.dWorldUpVectorY'.format(handle), 0)
        cmds.setAttr('{}.dWorldUpVectorEndZ'.format(handle), 1)
        cmds.setAttr('{}.dWorldUpVectorEndY'.format(handle), 0)

        # Connect Start and End Twist Transforms
        cmds.connectAttr(
            '{}.worldMatrix[0]'.format(mid_twist),
            '{}.dWorldUpMatrix'.format(handle),
        )
        cmds.connectAttr(
            '{}.worldMatrix[0]'.format(end_twist),
            '{}.dWorldUpMatrixEnd'.format(handle),
        )

        # Add Attributes
        split_attr_name = 'twist_twist'
        full_name = '{}.{}'.format(host_control, split_attr_name)

        cmds.addAttr(
            host_control,
            longName=split_attr_name,
            niceName='__________',
            attributeType='enum',
            enumName='TWIST',
        )
        cmds.setAttr(full_name, keyable=True, lock=True, channelBox=True)

        cmds.addAttr(
            host_control,
            longName=auto_start_twist,
            niceName='Start Twist Auto',
            defaultValue=0.0,
            minValue=0.0,
            maxValue=1.0,
            keyable=True,
        )
        cmds.addAttr(
            host_control,
            longName=auto_mid_twist,
            niceName='Mid Twist Auto',
            defaultValue=0.0,
            minValue=0.0,
            maxValue=1.0,
            keyable=True,
        )
        cmds.addAttr(
            host_control,
            longName=auto_end_twist,
            niceName='End Twist Auto',
            defaultValue=0.7,
            minValue=0.0,
            maxValue=1.0,
            keyable=True,
        )

        if side == 'R0':
            negated_plug = _negated_plug(
                'arm_{}_armTangentA_ctl.rotateX'.format(side)
            )
            cmds.connectAttr(negated_plug, '{}.rotateX'.format(start_twist))

            cmds.connectAttr(
                'arm_{}_elbowTangent_ctl.rotateX'.format(side),
                '{}.rotateX'.format(mid_twist),
            )

            negated_plug = _negated_plug(
                'arm_{}_forearmTangentB_ctl.rotateX'.format(side)
            )
            cmds.connectAttr(negated_plug, '{}.rotateX'.format(end_twist))

        else:
            cmds.connectAttr(
                'arm_{}_armTangentA_ctl.rotateX'.format(side),
                '{}.rotateX'.format(start_twist),
            )
            cmds.connectAttr(
                'arm_{}_elbowTangent_ctl.rotateX'.format(side),
                '{}.rotateX'.format(mid_twist),
            )
            cmds.connectAttr(
                'arm_{}_forearmTangentB_ctl.rotateX'.format(side),
                '{}.rotateX'.format(end_twist),
            )

        cmds.setAttr(
            'arm_{}_armTangentA_ctl.rotateX'.format(side),
            lock=False,
            keyable=True,
            channelBox=False,
        )
        cmds.setAttr(
            'arm_{}_elbowTangent_ctl.rotateX'.format(side),
            lock=False,
            keyable=True,
            channelBox=False,
        )
        cmds.setAttr(
            'arm_{}_forearmTangentB_ctl.rotateX'.format(side),
            lock=False,
            keyable=True,
            channelBox=False,
        )

        arm_twist_driver = 'arm_{}_auxTwist1_jnt'.format(side)
        for twist in [auto_start_twist, auto_mid_twist, auto_end_twist]:
            mult_node = cmds.createNode('multDoubleLinear')
            cmds.connectAttr(
                '{}.rotateX'.format(arm_twist_driver),
                '{}.input1'.format(mult_node),
            )
            cmds.connectAttr(
                '{}.{}'.format(host_control, twist),
                '{}.input2'.format(mult_node),
            )

            if side == 'R0' and twist == auto_mid_twist:
                # Negate the output
                negated_plug = _negated_plug('{}.output'.format(mult_node))
                cmds.connectAttr(
                    negated_plug, '{}.rotateX'.format(twist), f=True
                )
            else:
                cmds.connectAttr(
                    '{}.output'.format(mult_node), '{}.rotateX'.format(twist)
                )


def _negated_plug(src_plug):
    '''Create a negate node and return its output plug.'''
    neg = cmds.createNode('multDoubleLinear')
    cmds.setAttr(neg + '.input2', -1)  # multiply by -1
    cmds.connectAttr(src_plug, neg + '.input1', f=True)
    return neg + '.output'


def setup_leg_translation_driver():
    '''
    Creates an additional driver system for the translation of the hip,
    similar to what the shoulder is doing.
    '''
    name_string = 'legTranslationDriverHydraulic'

    for side in ['L0', 'R0']:
        hip_hydraulics = [
            'hipDriverHydraulic_{}_0_jnt',
            'hipDriverHydraulic_{}_1_jnt',
        ]
        new_hydraulics = []
        for hip_hydraulic in hip_hydraulics:
            hip_hydraulic = hip_hydraulic.format(side)
            if cmds.objExists(hip_hydraulic):
                new_name = hip_hydraulic.replace(
                    'hipDriverHydraulic', name_string
                )
                duplicate = cmds.duplicate(
                    hip_hydraulic, parentOnly=True, name=new_name
                )[0]
                new_hydraulics.append(duplicate)

        cmds.parent(new_hydraulics[-1], new_hydraulics[0])
        cmds.parent(new_hydraulics[0], 'spine_C0_0_jnt')

        aim_target = 'leg_{}_5_jnt'.format(side)
        world_up_object = 'hipDriverHydraulic_{}_base_hook'.format(side)

        # Create new aim constraint
        cmds.aimConstraint(
            aim_target,
            new_hydraulics[0],
            aimVector=[0, 1, 0],
            maintainOffset=False,
            upVector=[1, 0, 0],
            worldUpObject=world_up_object,
            worldUpType=2,
            worldUpVector=[1, 0, 0],
        )


def custom_rig_setup():
    '''
    Executes the custom rig setup process for mGear rigs.

    This function handles tasks that are not covered by mGear's
    guide template build.

    The setup includes:
    - Add NPO (Null Parent Object) nodes to specified controls.
    - Create sub-controls for specified controls and replace their shapes.
    - Transfer connections from spine IK controls to sub-controls.
    - Set up scale attributes for spine IK controls.
    - Add constraints to UI controls for desired parent behaviour.
    - Set up IK arm/leg length attributes, including utility nodes for scaling.
    - Increase the max value of arm Roundness and leg Roundness attributes.
    - Create Hip Driver constraints.

    Logging is used throughout the process to provide detailed feedback
    on successes and failures.
    '''
    logging.info('Starting custom rig setup...')

    # ADD NPO
    logging.info('Adding NPO to controls...')

    controls = ['arm_L0_ik_ctl', 'arm_R0_ik_ctl']

    for control in controls:
        if cmds.objExists(control):
            try:
                pm_control = pm.PyNode(control)
                rigbits.addNPO([pm_control])
            except Exception as e:
                cmds.warning('Failed to add NPO for {}: {}'.format(control, e))
    logging.info('NPO added to controls successfully.')

    # ADD SUB CTLS
    logging.info('Adding Sub controls...')
    cons = {
        'spine_C0_ik0_ctl': 'spineSub_C0_ik0_ctl',
        'spine_C0_ik1_ctl': 'spineSub_C0_ik1_ctl',
        'body_C0_ctl': 'bodySub_C0_ctl',
        'arm_L0_ik_ctl': 'armSub_L0_ik_ctl',
        'arm_R0_ik_ctl': 'armSub_R0_ik_ctl',
        'leg_L0_ik_ctl': 'legSub_L0_ik_ctl',
        'leg_R0_ik_ctl': 'legSub_R0_ik_ctl',
    }
    for con, sub_con_name in cons.items():
        if cmds.objExists(con):
            create_sub_control(con, sub_con_name)

    # ADD GIMBAL CTLS
    logging.info('Adding Gimbal controls...')
    cons = {
        'arm_L0_fk0_ctl': 'arm_L0_fk0_gimbal_ctl',
        'arm_R0_fk0_ctl': 'arm_R0_fk0_gimbal_ctl',
    }
    for con, gimbal_con_name in cons.items():
        if cmds.objExists(con):
            create_gimbal_control(con, gimbal_con_name)

    # TRANSFER SPINE IK CTLS CONNECTIONS TO SUB CTLS
    node_attributes = {
        'spine_C0_ik1_ctl': [
            'decomposeMatrix2.inputMatrix',
            'decomposeMatrix21.inputMatrix',
            'mgear_intMatrix2.matrixB',
            'mgear_intMatrix3.matrixB',
            'mgear_intMatrix4.matrixB',
            'mgear_intMatrix5.matrixB',
            'mgear_intMatrix6.matrixB',
        ],
        'spine_C0_ik0_ctl': [
            'decomposeMatrix1.inputMatrix',
            'decomposeMatrix8.inputMatrix',
            'mgear_intMatrix2.matrixA',
            'mgear_intMatrix3.matrixA',
            'mgear_intMatrix4.matrixA',
            'mgear_intMatrix5.matrixA',
            'mgear_intMatrix6.matrixA',
        ],
    }
    for spine_control, node_attribute_list in node_attributes.items():
        for node_attr in node_attribute_list:
            # Validate that the source and destination attributes exist
            source_attr = '{}.worldMatrix[0]'.format(spine_control)
            destination_attr = node_attr

            if not cmds.objExists(spine_control):
                cmds.warning(
                    'Source node {} does not exist. Skipping.'.format(
                        spine_control
                    )
                )
                continue

            destination_node = destination_attr.split('.')[0]
            destination_attr_name = destination_attr.split('.')[-1]

            if not cmds.objExists(destination_node):
                cmds.warning(
                    'Destination node {} does not exist. Skipping.'.format(
                        destination_node
                    )
                )
                continue

            if not cmds.attributeQuery(
                destination_attr_name.split('[')[0],
                node=destination_node,
                exists=True,
            ):
                cmds.warning(
                    'Destination attribute {} does not exist on node {}. Skipping.'.format(
                        destination_attr_name, destination_node
                    )
                )
                continue

            try:
                cmds.disconnectAttr(source_attr, destination_attr)
                cmds.connectAttr(
                    'spineSub{}.worldMatrix[0]'.format(spine_control[5:]),
                    destination_attr,
                    force=True,
                )
                logging.info(
                    'Reconnected {} to {}.'.format(
                        source_attr, destination_attr
                    )
                )
            except Exception as e:
                cmds.warning(
                    'Failed to reconnect {} to {}: {}'.format(
                        source_attr, destination_attr, e
                    )
                )

    # Handle indexed attributes explicitly
    indexed_attributes = [
        ('spine_C0_ik1_ctl.worldMatrix[0]', 'inputs'),
        ('spine_C0_ik0_ctl.worldMatrix[0]', 'inputs'),
    ]

    for source_attr, destination_attr_base in indexed_attributes:
        # Dynamically find the connected destination attribute
        destination_attr = get_connected_attribute(
            source_attr, destination_attr_base
        )
        if not destination_attr:
            logging.warning(
                'No connected attribute found for {}. Skipping.'.format(
                    source_attr
                )
            )
            continue

        try:
            cmds.disconnectAttr(source_attr, destination_attr)
            cmds.connectAttr(
                source_attr.replace('spine_C0', 'spineSub_C0'),
                destination_attr,
                force=True,
            )
            logging.info(
                'Reconnected {} to {}.'.format(source_attr, destination_attr)
            )
        except Exception as e:
            cmds.warning(
                'Failed to reconnect {} to {}: {}'.format(
                    source_attr, destination_attr, e
                )
            )

    # TRANSFER BODY CTL-SPINE IK CTLS CONNECTIONS TO SUB CTLS
    if cmds.objExists('bodySub_C0_ctl'):
        try:
            for ik in ['ik0', 'ik1']:
                cmds.connectAttr(
                    'bodySub_C0_ctl.translate',
                    'spine_C0_{}_cns_parentConstraint1.target[0].targetTranslate'.format(
                        ik
                    ),
                    force=True,
                )
                cmds.connectAttr(
                    'bodySub_C0_ctl.rotate',
                    'spine_C0_{}_cns_parentConstraint1.target[0].targetRotate'.format(
                        ik
                    ),
                    force=True,
                )
                cmds.connectAttr(
                    'bodySub_C0_ctl.scale',
                    'spine_C0_{}_cns_parentConstraint1.target[0].targetScale'.format(
                        ik
                    ),
                    force=True,
                )
                cmds.connectAttr(
                    'bodySub_C0_ctl.parentMatrix[0]',
                    'spine_C0_{}_cns_parentConstraint1.target[0].targetParentMatrix'.format(
                        ik
                    ),
                    force=True,
                )
                cmds.connectAttr(
                    'bodySub_C0_ctl.rotatePivot',
                    'spine_C0_{}_cns_parentConstraint1.target[0].targetRotatePivot'.format(
                        ik
                    ),
                    force=True,
                )
                cmds.connectAttr(
                    'bodySub_C0_ctl.rotatePivotTranslate',
                    'spine_C0_{}_cns_parentConstraint1.target[0].targetRotateTranslate'.format(
                        ik
                    ),
                    force=True,
                )
                cmds.connectAttr(
                    'bodySub_C0_ctl.rotateOrder',
                    'spine_C0_{}_cns_parentConstraint1.target[0].targetRotateOrder'.format(
                        ik
                    ),
                    force=True,
                )
                logging.info(
                    'Connected bodySub_C0_ctl to spine_C0_{}_cns_parentConstraint1'.format(
                        ik
                    )
                )
        except Exception as e:
            cmds.warning(
                'Failed to connect bodySub_C0_ctl to spine_C0_ik{}: {}'.format(
                    ik, e
                )
            )
    else:
        logging.warning(
            'bodySub_C0_ctl does not exist. Skipping body control connections to spine IK controls.'
        )

    # SETUP SPINE IK CONTROLS SCALE ATTRIBUTES
    spine_controls = {
        'spine_C0_ik1_ctl': ['mgear_matrixConstraint5', 'spine_C0_4_jnt'],
        'spine_C0_ik0_ctl': ['mgear_matrixConstraint1', 'spine_C0_0_jnt'],
    }

    for spine_ctl, connection_nodes in spine_controls.items():
        multDiv_node = cmds.shadingNode(
            'multiplyDivide',
            asUtility=True,
            name='{}_multDiv'.format(
                spine_ctl[:-4].replace('spine_C0_ik', 'spineIk')
            ),
        )
        cmds.connectAttr(
            '{}.scale'.format(spine_ctl),
            '{}.input1'.format(multDiv_node),
            force=True,
        )
        cmds.connectAttr(
            '{}.scale'.format(connection_nodes[0]),
            '{}.input2'.format(multDiv_node),
            force=True,
        )
        cmds.connectAttr(
            '{}.output'.format(multDiv_node),
            '{}.scale'.format(connection_nodes[1]),
            force=True,
        )
        for scale_attr in ['sx', 'sy', 'sz']:
            cmds.setAttr(
                '{}.{}'.format(spine_ctl, scale_attr), keyable=True, lock=False
            )

    # ADD CONSTRAINTS
    logging.info('Adding constraints to UI controls...')

    parent_node = 'bodySub_C0_ctl'
    cns_nodes = [
        'vis_C0_ik_cns',
        'headUI_C0_ik_cns',
        'spineUI_C0_ik_cns',
        'tailUI_C0_ik_cns',
        'armUI_L0_ik_cns',
        'armUI_R0_ik_cns',
        'legUI_L0_ik_cns',
        'legUI_R0_ik_cns',
    ]
    for cns_node in cns_nodes:
        if cmds.objExists(cns_node):
            try:
                unlock_and_lock_attrs(cns_node, ['tx', 'ty', 'tz'], lock=False)
                cmds.pointConstraint(
                    parent_node, cns_node, maintainOffset=True
                )
                unlock_and_lock_attrs(cns_node, ['tx', 'ty', 'tz'], lock=True)
            except Exception as e:
                cmds.warning(
                    'Failed to constrain {} to {}: {}'.format(
                        cns_node, parent_node, e
                    )
                )

    # SETUP IK ARM/LEG LENGTH ATTRIBUTES
    logging.info('Setting up IK arm/leg length attributes...')
    setup_ik_length_attr()
    logging.info('IK arm/leg length attributes setup completed successfully.')

    # FOOT ROLL ATTR RE-LOCATION
    try:
        logging.info('Starting Foot Roll attribute setup...')

        controls = ['legUI_L0_ctl', 'legUI_R0_ctl']
        foot_roll_attrs = ['footRoll', 'footBank']
        vis_attrs = VisibilityAttributes()

        # Unlock foot roll ctls' vis attrs so they can be hidden in rig_clean_up script
        for side in ['L', 'R']:
            cmds.setAttr(
                'foot_{}0_roll_ctl.v'.format(side), keyable=True, lock=False
            )
            logging.info(
                'Unlocked visibility attribute for foot_{}0_roll_ctl'.format(
                    side
                )
            )

        for ctl in controls:
            if not cmds.objExists(ctl):
                logging.warning(
                    'Control {} does not exist. Skipping Foot Roll setup for this control.'.format(
                        ctl
                    )
                )
                continue

            logging.info(
                'Adding Foot Roll attributes to control: {}'.format(ctl)
            )
            try:
                vis_attrs.add_separator(
                    ctl, 'foot_roll_foot_roll', 'FOOT_ROLL'
                )
                logging.info('Added separator to control: {}'.format(ctl))
            except Exception as e:
                logging.warning(
                    'Failed to add separator to {}: {}'.format(ctl, e)
                )
                continue

            # Add Foot Roll attributes
            for attr in foot_roll_attrs:
                try:
                    cmds.addAttr(
                        ctl,
                        longName=attr,
                        attributeType='float',
                        defaultValue=0,
                    )
                    cmds.setAttr('{}.{}'.format(ctl, attr), keyable=True)
                    logging.info(
                        'Added attribute {} to control: {}'.format(attr, ctl)
                    )
                except Exception as e:
                    logging.warning(
                        'Failed to add attribute {} to {}: {}'.format(
                            attr, ctl, e
                        )
                    )
                    continue

            # Connect Foot Roll attributes
            try:
                side = ctl[
                    6:7
                ]  # Extract side ('L' or 'R') from the control name
                cmds.connectAttr(
                    '{}.footRoll'.format(ctl),
                    'foot_{}0_roll_ctl.rotateZ'.format(side),
                    force=True,
                )
                cmds.connectAttr(
                    '{}.footBank'.format(ctl),
                    'foot_{}0_roll_ctl.rotateX'.format(side),
                    force=True,
                )
                logging.info(
                    'Connected Foot Roll attributes for control: {}'.format(
                        ctl
                    )
                )
            except Exception as e:
                logging.warning(
                    'Failed to connect Foot Roll attributes for {}: {}'.format(
                        ctl, e
                    )
                )

        logging.info('Foot Roll attribute setup completed successfully.')

    except Exception as e:
        logging.error(
            'Failed to complete Foot Roll attribute setup. Error: {}'.format(e)
        )

    # SPLAY SETUP
    vis_attrs = VisibilityAttributes()
    splay = {
        'armUI_{}0_ctl': 'fingerSplay',
        'legUI_{}0_ctl': 'toeSplay',
    }
    for control_name_template, attribute in splay.items():
        for side in ['L', 'R']:
            control_name = control_name_template.format(side)
            if not cmds.objExists(control_name):
                logging.warning(
                    'Control {} does not exist. Skipping attribute setup.'.format(
                        control_name
                    )
                )
                continue
            try:
                vis_attrs.add_separator(control_name, 'splay_splay', 'SPLAY')
                logging.info(
                    'Added separator to control: {}'.format(control_name)
                )
            except Exception as e:
                logging.warning(
                    'Failed to add separator to {}: {}'.format(control_name, e)
                )
                continue

            # Add the attribute
            try:
                cmds.addAttr(
                    control_name,
                    longName=attribute,
                    attributeType='float',
                    defaultValue=0,
                )
                cmds.setAttr(
                    '{}.{}'.format(control_name, attribute), keyable=True
                )
                logging.info(
                    'Added attribute {} to control: {}'.format(
                        attribute, control_name
                    )
                )
            except Exception as e:
                logging.warning(
                    'Failed to add attribute {} to {}: {}'.format(
                        attribute, control_name, e
                    )
                )

    splay_data = {
        'leg_L': (
            'toe',
            'L',
            'toeIn_L0_fk0_npo',
            'toeOut_L0_fk0_npo',
            'legUI_L0_ctl',
            None,
        ),
        'leg_R': (
            'toe',
            'R',
            'toeIn_R0_fk0_npo',
            'toeOut_R0_fk0_npo',
            'legUI_R0_ctl',
            None,
        ),
        'arm_L': (
            'finger',
            'L',
            'index_L0_fk0_npo',
            'pinky_L0_fk0_npo',
            'armUI_L0_ctl',
            'thumb_L0_fk0_npo',
        ),
        'arm_R': (
            'finger',
            'R',
            'index_R0_fk0_npo',
            'pinky_R0_fk0_npo',
            'armUI_R0_ctl',
            'thumb_R0_fk0_npo',
        ),
    }

    for (
        appendage,
        side,
        in_node,
        out_node,
        instance_crv_shape,
        aux_in_node,
    ) in splay_data.values():
        setup_splay(
            appendage, side, in_node, out_node, instance_crv_shape, aux_in_node
        )

    # INCREASE ARM ROUNDNESS ATTRIBUTE MAX VALUE
    logging.info('Increasing arm and leg roundness attributes max value...')
    max_value = 2.0
    for section in ['arm', 'leg']:
        for side in ['L', 'R']:
            ctl_name = '{}UI_{}0_ctl'.format(section, side)
            if cmds.objExists('{}.{}_roundness'.format(ctl_name, section)):
                cmds.addAttr(
                    '{}.{}_roundness'.format(ctl_name, section),
                    edit=True,
                    max=max_value,
                )
                logging.info(
                    'Increased {} roundness attribute max value for {} successfully to {}.'.format(
                        section, ctl_name, max_value
                    )
                )
            else:
                logging.warning(
                    '{} does not exist for {}.'.format(ctl_name, section)
                )
    logging.info(
        'Increased arm and leg roundness attributes max value successfully.'
    )

    # HIP DRIVER SETUP
    logging.info('Creating hip driver constraints...')
    for side in ['L', 'R']:
        if cmds.objExists('hipDriverRoot_{}0_ctl'.format(side)):
            cmds.pointConstraint(
                'hip_{}0_0_jnt'.format(side),
                'hipDriverRoot_{}0_ctl'.format(side),
                mo=True,
            )
            logging.info(
                'Created point constraint for hipDriverRoot_{}0_ctl to hip_{}0_0_jnt.'.format(
                    side, side
                )
            )
        else:
            logging.warning(
                'hipDriverRoot_{}0_ctl does not exist. Skipping hip driver constraints creation.'.format(
                    side
                )
            )

    # SETUP UI CONSTRAINT TO JOINTS
    logging.info('Setting up UI constraints to joints...')

    ui_constraints = {
        'arm_L0_end_jnt': 'armUI_L0_ik_cns',
        'leg_L0_end_jnt': 'legUI_L0_ik_cns',
        'arm_R0_end_jnt': 'armUI_R0_ik_cns',
        'leg_R0_end_jnt': 'legUI_R0_ik_cns',
        'spine_C0_0_jnt': 'spineUI_C0_ik_cns',
        'tail_C0_5_jnt': 'tailUI_C0_ik_cns',
    }

    constraint_suffix = '_pointConstraint1'
    attrs_to_lock = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']

    def set_attrs_lock(node, attrs, lock, keyable):
        for attr in attrs:
            cmds.setAttr(
                '{}.{}'.format(node, attr), lock=lock, keyable=keyable
            )

    # Delete existing constraints dynamically
    for cns in ui_constraints.values():
        constraint_name = cns + constraint_suffix
        if cmds.objExists(constraint_name):
            cmds.delete(constraint_name)
            logging.info(
                'Deleted existing constraint: {}'.format(constraint_name)
            )

    for jnt, cns in ui_constraints.items():
        if not cmds.objExists(jnt):
            logging.warning(
                'Joint {} does not exist. Skipping constraint setup.'.format(
                    jnt
                )
            )
            continue
        if not cmds.objExists(cns):
            logging.warning(
                'Constraint node {} does not exist. Skipping constraint setup.'.format(
                    cns
                )
            )
            continue
        # Unlock attributes
        set_attrs_lock(cns, attrs_to_lock, lock=False, keyable=True)
        # Create new UI parent constraint
        cmds.parentConstraint(jnt, cns, mo=True)
        # Relock attributes
        set_attrs_lock(cns, attrs_to_lock, lock=True, keyable=False)
        logging.info('Set up parent constraint from {} to {}'.format(jnt, cns))

    logging.info('UI constraints to joints setup completed successfully.')

    # HYDRAULIC CONTROLS INTEGRATION (DELETE SHAPES AND RENAME)
    logging.info(
        'Renaming hydraulic controls, removing from control set and deleting shapes...'
    )
    control_names = [
        'hipDriverRoot_{}0_ctl',
        'hipDriverHydraulic_{}0_base_ctl',
        'hipDriverHydraulic_{}0_tip_ctl',
        'shoulderDriverHydraulic_{}0_base_ctl',
        'shoulderDriverHydraulic_{}0_tip_ctl',
    ]
    for side in ['L', 'R']:
        if cmds.objExists(
            'spine_C0_0_cnx|hipDriverRoot_{}0_root'.format(side)
        ):
            # Connect visibility attribute to rig node's jnt visibility
            cmds.connectAttr(
                'rig.jnt_vis',
                'spine_C0_0_cnx|hipDriverRoot_{}0_root.v'.format(side),
            )
            logging.info(
                'Connected hipDriverRoot_{}0_root vis attr to rig.jnt_vis.'.format(
                    side
                )
            )
        else:
            logging.warning(
                'spine_C0_0_cnx|hipDriverRoot_{}0_root does not exist. '
                'Skipping visibility connection for hipDriverRoot_{}0_root.'.format(
                    side, side
                )
            )
        for ctl_name in control_names:
            control = ctl_name.format(side)
            if cmds.objExists(control):
                # Remove from controller set
                cmds.sets(control, remove='rig_controllers_grp')
                # Delete Shape node
                shape = cmds.listRelatives(control, shapes=True)[0]
                cmds.delete(shape)
                # Rename ctl suffix
                new_name = control.replace('ctl', 'hook')
                cmds.rename(control, new_name)
                logging.info('Renamed {} to {}'.format(control, new_name))
            else:
                logging.warning(
                    'Control {} does not exist. Skipping.'.format(control)
                )

    # HIP TRANSLATION HYDRAULIC SETUP
    logging.info('Creating hip translation hydraulic setup...')
    setup_leg_translation_driver()
    logging.info('Hip translation hydraulic setup DONE...')

    # SET JOINT LABELS
    logging.info('Setting joint labels for overlapping joints')
    set_joint_labels()
    logging.info('Joint labels set for overlapping joints')

    # CORRECT ARM TWIST
    logging.info('Correcting arm twist setup...')
    try:
        correct_arm_twist()
        logging.info('Arm twist setup corrected successfully.')
    except Exception as e:
        logging.error('Failed to correct arm twist setup: {}'.format(e))

    logging.info('Custom rig setup completed successfully.')


def main():
    '''
    Main entry point for the custom rig setup.
    '''
    logging.info('Starting custom rig setup...')
    custom_rig_setup()
    logging.info('Finished custom rig setup.')


if __name__ == '__main__':
    main()
