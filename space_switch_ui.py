"""
Space Switch Dashboard for Maya 2023
=====================================
An animator-focused dashboard for space switching with anti-gimbal lock features.

USAGE:
    Copy and paste this entire script into Maya's Script Editor and run.
    The dashboard will appear as a dockable window.

THREE-STAGE WORKFLOW:
    1. CREATE  - Build locator hierarchy and position from current frame
    2. BAKE    - Bake animation to locators with cleanup
    3. REBUILD - Apply constraints back to original objects

Auto-reloads when re-run for fast iteration during development.
"""

# ============================================================================
# AUTO-RELOAD FOR FAST ITERATION
# ============================================================================
import sys

_MODULE_NAME = "space_switch_dashboard"
if _MODULE_NAME in sys.modules:
    del sys.modules[_MODULE_NAME]

# ============================================================================
# IMPORTS
# ============================================================================
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
import math
from functools import partial

# ============================================================================
# CONSTANTS
# ============================================================================
WINDOW_NAME = "spaceSwitchDashboard"
WINDOW_TITLE = "Space Switch Dashboard"
LOCATOR_SUFFIX = "_SS_loc"
OFFSET_SUFFIX = "_offset"
GIMBAL_SUFFIX = "_gimbal"

# Color palette for locators (Maya override colors)
LOCATOR_COLORS = {
    "red": 13,
    "yellow": 17,
    "green": 14,
    "blue": 6,
    "purple": 9,
    "white": 16,
    "cyan": 18,
    "orange": 21,
}

ROTATION_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]


# ============================================================================
# SPACE SWITCHER CORE LOGIC
# ============================================================================
class SpaceSwitcher:
    """Core logic for space switching operations."""
    
    def __init__(self):
        self.created_locators = []
        self.source_objects = []
        self.temp_constraints = []

    def get_best_rotation_order(self, source_obj, start_time, end_time):
        """
        Calculate the best rotation order to minimize gimbal lock.
        Analyzes the source object's world rotation over the time range.
        Middle axis approaching +/- 90 degrees is bad.
        """
        if not cmds.objExists(source_obj):
            return 0 # Default xyz

        # Valid orders in Maya which map to MTransformationMatrix constants
        # 0: kXYZ, 1: kYZX, 2: kZXY, 3: kXZY, 4: kYXZ, 5: kZYX
        # Middle axes corresponding to these orders:
        # 0 (xyz) -> Y (1)
        # 1 (yzx) -> Z (2)
        # 2 (zxy) -> X (0)
        # 3 (xzy) -> Z (2)
        # 4 (yxz) -> X (0)
        # 5 (zyx) -> Y (1)
        middle_axis_map = {0: 1, 1: 2, 2: 0, 3: 2, 4: 0, 5: 1}
        
        # Map Maya's attribute integers (0-5) to OpenMaya MTransformationMatrix constants
        # Note: In API 2.0, kXYZ is 1, not 0. 0 is kInvalid.
        om_order_map = {
            0: om.MTransformationMatrix.kXYZ,
            1: om.MTransformationMatrix.kYZX,
            2: om.MTransformationMatrix.kZXY,
            3: om.MTransformationMatrix.kXZY,
            4: om.MTransformationMatrix.kYXZ,
            5: om.MTransformationMatrix.kZYX
        }
        
        # Track the max deviation (score) for each order. 
        # Score = Max value of abs(middle_axis_angle). Lower is better (further from 90 deg/1.57 rad).
        scores = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        
        # Sample frames
        frames = range(int(start_time), int(end_time) + 1)
        
        print(f"Analyzing {len(frames)} frames for best rotation order on '{source_obj}'...")

        for t in frames:
            try:
                # Get World Matrix at frame t
                mat_list = cmds.getAttr(f"{source_obj}.worldMatrix[0]", time=t)
                mat = om.MMatrix(mat_list)
                
                for order_idx, middle_axis_idx in middle_axis_map.items():
                    # Create a transformation matrix from the world matrix
                    tm = om.MTransformationMatrix(mat)
                    
                    # Reorder to the target rotation order to see what the curves would look like
                    # use mapped constant, not the 0-5 index directly
                    tm.reorderRotation(om_order_map[order_idx])
                    
                    # Get the Euler rotation
                    euler = tm.rotation()
                    
                    # Check the value of the middle axis (radians)
                    mid_val = abs(euler[middle_axis_idx])
                    
                    # We want to minimize the worst-case (highest) value of the middle axis
                    # closer to 0 is better. closer to PI/2 (1.57) is bad.
                    if mid_val > scores[order_idx]:
                        scores[order_idx] = mid_val
                        
            except Exception as e:
                print(f"Error analyzing frame {t}: {e}")
                continue

        # Find order with lowest max deviation
        best_order = min(scores, key=scores.get)
        
        # Debug Output
        print("Rotation Order Scores (Lower max deviation is better):")
        for order_idx, score in scores.items():
            mark = " [BEST]" if order_idx == best_order else ""
            print(f"  {ROTATION_ORDERS[order_idx].upper()}: Max Middle Axis = {math.degrees(score):.2f} deg{mark}")
            
        print(f"Selected Best Order: {ROTATION_ORDERS[best_order].upper()}")
        return best_order

    
    def create_locator_hierarchy(self, source_obj, target_obj=None, mode="world", 
                                  num_offsets=2, locator_size=18, 
                                  color_index=17, rotation_order=0):
        """
        Create locator hierarchy with Master Space node.
        Hierarchy: Master(Space) -> Top_Offset(Baked) -> [Gimbal] -> Locator(Control)
        """
        if not source_obj:
            return None, None, None
            
        base_name = source_obj.replace(":", "_").replace("|", "_")
        
        # 1. Create MASTER Group (The Space Node)
        master_name = f"{base_name}_Master_Space"
        master_grp = cmds.group(empty=True, name=master_name)
        cmds.setAttr(f"{master_grp}.rotateOrder", rotation_order)
        
        # Setup Master Space transform/constraints
        if mode == "world":
            # World space: Master stays at origin (Identity)
            pass 
        elif mode == "local":
             # Local space: Match Source Initial
             cmds.matchTransform(master_grp, source_obj, position=True, rotation=True)
             
        elif mode in ["object", "camera", "aim"]:
            # These modes REQUIRE a target
            if not target_obj or not cmds.objExists(target_obj):
                cmds.warning(f"Create Hierarchy: Target '{target_obj}' invalid for mode '{mode}'. Master staying at origin.")
            else:
                # Match Target Pivot first
                cmds.matchTransform(master_grp, target_obj, position=True, rotation=True)
                
                # Apply Space Constraints
                if mode == "object":
                    # STRICT SNAP to target (False) ensuring we adopt its space exactly
                    cmds.parentConstraint(target_obj, master_grp, maintainOffset=False)
                elif mode == "camera":
                    cmds.parentConstraint(target_obj, master_grp, maintainOffset=False)
                elif mode == "aim":
                    # Aim Space: Master positioned at Target, Aiming at Source.
                    # Static setup: Constraints are applied and then deleted immediately so Master is static.
                    cmds.matchTransform(master_grp, target_obj, position=True)
                    
                    # Aim at Source (X-axis)
                    ac = cmds.aimConstraint(source_obj, master_grp, maintainOffset=False, 
                                       aimVector=(1,0,0), upVector=(0,1,0), worldUpType="scene")
                    cmds.delete(ac)

        # 2. Create Locator Chain (Child of Master)
        # Create the main control locator (bottom of chain)
        locator_name = base_name + LOCATOR_SUFFIX
        locator = cmds.spaceLocator(name=locator_name)[0]
        
        # Set locator visuals
        cmds.setAttr(f"{locator}.localScaleX", locator_size)
        cmds.setAttr(f"{locator}.localScaleY", locator_size)
        cmds.setAttr(f"{locator}.localScaleZ", locator_size)
        locator_shape = cmds.listRelatives(locator, shapes=True)[0]
        cmds.setAttr(f"{locator_shape}.overrideEnabled", 1)
        cmds.setAttr(f"{locator_shape}.overrideColor", color_index)
        cmds.setAttr(f"{locator}.rotateOrder", rotation_order)
        # Expose rotateOrder in Channel Box
        cmds.setAttr(f"{locator}.rotateOrder", k=True)
        
        # Build offset hierarchy strictly above locator
        current_child = locator
        top_offset = locator
        
        for i in range(num_offsets):
            offset_name = f"{base_name}{OFFSET_SUFFIX}_{i+1}"
            if i == 0:
                offset_name = f"{base_name}{GIMBAL_SUFFIX}"
            
            is_top_offset = (i == num_offsets - 1)
            
            if is_top_offset:
                # The top offset holds the baked animation
                offset_grp = cmds.spaceLocator(name=offset_name)[0]
                # Expose rotateOrder in Channel Box
                cmds.setAttr(f"{offset_grp}.rotateOrder", k=True)
                
                # Visuals for baked locator
                top_size = locator_size * 1.2
                cmds.setAttr(f"{offset_grp}.localScaleX", top_size)
                cmds.setAttr(f"{offset_grp}.localScaleY", top_size)
                cmds.setAttr(f"{offset_grp}.localScaleZ", top_size)
                shape = cmds.listRelatives(offset_grp, shapes=True)[0]
                cmds.setAttr(f"{shape}.overrideEnabled", 1)
                cmds.setAttr(f"{shape}.overrideColor", color_index)
            else:
                offset_grp = cmds.group(empty=True, name=offset_name)
            
            cmds.setAttr(f"{offset_grp}.rotateOrder", rotation_order)
            
            cmds.parent(current_child, offset_grp)
            current_child = offset_grp
            top_offset = offset_grp
            
        # 3. Parent Chain to Master
        # Match chain to source object current position BEFORE parenting
        cmds.matchTransform(top_offset, source_obj, position=True, rotation=True)
        cmds.parent(top_offset, master_grp)
        
        # Store reference
        self.created_locators.append({
            "source": source_obj,
            "locator": locator,
            "top_group": top_offset, # The one defined as baked target
            "master": master_grp,
            "hierarchy": self._get_hierarchy(master_grp)
        })
        
        return top_offset, locator, master_grp
    
    def _get_hierarchy(self, top_node):
        """Get all nodes in the hierarchy."""
        hierarchy = [top_node]
        children = cmds.listRelatives(top_node, allDescendents=True, type="transform") or []
        hierarchy.extend(children)
        return hierarchy
    
    def create_temp_constraints(self, source_obj, target_node, translate=True, rotate=True):
        """
        Create temporary constraints from source to target for baking.
        
        Args:
            source_obj: The source object to follow
            target_node: The node to constrain (should be top_group for proper hierarchy)
            translate: Apply point constraint
            rotate: Apply orient constraint
        """
        constraints = []
        
        if translate:
            pc = cmds.pointConstraint(source_obj, target_node, maintainOffset=False)[0]
            constraints.append(pc)
        
        if rotate:
            oc = cmds.orientConstraint(source_obj, target_node, maintainOffset=False)[0]
            constraints.append(oc)
        
        self.temp_constraints.extend(constraints)
        return constraints
    
    def create_aim_constraint(self, source_obj, target_node, aim_target_obj):
        """
        Create aim constraint for object space aiming.
        
        Args:
            source_obj: The source object (for reference)
            target_node: The node to constrain (should be top_group)
            aim_target_obj: The object to aim at
        """
        ac = cmds.aimConstraint(
            aim_target_obj, target_node,
            maintainOffset=False,
            aimVector=(0, 0, 1),
            upVector=(0, 1, 0),
            worldUpType="vector",
            worldUpVector=(0, 1, 0)
        )[0]
        self.temp_constraints.append(ac)
        return ac
    
    def bake_animation(self, locators, sample_by=1, euler_filter=True, cleanup_constraints=True):
        """
        Bake animation to locators.
        
        Args:
            locators: List of locator names to bake
            sample_by: Sample rate for baking
            euler_filter: Apply Euler filter after baking
            cleanup_constraints: Whether to delete temporary constraints
        """
        if not locators:
            return
        
        start_time = cmds.playbackOptions(query=True, minTime=True)
        end_time = cmds.playbackOptions(query=True, maxTime=True)
        
        cmds.refresh(suspend=True)
        try:
            cmds.bakeResults(
                locators,
                simulation=True,
                time=(start_time, end_time),
                sampleBy=sample_by,
                disableImplicitControl=True,
                preserveOutsideKeys=True,
                sparseAnimCurveBake=True,
                removeBakedAttributeFromLayer=False,
                removeBakedAnimFromLayer=False,
                bakeOnOverrideLayer=False,
                minimizeRotation=True,
                controlPoints=False
            )
            
            # Delete temporary constraints
            if cleanup_constraints:
                for constraint in self.temp_constraints:
                    if cmds.objExists(constraint):
                        cmds.delete(constraint)
                self.temp_constraints = []
            
            # Ensure rotateOrder has no keys (it should be static)
            for loc in locators:
                if cmds.objExists(loc):
                    # Store the correct rotation order value
                    ro_val = cmds.getAttr(f"{loc}.rotateOrder")
                    # Remove any keys that might have been baked
                    cmds.cutKey(loc, attribute="rotateOrder", clear=True)
                    # Explicitly restore the value to ensure it doesn't revert to default
                    cmds.setAttr(f"{loc}.rotateOrder", ro_val)

            # Apply Euler filter
            if euler_filter:
                cmds.select(locators)
                cmds.filterCurve()
            
        finally:
            cmds.refresh(suspend=False)
    
    def cleanup_keys(self, locators, threshold=0.001):
        """
        Clean up animation curves:
        1. Remove redundant keys (linearize holds).
        2. Remove fully static channels.
        
        Args:
            locators: List of locator names
            threshold: Tolerance for considering values as static/equal
        """
        attrs = ["translateX", "translateY", "translateZ",
                 "rotateX", "rotateY", "rotateZ",
                 "scaleX", "scaleY", "scaleZ", "visibility"]
        
        for loc in locators:
            if not cmds.objExists(loc):
                continue
                
            for attr in attrs:
                attr_path = f"{loc}.{attr}"
                
                # Get animation curve
                anim_curve_list = cmds.listConnections(attr_path, type="animCurve")
                if not anim_curve_list:
                    continue
                
                anim_curve = anim_curve_list[0]
                
                # 1. Remove redundancy (optimize curve)
                self.remove_redundant_keys(anim_curve, threshold)
                
                # 2. Check if remaining curve is static
                # Get all keyframe values
                keyframes = cmds.keyframe(anim_curve, query=True, valueChange=True)
                if not keyframes:
                    continue
                
                # Check if all values are essentially the same
                min_val = min(keyframes)
                max_val = max(keyframes)
                
                if (max_val - min_val) <= threshold:
                    # Delete the animation curve (static channel)
                    cmds.delete(anim_curve)

    def remove_redundant_keys(self, anim_curve, threshold=0.001):
        """
        Remove keys that have the same value as their neighbors.
        """
        times = cmds.keyframe(anim_curve, query=True, timeChange=True)
        values = cmds.keyframe(anim_curve, query=True, valueChange=True)
        
        if not times or len(times) < 3:
            return
            
        count = len(times)
        to_delete = []
        
        # Iterate from index 1 to count-2
        for i in range(1, count - 1):
            prev_val = values[i-1]
            curr_val = values[i]
            next_val = values[i+1]
            
            # Check if current roughly equals prev AND next
            if (abs(curr_val - prev_val) <= threshold) and \
               (abs(curr_val - next_val) <= threshold):
                to_delete.append(times[i])
        
        if to_delete:
            cmds.cutKey(anim_curve, time=[(t,t) for t in to_delete])
    
    def rebuild_constraints(self, translate=True, rotate=True, maintain_offset=False):
        """
        Rebuild constraints from locators to source objects.
        
        Args:
            translate: Apply point constraint
            rotate: Apply orient constraint
            maintain_offset: Maintain offset in constraints
        """
        for loc_data in self.created_locators:
            source = loc_data["source"]
            locator = loc_data["locator"]
            
            if not cmds.objExists(source) or not cmds.objExists(locator):
                continue
            
            if translate:
                cmds.pointConstraint(locator, source, maintainOffset=maintain_offset)
            
            if rotate:
                cmds.orientConstraint(locator, source, maintainOffset=maintain_offset)
    
    def cleanup(self, delete_constraints_first=True):
        """
        Clean up locators and constraints.
        Deletes constraints FIRST to prevent objects popping back.
        """
        for loc_data in self.created_locators:
            source = loc_data["source"]
            top_group = loc_data["top_group"]
            master_grp = loc_data.get("master") # Get the master group
            
            if delete_constraints_first and cmds.objExists(source):
                # Delete constraints on source object first
                self._delete_constraints_on_node(source)
            
            # Then delete the locator hierarchy
            # If we delete the master group, everything below it (top_group, locators) goes too.
            if master_grp and cmds.objExists(master_grp):
                cmds.delete(master_grp)
            elif cmds.objExists(top_group):
                # Fallback if master not found for some reason
                cmds.delete(top_group)
        
        self.created_locators = []
    
    def _delete_constraints_on_node(self, node):
        """Delete all constraints on a given node."""
        constraint_types = [
            "pointConstraint", "orientConstraint", "scaleConstraint",
            "parentConstraint", "aimConstraint"
        ]
        
        for ctype in constraint_types:
            constraints = cmds.listRelatives(node, type=ctype) or []
            for c in constraints:
                if cmds.objExists(c):
                    cmds.delete(c)


# ============================================================================
# DASHBOARD UI
# ============================================================================
class SpaceSwitchDashboard:
    """Dockable dashboard UI for space switching."""
    
    def __init__(self):
        self.switcher = SpaceSwitcher()
        self.preview_locator = None
        self.target_object = None
        self.settings = {
            "space_mode": "world",
            "translate": True,
            "rotate": True,
            "aim_at_target": False,
            "rotation_order": 0,
            "locator_size": 18,
            "bake_master_space": False,
            "num_offsets": 2,
            "color_index": 17,
            "sample_by": 1,
            "euler_filter": True,
            "clean_static": True,
            "static_threshold": 0.001,
            "auto_best_order": True,
        }
        
        self.build_ui()
    
    def build_ui(self):
        """Build the dashboard UI."""
        # Delete existing window if it exists
        if cmds.window(WINDOW_NAME, exists=True):
            cmds.deleteUI(WINDOW_NAME)
        
        # Delete preview locator if exists
        if cmds.objExists("_SS_preview_locator"):
            cmds.delete("_SS_preview_locator")
        
        # Create window
        self.window = cmds.window(
            WINDOW_NAME,
            title=WINDOW_TITLE,
            widthHeight=(320, 520),
            sizeable=True
        )
        
        # Main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # ===== SPACE MODE =====
        cmds.frameLayout(label="Space Mode", collapsable=True, marginWidth=5, marginHeight=5)
        cmds.columnLayout(adjustableColumn=True)
        
        # Custom Radio Collection to support 5 modes (Grp limits to 4)
        self.mode_collection = cmds.radioCollection()
        
        # Row 1
        cmds.rowLayout(numberOfColumns=3)
        self.rb_world = cmds.radioButton(label="World", select=True, 
                                       onCommand=partial(self._on_space_mode_change, "world"))
        self.rb_local = cmds.radioButton(label="Local", 
                                       onCommand=partial(self._on_space_mode_change, "local"))
        self.rb_object = cmds.radioButton(label="Object", 
                                        onCommand=partial(self._on_space_mode_change, "object"))
        cmds.setParent("..")
        
        # Row 2
        cmds.rowLayout(numberOfColumns=2)
        self.rb_camera = cmds.radioButton(label="Camera", 
                                        onCommand=partial(self._on_space_mode_change, "camera"))
        self.rb_aim = cmds.radioButton(label="Aim", 
                                     onCommand=partial(self._on_space_mode_change, "aim"))
        cmds.setParent("..")
        
        
        # Source Field
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)
        cmds.text(label="Source: ", width=50)
        self.source_field = cmds.textField(editable=False, width=180)
        cmds.button(label="Pick", width=50, command=partial(self._pick_object, "source"))
        cmds.setParent("..")

        # Auto-populate Source from selection on load
        sel = cmds.ls(selection=True)
        if sel:
            cmds.textField(self.source_field, edit=True, text=sel[0])

        # Target Field
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)
        cmds.text(label="Target: ", width=50)
        self.target_field = cmds.textField(editable=True, width=180) # Always enabled
        self.target_pick_btn = cmds.button(label="Pick", width=50, command=partial(self._pick_object, "target"))
        cmds.setParent("..")
        
        cmds.setParent("..")
        cmds.setParent("..")
        
        # ===== ATTRIBUTES =====
        cmds.frameLayout(label="Attributes", collapsable=True, marginWidth=5, marginHeight=5)
        cmds.columnLayout(adjustableColumn=True)
        
        cmds.rowLayout(numberOfColumns=2)
        cmds.checkBox(
            label="Translation", value=True,
            changeCommand=lambda x: self._update_setting("translate", x)
        )
        cmds.checkBox(
            label="Rotation", value=True,
            changeCommand=lambda x: self._update_setting("rotate", x)
        )
        cmds.setParent("..")
        
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=3)
        cmds.text(label="Rotation Order: ")
        self.rot_order_menu = cmds.optionMenu(
            changeCommand=self._on_rotation_order_change
        )
        for ro in ROTATION_ORDERS:
            cmds.menuItem(label=ro.upper())
        
        cmds.checkBox(
            label="Auto-Detect", 
            value=True,
            annotation="Automatically calculate best rotation order to avoid gimbal lock.",
            changeCommand=lambda x: self._update_setting("auto_best_order", x)
        )
        cmds.setParent("..")
        
        cmds.setParent("..")
        cmds.setParent("..")
        
        # ===== LOCATOR SETTINGS =====
        cmds.frameLayout(label="Locator Settings", collapsable=True, marginWidth=5, marginHeight=5)
        cmds.columnLayout(adjustableColumn=True)
        
        cmds.button(
            label="Create Preview Locator",
            command=self._create_preview_locator,
            backgroundColor=(0.3, 0.5, 0.3)
        )
        
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=3)
        cmds.text(label="Scale: ", width=50)
        cmds.button(
            label="-", width=40,
            command=partial(self._adj_scale, -0.1)
        )
        cmds.button(
            label="+", width=40,
            command=partial(self._adj_scale, 0.1)
        )
        cmds.setParent("..")
        
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
        cmds.text(label="Offsets: ", width=50)
        self.offset_slider = cmds.intSliderGrp(
            field=True,
            minValue=1, maxValue=5, value=2,
            changeCommand=lambda x: self._update_setting("num_offsets", int(x))
        )
        cmds.setParent("..")
        
        # Color buttons
        cmds.text(label="Color:", align="left")
        cmds.rowLayout(numberOfColumns=8, columnWidth=[(i+1, 35) for i in range(8)])
        
        color_buttons = [
            ("red", (0.8, 0.2, 0.2)),
            ("yellow", (0.9, 0.9, 0.2)),
            ("green", (0.2, 0.8, 0.2)),
            ("blue", (0.2, 0.4, 0.9)),
            ("purple", (0.6, 0.2, 0.8)),
            ("white", (0.9, 0.9, 0.9)),
            ("cyan", (0.2, 0.8, 0.8)),
            ("orange", (0.9, 0.5, 0.1)),
        ]
        
        for color_name, rgb in color_buttons:
            cmds.button(
                label="",
                width=32, height=25,
                backgroundColor=rgb,
                command=partial(self._on_color_select, color_name)
            )
        
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.setParent("..")
        
        # ===== BAKE OPTIONS =====
        cmds.frameLayout(label="Bake Options", collapsable=True, marginWidth=5, marginHeight=5)
        cmds.columnLayout(adjustableColumn=True)
        
        cmds.rowLayout(numberOfColumns=3)
        cmds.text(label="Sample By: ")
        cmds.optionMenu(changeCommand=lambda x: self._update_setting("sample_by", int(x)))
        cmds.menuItem(label="1")
        cmds.menuItem(label="2")
        cmds.menuItem(label="5")
        cmds.menuItem(label="10")
        cmds.checkBox(
            label="Euler Filter", value=True,
            changeCommand=lambda x: self._update_setting("euler_filter", x)
        )
        cmds.setParent("..")
        
        cmds.rowLayout(numberOfColumns=3)
        cmds.checkBox(
            label="Clean Static Keys", value=True,
            changeCommand=lambda x: self._update_setting("clean_static", x)
        )
        cmds.text(label=" Threshold: ")
        cmds.floatField(
            value=0.001, precision=4, width=60,
            changeCommand=lambda x: self._update_setting("static_threshold", x)
        )
        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=2)
        cmds.checkBox(
            label="Bake Master Space", 
            value=False,
            annotation="Bakes the Master Group and deletes its constraints before baking locators.",
            changeCommand=lambda x: self._update_setting("bake_master_space", x)
        )
        cmds.setParent("..")
        
        cmds.setParent("..")
        cmds.setParent("..")
        
        # ===== STAGE BUTTONS =====
        cmds.frameLayout(label="Workflow Stages", collapsable=False, marginWidth=5, marginHeight=5)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        cmds.button(
            label="STAGE 1: Create Setup",
            height=35,
            backgroundColor=(0.3, 0.4, 0.5),
            command=self._stage_create
        )
        cmds.button(
            label="STAGE 2: Bake to Locators",
            height=35,
            backgroundColor=(0.4, 0.5, 0.3),
            command=self._stage_bake
        )
        cmds.button(
            label="STAGE 3: Rebuild Constraints",
            height=35,
            backgroundColor=(0.5, 0.4, 0.3),
            command=self._stage_rebuild
        )
        
        cmds.separator(height=10, style="none")
        cmds.button(
            label="RUN FULL SPACE SWITCH",
            height=50,
            backgroundColor=(0.2, 0.6, 0.3),
            command=self._stage_run_all,
            annotation="Run all 3 stages in sequence"
        )
        
        cmds.setParent("..")
        cmds.setParent("..")
        
        # ===== CLEANUP =====
        cmds.frameLayout(label="Cleanup", collapsable=True, marginWidth=5, marginHeight=5)
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=True)
        cmds.button(
            label="Select Locators",
            command=self._select_locators
        )
        cmds.button(
            label="Delete All",
            backgroundColor=(0.6, 0.3, 0.3),
            command=self._cleanup_all
        )
        cmds.setParent("..")
        cmds.setParent("..")
        
        cmds.setParent("..")  # main_layout
        
        # Show window
        cmds.showWindow(self.window)
    
    # =========================================================================
    # UI CALLBACKS
    # =========================================================================
    def _update_setting(self, key, value):
        """Update a setting value."""
        self.settings[key] = value
    

    def _on_space_mode_change(self, mode, *args):
        """Handle space mode change."""
        self.settings["space_mode"] = mode
        
        # Update UI interactions if needed
        # (Target field logic is handled by validation in Stage 1)
        pass

        # Auto-populate Camera target
        if mode == "camera":
            panel = cmds.getPanel(withFocus=True)
            if panel and "modelPanel" in panel:
                cam = cmds.modelPanel(panel, query=True, camera=True)
                if cam:
                    # cam might be shape or transform, get transform
                    if cmds.nodeType(cam) == "camera":
                        cam = cmds.listRelatives(cam, parent=True)[0]
                    cmds.textField(self.target_field, edit=True, text=cam)
                    self.target_object = cam

    
    def _on_rotation_order_change(self, value):
        """Handle rotation order menu change."""
        order_index = ROTATION_ORDERS.index(value.lower())
        self.settings["rotation_order"] = order_index
        
        # Update preview locator if exists
        if self.preview_locator and cmds.objExists(self.preview_locator):
            cmds.setAttr(f"{self.preview_locator}.rotateOrder", order_index)
            
    def _adj_scale(self, amount, *args):
        """Additive scale adjustment for selected (or preview) locators."""
        sel = cmds.ls(selection=True)
        
        # If nothing selected, try to affect preview locator
        if not sel and self.preview_locator and cmds.objExists(self.preview_locator):
            target_objs = [self.preview_locator]
        else:
            target_objs = sel
            
        if not target_objs:
             cmds.warning("Select locators/objects to scale.")
             return

        for obj in target_objs:
            # Check if attributes are locked
            if cmds.getAttr(f"{obj}.scaleX", lock=True):
                continue
                
            current_x = cmds.getAttr(f"{obj}.scaleX")
            current_y = cmds.getAttr(f"{obj}.scaleY")
            current_z = cmds.getAttr(f"{obj}.scaleZ")
            
            # If it's a locator shape, we might be scaling localScale (like previous slider)
            # But user asked for scaling transforms.
            # Usually users scale the 'localScale' attr on shape for locators to avoid transform scale issues.
            # Let's check if it's a locator.
            shapes = cmds.listRelatives(obj, shapes=True)
            is_locator = False
            if shapes:
                if cmds.nodeType(shapes[0]) == "locator":
                    is_locator = True
                    
            if is_locator:
                # Scale the LOCAL scale attributes on the shape
                shape = shapes[0]
                sx = cmds.getAttr(f"{shape}.localScaleX")
                sy = cmds.getAttr(f"{shape}.localScaleY")
                sz = cmds.getAttr(f"{shape}.localScaleZ")
                
                # Prevent negative scale?
                new_s = max(0.1, sx + amount)
                
                cmds.setAttr(f"{shape}.localScaleX", new_s)
                cmds.setAttr(f"{shape}.localScaleY", new_s)
                cmds.setAttr(f"{shape}.localScaleZ", new_s)
            else:
                # Standard transform scale
                new_s = max(0.1, current_x + amount)
                cmds.scale(new_s, new_s, new_s, obj)
                
    def _on_color_select(self, color_name, *args):
        """Handle color button click. Applies to SELECTION."""
        color_index = LOCATOR_COLORS.get(color_name, 17)
        self.settings["color_index"] = color_index
        
        # Apply to selection
        sel = cmds.ls(selection=True)
        
        # Also update preview locator if it exists and nothing selected, or if it is selected
        if not sel and self.preview_locator and cmds.objExists(self.preview_locator):
            sel = [self.preview_locator]
            
        if not sel:
            cmds.inViewMessage(message=f"Color set to {color_name}. Select objects to apply.", pos="midCenter", fade=True)
            return

        for obj in sel:
            shapes = cmds.listRelatives(obj, shapes=True)
            if not shapes:
                continue
                
            for shape in shapes:
                cmds.setAttr(f"{shape}.overrideEnabled", 1)
                cmds.setAttr(f"{shape}.overrideColor", color_index)
    
    def _pick_object(self, field_type, *args):
        """Pick object from selection for source or target field."""
        sel = cmds.ls(selection=True)
        if not sel:
            cmds.warning("Nothing selected to pick.")
            return

        obj = sel[0]
        if field_type == "source":
            cmds.textField(self.source_field, edit=True, text=obj)
        elif field_type == "target":
            self.target_object = obj
            cmds.textField(self.target_field, edit=True, text=obj)
            
    def _create_preview_locator(self, *args):
        """Create a preview locator to visualize settings."""
        # Delete existing preview
        if cmds.objExists("_SS_preview_locator"):
            cmds.delete("_SS_preview_locator")
        
        # Determine position source
        # Priority: Source Field -> Selection -> World Center
        source_obj = cmds.textField(self.source_field, query=True, text=True)
        if not source_obj or not cmds.objExists(source_obj):
             sel = cmds.ls(selection=True)
             if sel:
                 source_obj = sel[0]
        
        # Create preview
        loc = cmds.spaceLocator(name="_SS_preview_locator")[0]
        self.preview_locator = loc
        
        # Apply current settings
        size = self.settings["locator_size"]
        cmds.setAttr(f"{loc}.localScaleX", size)
        cmds.setAttr(f"{loc}.localScaleY", size)
        cmds.setAttr(f"{loc}.localScaleZ", size)
        
        shape = cmds.listRelatives(loc, shapes=True)[0]
        cmds.setAttr(f"{shape}.overrideEnabled", 1)
        cmds.setAttr(f"{shape}.overrideColor", self.settings["color_index"])
        
        cmds.setAttr(f"{loc}.rotateOrder", self.settings["rotation_order"])
        
        cmds.setAttr(f"{loc}.rotateOrder", self.settings["rotation_order"])
        
        # Match to source if available
        if source_obj and cmds.objExists(source_obj):
            cmds.matchTransform(loc, source_obj, position=True, rotation=True)
        
        cmds.select(loc)
    
    # =========================================================================
    # STAGE OPERATIONS
    # =========================================================================
    def _stage_create(self, *args):
        """Stage 1: Create locator setup."""
        # Get source object
        source_obj = cmds.textField(self.source_field, query=True, text=True)
        
        # Fallback to selection if source field is empty
        if not source_obj:
            sel = cmds.ls(selection=True)
            if sel:
                source_obj = sel[0]
                # Auto-populate field
                cmds.textField(self.source_field, edit=True, text=source_obj)
        
        if not source_obj or not cmds.objExists(source_obj):
            cmds.warning("Please direct 'Source' to an object or select an object.")
            return False


        # Prepare list
        objects_to_process = [source_obj]
        
        # Delete preview locator
        if cmds.objExists("_SS_preview_locator"):
            cmds.delete("_SS_preview_locator")
            self.preview_locator = None
        
        # Clear previous data
        self.switcher = SpaceSwitcher()
        
        # Query UI state directly for robustness
        effective_mode = self.settings.get("space_mode", "world")

        # Validate target
        if effective_mode in ["object", "camera", "aim"]:
            target_obj_name = cmds.textField(self.target_field, query=True, text=True)
            if not target_obj_name or not cmds.objExists(target_obj_name):
                 cmds.warning(f"{effective_mode.title()} mode requires a valid Target object.")
                 return False
            self.target_object = target_obj_name
                
                
        for obj in objects_to_process:
            
            # Auto-detect best rotation order if enabled
            rot_order = self.settings["rotation_order"]
            if self.settings["auto_best_order"]:
                start = cmds.playbackOptions(q=True, min=True)
                end = cmds.playbackOptions(q=True, max=True)
                best_order = self.switcher.get_best_rotation_order(obj, start, end)
                if best_order is not None:
                    rot_order = best_order
                    # Update menu to reflect choice (optional, might be confusing if batching)
                    # cmds.optionMenu(self.rot_order_menu, edit=True, select=best_order+1)

            # Create locator hierarchy with MASTER logic
            top_group, locator, master = self.switcher.create_locator_hierarchy(
                source_obj=obj,
                target_obj=self.target_object, # Pass strict target (or None)
                mode=effective_mode,    # Pass mode so master constraints are built
                num_offsets=self.settings["num_offsets"],
                locator_size=self.settings["locator_size"],
                color_index=self.settings["color_index"],
                rotation_order=rot_order
            )
            
            if not top_group:
                 continue

            
            # Create temporary constraints to TOP_GROUP for baking
            # The MASTER above it is already constrained to the space
            # So we just constrain top_group to Source to capture motion relative to Master
            
            self.switcher.create_temp_constraints(
                obj, top_group,
                translate=self.settings["translate"],
                rotate=self.settings["rotate"]
            )
            
            # Check for rig_layer
            if cmds.objExists("rig_layer"):
                cmds.editDisplayLayerMembers("rig_layer", master, noRecurse=True)
        
        # Select the created locators
        top_groups = [data["top_group"] for data in self.switcher.created_locators]
        cmds.select(top_groups)
        
        cmds.inViewMessage(
            message=f"Created {len(top_groups)} locator setup(s). Ready for baking.",
            pos="midCenter", fade=True
        )
        return True
    
    def _stage_bake(self, *args):
        """Stage 2: Bake animation to locators."""
        if not self.switcher.created_locators:
            cmds.warning("No locators to bake. Run Stage 1 first.")
            return False
        
        # Get settings
        sample_by = self.settings["sample_by"]
        euler_filter = self.settings["euler_filter"]

        # 1. OPTIONAL: Bake Master Space first
        if self.settings.get("bake_master_space", False):
            master_groups = [data["master"] for data in self.switcher.created_locators]
            # Bake master groups, but KEEP temp constraints for the next step
            self.switcher.bake_animation(
                master_groups,
                sample_by=sample_by,
                euler_filter=euler_filter,
                cleanup_constraints=False
            )
            
            # Delete constraints on master groups (free them from target)
            for master in master_groups:
                self.switcher._delete_constraints_on_node(master)

        # 2. Bake to TOP_GROUP (parent)
        top_groups = [data["top_group"] for data in self.switcher.created_locators]
        
        self.switcher.bake_animation(
            top_groups,
            sample_by=sample_by,
            euler_filter=euler_filter,
            cleanup_constraints=True
        )
        
        if self.settings["clean_static"]:
            self.switcher.cleanup_keys(top_groups, self.settings["static_threshold"])
        
        # Select locators for animator to work with
        locators = [data["locator"] for data in self.switcher.created_locators]
        cmds.select(locators)
        cmds.inViewMessage(
            message=f"Baked {len(top_groups)} top group(s). Locators ready for adjustments.",
            pos="midCenter", fade=True
        )
        return True
    
    def _stage_rebuild(self, *args):
        """Stage 3: Rebuild constraints from locators to source."""
        if not self.switcher.created_locators:
            cmds.warning("No locator data. Run Stage 1 and 2 first.")
            return False
        
        self.switcher.rebuild_constraints(
            translate=self.settings["translate"],
            rotate=self.settings["rotate"],
            maintain_offset=False
        )
        
        sources = [data["source"] for data in self.switcher.created_locators]
        cmds.select(sources)
        cmds.inViewMessage(
            message="Constraints rebuilt! Space switch complete.",
            pos="midCenter", fade=True
        )
        return True
        
    def _stage_run_all(self, *args):
        """Run all stages in sequence."""
        if not self._stage_create():
            return
        
        # Force a refresh to ensure Maya processes the creation
        cmds.refresh()
        
        if not self._stage_bake():
            return
            
        if not self._stage_rebuild():
            return
            
        # Select the BAKED locators (offset locators)
        if self.switcher.created_locators:
            top_groups = [data["top_group"] for data in self.switcher.created_locators]
            cmds.select(top_groups)
        
        cmds.inViewMessage(
            message="FULL SPACE SWITCH COMPLETE! Offset locators selected.",
            pos="midCenter", fade=True, pivot=[0,0]
        )
    
    # =========================================================================
    # CLEANUP
    # =========================================================================
    def _select_locators(self, *args):
        """Select all created locators."""
        if self.switcher.created_locators:
            locators = [data["top_group"] for data in self.switcher.created_locators]
            existing = [loc for loc in locators if cmds.objExists(loc)]
            if existing:
                cmds.select(existing)
            else:
                cmds.warning("No locators found in scene.")
        else:
            # Try to find by naming convention
            all_locs = cmds.ls("*" + LOCATOR_SUFFIX, type="transform")
            if all_locs:
                cmds.select(all_locs)
            else:
                cmds.warning("No space switch locators found.")
    
    def _cleanup_all(self, *args):
        """Delete all locators (constraints first to prevent pop)."""
        self.switcher.cleanup(delete_constraints_first=True)
        
        # Also delete any preview locator
        if cmds.objExists("_SS_preview_locator"):
            cmds.delete("_SS_preview_locator")
        
        cmds.inViewMessage(
            message="Cleanup complete. Constraints and locators deleted.",
            pos="midCenter", fade=True
        )


# ============================================================================
# LAUNCH
# ============================================================================
# Global variable to hold the window instance and prevent GC
_space_switch_ui_instance = None

def show():
    """Show the Space Switch Dashboard."""
    global _space_switch_ui_instance
    _space_switch_ui_instance = SpaceSwitchDashboard()
    return _space_switch_ui_instance


# Run on import/execute
if __name__ == "__main__":
    show()
else:
    show()
