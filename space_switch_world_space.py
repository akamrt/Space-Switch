"""
Space Switch to World Space Tool for Maya
Converted from MEL to Python for Maya 2023
Original MEL written by Richard Lico - Copyright Animation Sherpa 2020

This script creates world-space locators from selected objects, bakes the animation,
and then constrains the original object back to the locator - effectively switching
the object to world space control.

Usage:
    Select object(s) and run the script. A dialog will ask what attributes 
    (Rotation, Translation, or Both) you want to control via the world space locator.
"""

import maya.cmds as cmds


def space_switch_to_world():
    """
    Main function to switch selected objects to world space control.
    Creates a world space locator for each selected object, bakes the animation,
    and constrains the original object to the locator.
    """
    # Get timeline range
    start_time = cmds.playbackOptions(query=True, minTime=True)
    end_time = cmds.playbackOptions(query=True, maxTime=True)
    
    # Get selection
    selection = cmds.ls(selection=True)
    
    if not selection:
        cmds.confirmDialog(
            title="Confirm",
            message="You need to select something first",
            button=["OK"],
            defaultButton="OK"
        )
        return
    
    # Process each selected object
    for item in selection:
        locator_name = "{}_temp_worldspace_locator".format(item)
        
        # Create a locator with the selected object's name appended
        cmds.spaceLocator(position=(0, 0, 0), name=locator_name)
        
        # Set size of locator
        cmds.setAttr("{}.localScaleX".format(locator_name), 18)
        cmds.setAttr("{}.localScaleY".format(locator_name), 18)
        cmds.setAttr("{}.localScaleZ".format(locator_name), 18)
        
        # Create constraints between selected object and new locator
        cmds.select(item)
        cmds.select(locator_name, add=True)
        cmds.pointConstraint()
        cmds.orientConstraint()
        
        # Select the locator and bake the animation
        cmds.select(locator_name)
        
        # Suspend refresh for performance during baking
        cmds.refresh(suspend=True)
        try:
            # Bake the animation
            cmds.bakeResults(
                simulation=True,
                time=(start_time, end_time),
                sampleBy=1,
                disableImplicitControl=True,
                preserveOutsideKeys=True,
                sparseAnimCurveBake=False,
                removeBakedAttributeFromLayer=False,
                removeBakedAnimFromLayer=False,
                bakeOnOverrideLayer=False,
                minimizeRotation=True,
                controlPoints=False
            )
            
            # Delete static channels
            cmds.delete(staticChannels=True)
            
            # Filter curves to reduce keys
            cmds.filterCurve()
            
            # Delete constraints from the locator
            delete_constraints(locator_name)
            
        finally:
            # Resume refresh
            cmds.refresh(suspend=False)
        
        # Ask the user what attributes they want to use
        response = cmds.confirmDialog(
            title="Confirm",
            message="What would you like to Control?",
            button=["Rotation", "Translation", "Both"],
            defaultButton="Both",
            cancelButton="Both",
            dismissString="Both"
        )
        
        # Apply the appropriate constraint based on user choice
        if response == "Rotation":
            cmds.select(locator_name)
            cmds.select(item, add=True)
            cmds.orientConstraint()
            
        elif response == "Translation":
            cmds.select(locator_name)
            cmds.select(item, add=True)
            cmds.pointConstraint()
            
        else:  # Both (default)
            cmds.select(locator_name)
            cmds.select(item, add=True)
            cmds.pointConstraint()
            cmds.orientConstraint()
        
        # Check to see if the rig_layer exists and add the locator to it
        cmds.select(locator_name)
        if cmds.objExists("rig_layer"):
            cmds.editDisplayLayerMembers("rig_layer", locator_name, noRecurse=True)


def delete_constraints(node):
    """
    Delete all constraints on a given node.
    
    Args:
        node: The node to delete constraints from
    """
    # Find all constraint types connected to the node
    constraint_types = [
        'pointConstraint',
        'orientConstraint',
        'scaleConstraint',
        'parentConstraint',
        'aimConstraint'
    ]
    
    for constraint_type in constraint_types:
        constraints = cmds.listRelatives(node, type=constraint_type)
        if constraints:
            cmds.delete(constraints)


# Run the script when executed
if __name__ == "__main__":
    space_switch_to_world()
