"""
Example Script for PrecastWallBKK
"""

import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_Reinforcement as AllplanReinf
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import GeometryValidate as GeometryValidate

import NemAll_Python_Utility

import StdReinfShapeBuilder.ProfileReinfShapeBuilder as ProfileShapeBuilder
import StdReinfShapeBuilder.GeneralReinfShapeBuilder as GeneralShapeBuilder
import StdReinfShapeBuilder.LinearBarPlacementBuilder as LinearBarBuilder

from StdReinfShapeBuilder.ConcreteCoverProperties import ConcreteCoverProperties
from StdReinfShapeBuilder.ReinforcementShapeProperties import ReinforcementShapeProperties
from StdReinfShapeBuilder.RotationAngles import RotationAngles

from HandleDirection import HandleDirection
from HandleProperties import HandleProperties
from PythonPart import View2D3D, PythonPart

import math

print('Load wall4.py')

def check_allplan_version(build_ele, version):
    """
    Check the current Allplan version

    Args:
        build_ele: the building element.
        version:   the current Allplan version

    Returns:
        True/False if version is supported by this script
    """

    # Delete unused arguments
    del build_ele
    del version

    # Support all versions
    return True


def create_element(build_ele, doc):
    """
    Creation of element

    Args:
        build_ele: the building element.
        doc:       input document
    """
    element = CreateWall(doc)

    return element.create(build_ele)


def move_handle(build_ele, handle_prop, input_pnt, doc):
    """
    Modify the element geometry by handles

    Args:
        build_ele:  the building element.
        handle_prop handle properties
        input_pnt:  input point
        doc:        input document
    """

    build_ele.change_property(handle_prop, input_pnt)

    return create_element(build_ele, doc)

def create_longitudinal_shape_with_hooks_edit(length, model_angles,
                                         shape_props,
                                         concrete_cover_props,
                                         start_hook=0,
                                         end_hook=0,
                                         start_angle=0,
                                         end_angle=0):

    shape_builder = AllplanReinf.ReinforcementShapeBuilder()

    shape_builder.AddPoints([(AllplanGeo.Point2D(), concrete_cover_props.left),
                             (AllplanGeo.Point2D(length, 0), concrete_cover_props.bottom),
                             (concrete_cover_props.right)])

    if start_hook == 0:
        shape_builder.SetAnchorageHookStart(start_angle)
    elif start_hook > 0:
        shape_builder.SetHookStart(start_hook, start_angle, AllplanReinf.HookType.eAnchorage)

    if end_hook == 0:
        shape_builder.SetAnchorageHookEnd(end_angle)
    elif end_hook > 0:
        shape_builder.SetHookEnd(end_hook, end_angle, AllplanReinf.HookType.eAnchorage)

    shape = shape_builder.CreateShape(shape_props)

    if shape.IsValid() is True:
        shape.Rotate(model_angles)

    return shape

class CreateWall():
    """
    Definition of class CreateWall
    """

    def __init__(self, doc):
        """
        Initialisation of class CreateWall

        Args:
            doc: input document
        """

        self.model_ele_list = []
        self.handle_list = []
        self.document = doc


    def create(self, build_ele):
        """
        Create the elements

        Args:
            build_ele:  the building element.

        Returns:
            tuple  with created elements and handles.
        """

        self.wall_length  = build_ele.Length1_1.value
        self.wall_width = build_ele.Width1_1.value
        self.wall_thickness = build_ele.Thickness1_1.value

        #Reinforcement Get Value Start 01

        self.windows_refx = build_ele.win_x.value
        self.windows_refz = build_ele.win_z.value
        self.windows_width = build_ele.win_width.value
        self.windows_length  = build_ele.win_length.value

        self.shading_back_d=build_ele.shading_back_depth.value

        #upper_shading get data
        self.shading_d=build_ele.shading1_depth.value
        self.shading_b=build_ele.shading1_b.value
        self.shading_t=build_ele.shading1_thickness.value
        self.shading_l=build_ele.shading1_length.value

        self.rein = build_ele.chkb_rein.value
        self.concrete_grade        = 4
        self.concrete_cover        = 0
        self.diameter              = build_ele.Diameter.value
        self.bending_roller        = 4.0
        self.steel_grade           = 4
        self.distance              = build_ele.Distance.value
        self.mesh_type             = None

        # self.concrete_cover = build_ele.ConcreteCover.value
        # self.diameter       = build_ele.Diameter.value
        # self.bending_roller = build_ele.BendingRoller.value
        # self.concrete_grade = build_ele.ConcreteGrade.value
        # self.steel_grade    = build_ele.SteelGrade.value
        # self.distance       = build_ele.Distance.value
        # self.mesh_type      = build_ele.MeshType.value

        self.start_hook            = True
        self.start_hook_angle      = AllplanGeo.Angle()
        self.end_hook              = True
        self.end_hook_angle        = AllplanGeo.Angle()


        self.distance_longbar       = 50
        self.distance_longbar_vshade= 90 #vshade rein@distance
        self.distance_rein_shading  = 200
        #Wiremesh
        self.distance_wiremesh = build_ele.Distance2.value

        #Reinforcement Get Value End 01

        self.create_geometry(build_ele)

        views = [View2D3D (self.model_ele_list)]

        reinforcement = []

        if (self.rein) :
            reinforcement = self.create_reinforcement()

        pythonpart = PythonPart ("Wall Creation",
                                 parameter_list = build_ele.get_params_list(),
                                 hash_value     = build_ele.get_hash(),
                                 python_file    = build_ele.pyp_file_name,
                                 views          = views,
                                 reinforcement  = reinforcement)

        self.model_ele_list = pythonpart.create()

        return (self.model_ele_list, self.handle_list)


    def create_reinforcement(self):
        """
        Create the stirrup placement
        Returns: created stirrup reinforcement
        """
        self.start_hook_angle.Deg = 180.0
        self.end_hook_angle.Deg = 180.0

        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller, self.steel_grade,
                                                         self.concrete_grade, AllplanReinf.BendingShapeType.Stirrup)

        shape_props_longbar = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        

        start_hook = -1
        start_hook_angle  = 90
        if self.start_hook:
            start_hook = 0 # 0 == calculate hook length
            start_hook_angle = self.start_hook_angle.Deg

        end_hook = -1
        end_hook_angle = 90
        if self.end_hook:
            end_hook = 0 # 0 == calculate hook length
            end_hook_angle = self.end_hook_angle.Deg

        #offset from windows
        offset = 50
        shape1_offset = 20
        y1_cover_offset = 30

        x1_ref= 0
        y1_ref= 0 + y1_cover_offset
        z1_ref= self.windows_refz + self.windows_width + offset + shape1_offset
        placement1_length = self.wall_length    #130 is depth of shading back

        placement1_start_point = AllplanGeo.Point3D(x1_ref, y1_ref, z1_ref)
        placement1_end_point = AllplanGeo.Point3D(x1_ref+placement1_length, y1_ref, z1_ref)
        rotation1_angles = RotationAngles(90, 0, 90)

        
        shape1 = GeneralShapeBuilder.create_open_stirrup(200, 420,
                                                        rotation1_angles,
                                                        shape_props,
                                                        concrete_cover_props,
                                                        start_hook,
                                                        end_hook,
                                                        start_hook_angle,
                                                        end_hook_angle)
        
        z_longbar_offset=30
        y_longbar_offset=40

        x2_ref= 0
        y2_ref= 0
        z2_ref= self.windows_refz + self.windows_width + z_longbar_offset + offset
        longbar_length = self.wall_length -1    #130 is depth of shading back

        longbar_start_point = AllplanGeo.Point3D(x2_ref, y2_ref+y_longbar_offset, z2_ref)
        longbar_end_point = AllplanGeo.Point3D(x2_ref, y2_ref+self.shading_back_d+self.wall_thickness-y_longbar_offset, z2_ref)

        longbar_angles = RotationAngles(90, 0 , 0)

        shape_longbar = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_length,
                                                                               longbar_angles,
                                                                               shape_props_longbar,
                                                                               concrete_cover_props)
        


        reinforcement = []

        if shape1.IsValid():
            reinforcement.append (LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape1,
                placement1_start_point,
                placement1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance))

        if shape_longbar.IsValid():
            reinforcement.append (LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar,
                longbar_start_point,
                longbar_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_longbar))

        #shape_props_longbar_vshade1



        reinforcement.append( self.create_rein_shading() )
        reinforcement.append( self.create_longbar_vshading1() )
        reinforcement.append( self.create_longbar_vshading2() )
        reinforcement.append( self.create_longbar_vshading3() )
        reinforcement.append( self.create_longbar_vshading4() )
        #Wiremesh Adding
        reinforcement.append( self.create_longbar_wiremesh1() )
        reinforcement.append( self.create_longbar_wiremesh2() )
        reinforcement.append( self.create_longbar_wiremesh3() )
        reinforcement.append( self.create_longbar_wiremesh4() )
        reinforcement.append( self.create_longbar_wiremesh5() )
        reinforcement.append( self.create_longbar_wiremesh6() )

        #create_longbar_wiremesh_h1

        reinforcement.append( self.create_longbar_wiremesh_h1() )
        reinforcement.append( self.create_longbar_wiremesh_h2() )
        reinforcement.append( self.create_longbar_wiremesh_h3() )
        reinforcement.append( self.create_longbar_wiremesh_h4() )
        reinforcement.append( self.create_longbar_wiremesh_h5() )
        reinforcement.append( self.create_longbar_wiremesh_h6() )

        return reinforcement

    def create_longbar_wiremesh1(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0

        wiremesh1_x_ref= 0
        wiremesh1_y_ref= 30
        wiremesh1_z_ref= 0
        wiremesh1_depth = 0
        #0 point to start windows
        wiremesh1_x1_length = self.windows_refx
        longbar_wiremesh1_length = self.wall_width -1    #130 is depth of shading back

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+y_longbar_wiremesh1_offset, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref+wiremesh1_x1_length, wiremesh1_y_ref+wiremesh1_depth, wiremesh1_z_ref)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(0, -90 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh2(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0

        wiremesh1_x_ref= 0
        wiremesh1_y_ref= 30
        wiremesh1_z_ref= 50
        wiremesh1_depth = 0

        #0 point to start windows
        wiremesh1_x1_length = self.windows_refx
        longbar_wiremesh1_length = self.wall_width -1    #130 is depth of shading back

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref+wiremesh1_x1_length, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(0, -90 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh3(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0


        #|<---|--->|    |
        wiremesh1_x_ref= self.windows_refx + self.windows_length
        #|<---|----|--->|
        wiremesh1_x1_length = self.wall_length-wiremesh1_x_ref

        wiremesh1_y_ref= 30
        wiremesh1_z_ref= 0
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.wall_width -1    #130 is depth of shading back

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+y_longbar_wiremesh1_offset, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref+wiremesh1_x1_length, wiremesh1_y_ref+wiremesh1_depth, wiremesh1_z_ref)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(0, -90 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh4(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0

       #|<---|--->|    |
        wiremesh1_x_ref= self.windows_refx + self.windows_length
        #|<---|----|--->|
        wiremesh1_x1_length = self.wall_length-wiremesh1_x_ref

        wiremesh1_y_ref= 30
        wiremesh1_z_ref= 50
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.wall_width -1    #130 is depth of shading back

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref+wiremesh1_x1_length, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(0, -90 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh5(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0


        #|<-->|    |    |
        wiremesh1_x_ref= self.windows_refx
        #|<---|--->|    |
        wiremesh1_x1_length = self.windows_length

        wiremesh1_y_ref= 30
        wiremesh1_z_ref= 0
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.windows_refz-10    

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+y_longbar_wiremesh1_offset, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref+wiremesh1_x1_length, wiremesh1_y_ref+wiremesh1_depth, wiremesh1_z_ref)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(0, -90 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh6(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0

        #|<-->|    |    |
        wiremesh1_x_ref= self.windows_refx
        #|<---|--->|    |
        wiremesh1_x1_length = self.windows_length

        wiremesh1_y_ref= 30
        wiremesh1_z_ref= 50
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.windows_refz-60    #130 is depth of shading back

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref+wiremesh1_x1_length, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(0, -90 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

 

    def create_longbar_wiremesh_h1(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0


        #|<-->|    |    |
        wiremesh1_x_ref= self.windows_refx
        #|<---|--->|    |
        wiremesh1_x1_length = self.windows_length
        #------
        wiremesh1_h_width = self.wall_width

        #

        wiremesh1_x_ref= 0
        wiremesh1_y_ref= 30
        wiremesh1_z_ref= self.windows_refz
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.windows_refx    

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+y_longbar_wiremesh1_offset, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+wiremesh1_depth, wiremesh1_h_width)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(90, 0 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)




        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh_h2(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0


        #|<-->|    |    |
        wiremesh1_x_ref= self.windows_refx
        #|<---|--->|    |
        wiremesh1_x1_length = self.windows_length
        #------
        wiremesh1_h_width = self.wall_width

        #

        wiremesh1_x_ref= 0
        wiremesh1_y_ref= 30
        wiremesh1_z_ref= self.windows_refz
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.windows_refx    

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_h_width)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(90, 0 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)




        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh_h3(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0



        #|<-->|    |    |
        wiremesh1_x_ref= self.windows_refx + self.windows_length
        #|<---|--->|    |
        wiremesh1_x1_length = self.wall_length
        #------
        wiremesh1_h_width = self.wall_width

        #

        
        wiremesh1_y_ref= 30
        wiremesh1_z_ref= self.windows_refz
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.wall_length - (self.windows_refx + self.windows_length)    

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+y_longbar_wiremesh1_offset, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+wiremesh1_depth, wiremesh1_h_width)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(90, 0 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)




        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh_h4(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0


        #|<-->|    |    |
        wiremesh1_x_ref= self.windows_refx + self.windows_length
        #|<---|--->|    |
        wiremesh1_x1_length = self.wall_length
        #------
        wiremesh1_h_width = self.wall_width

        #

        
        wiremesh1_y_ref= 30
        wiremesh1_z_ref= self.windows_refz
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.wall_length - (self.windows_refx + self.windows_length)    

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_h_width)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(90, 0 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)




        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh_h5(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0


        #|<-->|    |    |
        wiremesh1_x_ref= self.windows_refx
        #|<---|--->|    |
        wiremesh1_x1_length = self.windows_length
        #------
        wiremesh1_h_width = self.windows_refz

        #

        wiremesh1_x_ref= 0
        wiremesh1_y_ref= 30
        wiremesh1_z_ref= 0
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.wall_length   

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+y_longbar_wiremesh1_offset, wiremesh1_z_ref)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref, wiremesh1_y_ref+wiremesh1_depth, wiremesh1_h_width-20)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(90, 0 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)




        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1

    def create_longbar_wiremesh_h6(self):
        longbar_wiremesh1 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_wiremesh1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_wiremesh1_offset=30
        y_longbar_wiremesh1_offset=0


        #|<-->|    |    |
        wiremesh1_x_ref= self.windows_refx
        #|<---|--->|    |
        wiremesh1_x1_length = self.windows_length
        #------
        wiremesh1_h_width = self.windows_refz

        #

        wiremesh1_x_ref= 0
        wiremesh1_y_ref= 30
        wiremesh1_z_ref= 0
        wiremesh1_depth = 0
        #0 point to start windows
        


        longbar_wiremesh1_length = self.wall_length   

        longbar_wiremesh1_start_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_z_ref+50)
        longbar_wiremesh1_end_point = AllplanGeo.Point3D(wiremesh1_x_ref, self.wall_thickness - wiremesh1_y_ref, wiremesh1_h_width-20)
        #Edit Z 90
        longbar_wiremesh1_angles = RotationAngles(90, 0 , 0)

        shape_longbar_wiremesh1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_wiremesh1_length,
                                                                               longbar_wiremesh1_angles,
                                                                               shape_props_longbar_wiremesh1,
                                                                               concrete_cover_props)




        if shape_longbar_wiremesh1.IsValid():
          longbar_wiremesh1 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_wiremesh1,
                longbar_wiremesh1_start_point,
                longbar_wiremesh1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_wiremesh)

        return longbar_wiremesh1


# Shading Vertical
    def create_longbar_vshading1(self):
        longbar_vshading = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_vshade1 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_vshade1_offset=30
        y_longbar_vshade1_offset=0

        vshade1_x_ref= 30
        vshade1_y_ref= -280
        vshade1_z_ref= 0
        vshade1_depth = 280
        longbar_vshade1_length = self.wall_width -1    #130 is depth of shading back

        longbar_vshade1_start_point = AllplanGeo.Point3D(vshade1_x_ref, vshade1_y_ref+y_longbar_vshade1_offset, vshade1_z_ref)
        longbar_vshade1_end_point = AllplanGeo.Point3D(vshade1_x_ref, vshade1_y_ref+vshade1_depth, vshade1_z_ref)
        #Edit Z 90
        longbar_vshade1_angles = RotationAngles(0, -90 , 0)

        shape_longbar_vshade1 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_vshade1_length,
                                                                               longbar_vshade1_angles,
                                                                               shape_props_longbar_vshade1,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_vshade1.IsValid():
          longbar_vshading = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_vshade1,
                longbar_vshade1_start_point,
                longbar_vshade1_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_longbar_vshade)

        return longbar_vshading

    def create_longbar_vshading2(self):
        longbar_vshading2 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_vshade2 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_vshade2_offset=30
        y_longbar_vshade2_offset=0

        vshade2_x_ref= 430
        vshade2_y_ref= -280
        vshade2_z_ref= 0
        vshade2_depth = 280
        longbar_vshade2_length = self.wall_width -1    #130 is depth of shading back

        longbar_vshade2_start_point = AllplanGeo.Point3D(vshade2_x_ref, vshade2_y_ref+y_longbar_vshade2_offset, vshade2_z_ref)
        longbar_vshade2_end_point = AllplanGeo.Point3D(vshade2_x_ref, vshade2_y_ref+vshade2_depth, vshade2_z_ref)
        #Edit Z 90
        longbar_vshade2_angles = RotationAngles(0, -90 , 0)

        shape_longbar_vshade2 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_vshade2_length,
                                                                               longbar_vshade2_angles,
                                                                               shape_props_longbar_vshade2,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_vshade2.IsValid():
          longbar_vshading2 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_vshade2,
                longbar_vshade2_start_point,
                longbar_vshade2_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_longbar_vshade)

        return longbar_vshading2

    def create_longbar_vshading3(self):
        longbar_vshading3 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_vshade3 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_vshade3_offset=30
        y_longbar_vshade3_offset=0

        vshade3_x_ref= self.wall_length - 430
        vshade3_y_ref= -280
        vshade3_z_ref= 0
        vshade3_depth = 280
        longbar_vshade3_length = self.wall_width -1    #130 is depth of shading back

        longbar_vshade3_start_point = AllplanGeo.Point3D(vshade3_x_ref, vshade3_y_ref+y_longbar_vshade3_offset, vshade3_z_ref)
        longbar_vshade3_end_point = AllplanGeo.Point3D(vshade3_x_ref, vshade3_y_ref+vshade3_depth, vshade3_z_ref)
        #Edit Z 90
        longbar_vshade3_angles = RotationAngles(0, -90 , 0)

        shape_longbar_vshade3 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_vshade3_length,
                                                                               longbar_vshade3_angles,
                                                                               shape_props_longbar_vshade3,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_vshade3.IsValid():
          longbar_vshading3 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_vshade3,
                longbar_vshade3_start_point,
                longbar_vshade3_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_longbar_vshade)

        return longbar_vshading3

    def create_longbar_vshading4(self):
        longbar_vshading4 = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar_vshade4 = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        # Longbar Vertical Shading Start-01
        z_longbar_vshade4_offset=30
        y_longbar_vshade4_offset=0

        vshade4_x_ref= self.wall_length - 30
        vshade4_y_ref= -280
        vshade4_z_ref= 0
        vshade4_depth = 280
        longbar_vshade4_length = self.wall_width -1    #130 is depth of shading back

        longbar_vshade4_start_point = AllplanGeo.Point3D(vshade4_x_ref, vshade4_y_ref+y_longbar_vshade4_offset, vshade4_z_ref)
        longbar_vshade4_end_point = AllplanGeo.Point3D(vshade4_x_ref, vshade4_y_ref+vshade4_depth, vshade4_z_ref)
        #Edit Z 90
        longbar_vshade4_angles = RotationAngles(0, -90 , 0)

        shape_longbar_vshade4 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(longbar_vshade4_length,
                                                                               longbar_vshade4_angles,
                                                                               shape_props_longbar_vshade4,
                                                                               concrete_cover_props)

        # Longbar Vertical Shading End-01

        if shape_longbar_vshade4.IsValid():
          longbar_vshading4 = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, shape_longbar_vshade4,
                longbar_vshade4_start_point,
                longbar_vshade4_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_longbar_vshade)

        return longbar_vshading4


    def create_rein_shading(self):
        rein_shading = None
        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_rein_shading = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        offset = 50

        x_offset = 0
        y_offset = 30
        z_offset = 20

        x_ref = self.windows_refx + self.windows_length/2 - self.shading_l/2 + x_offset
        y_ref = -self.shading_d + y_offset
        z_ref = self.windows_refz + self.windows_width + offset + z_offset

        rein_shading_length = self.shading_b - z_offset*2

        rein_shading_start_point = AllplanGeo.Point3D(x_ref, y_ref, z_ref)
        rein_shading_end_point = AllplanGeo.Point3D(x_ref+self.shading_l, y_ref, z_ref)


        theta = math.atan2(self.shading_t-self.shading_b,self.shading_d)
        theta = math.degrees(theta)
        #NemAll_Python_Utility.ShowMessageBox('%6.2f' %theta,1)

        #theta = 14.93
        start_hook = -1
        end_hook = 500
        start_hook_angle  = 90
        end_hook_angle = 90-theta

        rein_shading_angles = RotationAngles(0, 270 , 0)

        # rein_shading_shape = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(rein_shading_length,
        #                                                                        rein_shading_angles,
        #                                                                        shape_props_rein_shading,
        #                                                                        concrete_cover_props,
        #                                                                        start_hook,
        #                                                                        end_hook)

        rein_shading_shape = create_longitudinal_shape_with_hooks_edit(rein_shading_length,
                                                                               rein_shading_angles,
                                                                               shape_props_rein_shading,
                                                                               concrete_cover_props,
                                                                               start_hook = start_hook,
                                                                               end_hook = end_hook,
                                                                               start_angle = start_hook_angle,
                                                                               end_angle = end_hook_angle)

        if rein_shading_shape.IsValid():
          rein_shading = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, rein_shading_shape,
                rein_shading_start_point,
                rein_shading_end_point,
                self.concrete_cover,
                self.concrete_cover,
                self.distance_rein_shading)

        return rein_shading


    def add_windows(self, build_ele, com_prop_stroke, wall_length, wall_width, wall_thickness):
        p_x = build_ele.win_x.value
        p_y = 0
        p_z = build_ele.win_z.value

        void_length  = build_ele.win_length.value
        void_width = build_ele.win_width.value
        void_thickness = wall_thickness

        void = AllplanGeo.Polyhedron3D.CreateCuboid(void_length, void_thickness, void_width)
        trans_to_ref_point_2 = AllplanGeo.Matrix3D()
        trans_to_ref_point_2.Translate(AllplanGeo.Vector3D(p_x, p_y, p_z))
        void = AllplanGeo.Transform(void, trans_to_ref_point_2)

        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, void))

        #--------------------------------------------------------------------------------------#
        #----------------------------------Void Handle-----------------------------------------#
        #--------------------------------------------------------------------------------------#
        origin = AllplanGeo.Point3D(0, 0, 0)

        originwin = AllplanGeo.Point3D(p_x, 0, p_z)
        win_plength = AllplanGeo.Point3D(p_x+void_length, 0, p_z)
        win_pwidth = AllplanGeo.Point3D(p_x, 0, p_z+void_width)
        win_pointx = AllplanGeo.Point3D(p_x+void_length/2, 0, p_z)
        win_pointz = AllplanGeo.Point3D(p_x, 0, p_z+void_width/2)

        handle_winlength = HandleProperties("windowsMoveLength",
                                   win_plength,
                                   originwin,
                                   [("win_length", HandleDirection.x_dir)],
                                   HandleDirection.x_dir,
                                   True)
        self.handle_list.append(handle_winlength)

        handle_winwidth = HandleProperties("windowsMoveWidth",
                                   win_pwidth,
                                   originwin,
                                   [("win_width", HandleDirection.z_dir)],
                                   HandleDirection.z_dir,
                                   True)
        self.handle_list.append(handle_winwidth)

        handle_winx = HandleProperties("windowsMoveX",
                                   win_pointx,
                                   originwin,
                                   [("win_x", HandleDirection.x_dir)],
                                   HandleDirection.x_dir,
                                   False)
        self.handle_list.append(handle_winx)

        handle_winz = HandleProperties("windowsMoveZ",
                                   win_pointz,
                                   origin,
                                   [("win_z", HandleDirection.z_dir)],
                                   HandleDirection.z_dir,
                                   False)
        self.handle_list.append(handle_winz)

        return void

    def add_door(self, build_ele, com_prop_stroke, wall_length, wall_width, wall_thickness):
        d_x = build_ele.door_x.value
        d_y = 0
        d_z = 0

        door_length = build_ele.door_length.value
        door_width = build_ele.door_width.value
        door_thickness = wall_thickness

        door = AllplanGeo.Polyhedron3D.CreateCuboid(door_length, door_thickness, door_width)
        trans_to_ref_point_3 = AllplanGeo.Matrix3D()
        trans_to_ref_point_3.Translate(AllplanGeo.Vector3D(d_x, d_y, d_z))
        door = AllplanGeo.Transform(door, trans_to_ref_point_3)

        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, door))

        #--------------------------------------------------------------------------------------#
        #----------------------------------Door Handle-----------------------------------------#
        #--------------------------------------------------------------------------------------#

        origin = AllplanGeo.Point3D(0, 0, 0)
        door_plength = AllplanGeo.Point3D(d_x+door_length, 0, 0)
        door_pwidth = AllplanGeo.Point3D(d_x, 0, door_width)
        door_pointx = AllplanGeo.Point3D(d_x, 0, 0)

        handle_doorlength = HandleProperties("DoorMoveLength",
                                   door_plength,
                                   door_pointx,
                                   [("door_length", HandleDirection.x_dir)],
                                   HandleDirection.x_dir,
                                   True)
        self.handle_list.append(handle_doorlength)

        handle_doorwidth = HandleProperties("DoorMoveWidth",
                                   door_pwidth,
                                   door_pointx,
                                   [("door_width", HandleDirection.z_dir)],
                                   HandleDirection.z_dir,
                                   True)
        self.handle_list.append(handle_doorwidth)
        handle_doorx = HandleProperties("doorMoveX",
                                   door_pointx,
                                   origin,
                                   [("door_x", HandleDirection.x_dir)],
                                   HandleDirection.x_dir,
                                   False)
        self.handle_list.append(handle_doorx)

        return door

    def add_joins_left(self, build_ele ,com_prop_stroke ,type =1) :
        wall_length  = build_ele.Length1_1.value
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value

        j_a = build_ele.type1_a.value
        j_c = build_ele.type1_c.value
        j_d = build_ele.type1_d.value

        join1_point = AllplanGeo.Polygon2D()

        path1 = AllplanGeo.Polyline3D()

        ref_pnt = AllplanGeo.Point2D(0, 0)

        if (type == 1) :
          j_b = wall_thickness/2

          join1_point += AllplanGeo.Point2D(0,-j_a/2)
          join1_point += AllplanGeo.Point2D(j_c,-j_d/2)
          join1_point += AllplanGeo.Point2D(j_c,j_d/2)
          join1_point += AllplanGeo.Point2D(0,j_a/2)
          join1_point += AllplanGeo.Point2D(0,-j_a/2)


          if not GeometryValidate.is_valid(join1_point):
              return

          path1 += AllplanGeo.Point3D(0,j_b,0)
          path1 += AllplanGeo.Point3D(0,j_b,wall_width)

        if (type == 2) :
          j_b = build_ele.type1_b.value
          join1_point += AllplanGeo.Point2D(-j_a/2,0)
          join1_point += AllplanGeo.Point2D(-j_d/2,j_c)
          join1_point += AllplanGeo.Point2D(j_d/2,j_c)
          join1_point += AllplanGeo.Point2D(j_a/2,0)
          join1_point += AllplanGeo.Point2D(-j_a/2,0)

          if not GeometryValidate.is_valid(join1_point):
              return

          path1 += AllplanGeo.Point3D(j_b,0,0)
          path1 += AllplanGeo.Point3D(j_b,0,wall_width)

          handle_b1 = HandleProperties("Moveb1",
                                   AllplanGeo.Point3D(j_b,0,0),
                                   AllplanGeo.Point3D(0, 0, 0),
                                   [("type1_b", HandleDirection.x_dir)],
                                   HandleDirection.x_dir,
                                   False)
          self.handle_list.append(handle_b1)

        if (type == 3) :

          join1_point += AllplanGeo.Point2D(0, 0)
          join1_point += AllplanGeo.Point2D(j_c, 0)
          join1_point += AllplanGeo.Point2D(j_c, j_d)
          join1_point += AllplanGeo.Point2D(0, j_a)
          join1_point += AllplanGeo.Point2D(0, 0)

          if not GeometryValidate.is_valid(join1_point):
              return

          path1 += AllplanGeo.Point3D(0,0,0)
          path1 += AllplanGeo.Point3D(0,0,wall_width)

        err, join1 = AllplanGeo.CreatePolyhedron(join1_point, ref_pnt, path1)
        if not GeometryValidate.polyhedron(err):
          #NemAll_Python_Utility.ShowMessageBox("error",1)
          return

        #NemAll_Python_Utility.ShowMessageBox("pass2",1)
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, join1))
        return join1

    def add_joins_right(self, build_ele ,com_prop_stroke ,type =1) :
        wall_length  = build_ele.Length1_1.value
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value

        j_a = build_ele.type2_a.value
        j_c = build_ele.type2_c.value
        j_d = build_ele.type2_d.value

        join2_point = AllplanGeo.Polygon2D()

        path2 = AllplanGeo.Polyline3D()

        ref_pnt = AllplanGeo.Point2D(0, 0)

        if (type == 1) :
          j_b = wall_thickness/2

          join2_point += AllplanGeo.Point2D(0,-j_a/2)
          join2_point += AllplanGeo.Point2D(-j_c,-j_d/2)
          join2_point += AllplanGeo.Point2D(-j_c,j_d/2)
          join2_point += AllplanGeo.Point2D(0,j_a/2)
          join2_point += AllplanGeo.Point2D(0,-j_a/2)

          if not GeometryValidate.is_valid(join2_point):
              return

          path2 += AllplanGeo.Point3D(wall_length,j_b,0)
          path2 += AllplanGeo.Point3D(wall_length,j_b,wall_width)

        if (type == 2) :
          j_b = build_ele.type2_b.value
          join2_point += AllplanGeo.Point2D(-j_a/2,0)
          join2_point += AllplanGeo.Point2D(-j_d/2,j_c)
          join2_point += AllplanGeo.Point2D(j_d/2,j_c)
          join2_point += AllplanGeo.Point2D(j_a/2,0)
          join2_point += AllplanGeo.Point2D(-j_a/2,0)

          if not GeometryValidate.is_valid(join2_point):
              return

          path2 += AllplanGeo.Point3D(wall_length-j_b,0,0)
          path2 += AllplanGeo.Point3D(wall_length-j_b,0,wall_width)

          handle_b2 = HandleProperties("Moveb2",
                                  AllplanGeo.Point3D(wall_length-j_b,0,0),
                                  AllplanGeo.Point3D(wall_length, 0, 0),
                                  [("type2_b", HandleDirection.x_dir)],
                                  HandleDirection.x_dir,
                                  True)
          self.handle_list.append(handle_b2)


        if (type == 3) :

          join2_point += AllplanGeo.Point2D(0, 0)
          join2_point += AllplanGeo.Point2D(-j_c, 0)
          join2_point += AllplanGeo.Point2D(-j_c, j_d)
          join2_point += AllplanGeo.Point2D(0, j_a)
          join2_point += AllplanGeo.Point2D(0, 0)

          if not GeometryValidate.is_valid(join2_point):
              return

          path2 += AllplanGeo.Point3D(wall_length,0,0)
          path2 += AllplanGeo.Point3D(wall_length,0,wall_width)


        err, join2 = AllplanGeo.CreatePolyhedron(join2_point, ref_pnt, path2)
        if not GeometryValidate.polyhedron(err):
            return

        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, join2))
        return join2

    def add_upper_join(self, build_ele ,com_prop_stroke ,type =1) :

        #upper_join_l=build_ele.type3_length.value

        upper_join_l=self.wall_length
        upper_join_h=build_ele.type3_height.value
        upper_join_d1=build_ele.type3_depth1.value
        upper_join_d2=build_ele.type3_depth2.value

        wall_length  = build_ele.Length1_1.value
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value

        upper_join_point = AllplanGeo.Polygon3D()
        upper_join_path = AllplanGeo.Polyline3D()


        x_ref= wall_length/2 - upper_join_l/2
        y_ref= wall_thickness
        z_ref= wall_width
        

        upper_join_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+0)
        upper_join_point += AllplanGeo.Point3D(x_ref, y_ref-upper_join_d1, z_ref+0)
        upper_join_point += AllplanGeo.Point3D(x_ref, y_ref-upper_join_d2, z_ref+upper_join_h)
        upper_join_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+upper_join_h)
        upper_join_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+0)

        if not GeometryValidate.is_valid(upper_join_point):
          return

        upper_join_path += AllplanGeo.Point3D(x_ref,0,0)
        upper_join_path += AllplanGeo.Point3D(x_ref+upper_join_l,0,0)


        err, upper_join = AllplanGeo.CreatePolyhedron(upper_join_point, upper_join_path)
        if not GeometryValidate.polyhedron(err):
            return        
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, upper_join))
        return upper_join

    def add_lower_join(self, build_ele ,com_prop_stroke ,type =1) :
        lower_join_h=build_ele.type4_height.value
        lower_join_d1=build_ele.type4_depth1.value
        lower_join_d2=build_ele.type4_depth2.value

        wall_length  = build_ele.Length1_1.value
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value

        lower_join_point = AllplanGeo.Polygon3D()
        lower_join_path = AllplanGeo.Polyline3D()


        x_ref= 0
        y_ref= wall_thickness
        z_ref= 0
        

        lower_join_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+0)
        lower_join_point += AllplanGeo.Point3D(x_ref, y_ref-lower_join_d1, z_ref+0)
        lower_join_point += AllplanGeo.Point3D(x_ref, y_ref-lower_join_d2, z_ref+lower_join_h)
        lower_join_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+lower_join_h)
        lower_join_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+0)

        if not GeometryValidate.is_valid(lower_join_point):
          return

        lower_join_path += AllplanGeo.Point3D(x_ref,0,0)
        lower_join_path += AllplanGeo.Point3D(x_ref+wall_length,0,0)


        err, lower_join = AllplanGeo.CreatePolyhedron(lower_join_point, lower_join_path)
        if not GeometryValidate.polyhedron(err):
            return        
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, lower_join))
        return lower_join

    def add_upper_shading(self, build_ele ,com_prop_stroke) :
        #upper_shading=0

        shading_d=build_ele.shading1_depth.value
        shading_b=build_ele.shading1_b.value
        shading_t=build_ele.shading1_thickness.value
        shading_l=build_ele.shading1_length.value

        windows_refx = build_ele.win_x.value
        windows_refz = build_ele.win_z.value
        windows_length  = build_ele.win_length.value
        windows_width = build_ele.win_width.value

        upper_shading_point = AllplanGeo.Polygon3D()
        upper_shading_path = AllplanGeo.Polyline3D()

        offset=50
        
        z_ref= windows_refz + windows_width + offset
        x_ref= windows_refx + windows_length/2   - shading_l/2

        upper_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+0)
        upper_shading_point += AllplanGeo.Point3D(x_ref, -shading_d, z_ref+0)
        upper_shading_point += AllplanGeo.Point3D(x_ref, -shading_d, z_ref+shading_b)
        upper_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+shading_t)
        upper_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+0)

        if not GeometryValidate.is_valid(upper_shading_point):
          return

        upper_shading_path += AllplanGeo.Point3D(x_ref,0,0)
        upper_shading_path += AllplanGeo.Point3D(x_ref+shading_l,0,0)


        err, upper_shading = AllplanGeo.CreatePolyhedron(upper_shading_point, upper_shading_path)
        if not GeometryValidate.polyhedron(err):
            return        
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, upper_shading))
        return upper_shading

    def add_lower_shading(self, build_ele ,com_prop_stroke) :
        #lower_shading=0
        shading_d=build_ele.shading2_depth.value
        shading_b=build_ele.shading2_b.value
        shading_t=build_ele.shading2_thickness.value

        #shading_l=build_ele.shading2_length.value

        windows_refx = build_ele.win_x.value
        windows_refz = build_ele.win_z.value
        windows_length  = build_ele.win_length.value
        windows_width = build_ele.win_width.value

        shading_l=windows_length

        lower_shading_point = AllplanGeo.Polygon3D()
        lower_shading_path = AllplanGeo.Polyline3D()
        
        #offset from windows
        offset = 0

        z_ref= windows_refz - shading_t - offset
        x_ref= windows_refx + windows_length/2   - shading_l/2

        lower_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+0)
        lower_shading_point += AllplanGeo.Point3D(x_ref, -shading_d, z_ref+0)
        lower_shading_point += AllplanGeo.Point3D(x_ref, -shading_d, z_ref+shading_b)
        lower_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+shading_t)
        lower_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+0)

        if not GeometryValidate.is_valid(lower_shading_point):
          return

        lower_shading_path += AllplanGeo.Point3D(x_ref,0,0)
        lower_shading_path += AllplanGeo.Point3D(x_ref+shading_l,0,0)


        err, lower_shading = AllplanGeo.CreatePolyhedron(lower_shading_point, lower_shading_path)
        if not GeometryValidate.polyhedron(err):
            return        
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, lower_shading))
        return lower_shading

    def add_shading_back(self, build_ele ,com_prop_stroke) :
        #lower_shading=0
        shading_back_l1=build_ele.shading_back_l1.value
        shading_back_l2=build_ele.shading_back_l2.value
        shading_back_h1=build_ele.shading_back_h1.value
        shading_back_h2=build_ele.shading_back_h2.value
        shading_back_d=build_ele.shading_back_depth.value

        wall_length  = build_ele.Length1_1.value
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value

        windows_refz = build_ele.win_z.value
        windows_width = build_ele.win_width.value
        

        shading_back_point = AllplanGeo.Polygon3D()
        shading_back_path = AllplanGeo.Polyline3D()
        
        #offset from windows
        offset = 50

        x_ref= wall_length/2 - shading_back_l1/2
        y_ref= wall_thickness
        z_ref= windows_refz + windows_width + offset
        

        shading_back_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref)
        shading_back_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+shading_back_h1)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1/2 - shading_back_l2/2, y_ref, z_ref+shading_back_h1)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1/2 - shading_back_l2/2, y_ref, z_ref+shading_back_h1+shading_back_h2)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1/2 + shading_back_l2/2, y_ref, z_ref+shading_back_h1+shading_back_h2)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1/2 + shading_back_l2/2, y_ref, z_ref+shading_back_h1)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1, y_ref, z_ref+shading_back_h1)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1, y_ref, z_ref)
        shading_back_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref)

        if not GeometryValidate.is_valid(shading_back_point):
          return

        shading_back_path += AllplanGeo.Point3D(x_ref,y_ref,z_ref)
        shading_back_path += AllplanGeo.Point3D(x_ref,y_ref+shading_back_d,z_ref)


        err, shading_back = AllplanGeo.CreatePolyhedron(shading_back_point, shading_back_path)
        if not GeometryValidate.polyhedron(err):
            return
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, shading_back))
        return shading_back

    def add_ver_shading(self, build_ele ,com_prop_stroke) :
        #ver_shading=0

        ver_shading_width1  = 150
        ver_shading_width2  = 120
        ver_shading_offset  = 10
        ver_shading_depth   = 300

        ver1_shading_point = AllplanGeo.Polygon3D()
        ver2_shading_point = AllplanGeo.Polygon3D()
        ver3_shading_point = AllplanGeo.Polygon3D()
        ver4_shading_point = AllplanGeo.Polygon3D()

        ver_shading_path = AllplanGeo.Polyline3D()
        
        offset = 160

        x1_ref= 0
        y1_ref= 0
        z1_ref= 0

        x2_ref= ver_shading_width1+offset
        y2_ref= 0
        z2_ref= 0

        x3_ref= self.wall_length - (ver_shading_width1*2) - offset
        y3_ref= 0
        z3_ref= 0

        x4_ref= self.wall_length - ver_shading_width1
        y4_ref= 0
        z4_ref= 0
        
        ver1_shading_point += AllplanGeo.Point3D(x1_ref, y1_ref, z1_ref)
        ver1_shading_point += AllplanGeo.Point3D(x1_ref+ver_shading_offset, y1_ref-ver_shading_depth, z1_ref)
        ver1_shading_point += AllplanGeo.Point3D(x1_ref+ver_shading_offset+ver_shading_width2, y1_ref-ver_shading_depth, z1_ref)
        ver1_shading_point += AllplanGeo.Point3D(x1_ref+ver_shading_width1, y1_ref, z1_ref)
        ver1_shading_point += AllplanGeo.Point3D(x1_ref, y1_ref, z1_ref)

        ver2_shading_point += AllplanGeo.Point3D(x2_ref, y2_ref, z2_ref)
        ver2_shading_point += AllplanGeo.Point3D(x2_ref+ver_shading_offset, y2_ref-ver_shading_depth, z2_ref)
        ver2_shading_point += AllplanGeo.Point3D(x2_ref+ver_shading_offset+ver_shading_width2, y2_ref-ver_shading_depth, z2_ref)
        ver2_shading_point += AllplanGeo.Point3D(x2_ref+ver_shading_width1, y2_ref, z2_ref)
        ver2_shading_point += AllplanGeo.Point3D(x2_ref, y2_ref, z2_ref)

        ver3_shading_point += AllplanGeo.Point3D(x3_ref, y3_ref, z3_ref)
        ver3_shading_point += AllplanGeo.Point3D(x3_ref+ver_shading_offset, y3_ref-ver_shading_depth, z3_ref)
        ver3_shading_point += AllplanGeo.Point3D(x3_ref+ver_shading_offset+ver_shading_width2, y3_ref-ver_shading_depth, z3_ref)
        ver3_shading_point += AllplanGeo.Point3D(x3_ref+ver_shading_width1, y3_ref, z3_ref)
        ver3_shading_point += AllplanGeo.Point3D(x3_ref, y3_ref, z3_ref)


        ver4_shading_point += AllplanGeo.Point3D(x4_ref, y4_ref, z4_ref)
        ver4_shading_point += AllplanGeo.Point3D(x4_ref+ver_shading_offset, y4_ref-ver_shading_depth, z4_ref)
        ver4_shading_point += AllplanGeo.Point3D(x4_ref+ver_shading_offset+ver_shading_width2, y4_ref-ver_shading_depth, z4_ref)
        ver4_shading_point += AllplanGeo.Point3D(x4_ref+ver_shading_width1, y4_ref, z4_ref)
        ver4_shading_point += AllplanGeo.Point3D(x4_ref, y4_ref, z4_ref)

        if not GeometryValidate.is_valid(ver1_shading_point):
          return

        if not GeometryValidate.is_valid(ver2_shading_point):
          return

        if not GeometryValidate.is_valid(ver3_shading_point):
          return

        if not GeometryValidate.is_valid(ver4_shading_point):
          return

        ver_shading_path += AllplanGeo.Point3D(x1_ref,y1_ref,z1_ref)
        ver_shading_path += AllplanGeo.Point3D(x1_ref,y1_ref,z1_ref+self.wall_width)


        err, ver1_shading = AllplanGeo.CreatePolyhedron(ver1_shading_point, ver_shading_path)
        if not GeometryValidate.polyhedron(err):
            return

        err, ver2_shading = AllplanGeo.CreatePolyhedron(ver2_shading_point, ver_shading_path)
        if not GeometryValidate.polyhedron(err):
            return

        err, ver3_shading = AllplanGeo.CreatePolyhedron(ver3_shading_point, ver_shading_path)
        if not GeometryValidate.polyhedron(err):
            return

        err, ver4_shading = AllplanGeo.CreatePolyhedron(ver4_shading_point, ver_shading_path)
        if not GeometryValidate.polyhedron(err):
            return

        return ver1_shading, ver2_shading, ver3_shading, ver4_shading

    def create_geometry(self, build_ele):
        """
        Create the element geometries

        Args:
            build_ele:  the building element.
        """

        #----------------- Extract palette parameter values

        wall_length  = build_ele.Length1_1.value
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value

        void_active = build_ele.chkb_win.value
        door_active = build_ele.chkb_door.value

        join1_type_added = build_ele.join1_type_active.value
        join1_type_select = build_ele.join1_type.value

        join2_type_added = build_ele.join2_type_active.value
        join2_type_select = build_ele.join2_type.value

        join3_type_added = build_ele.join3_type_active.value
        join3_type_select = 1

        join4_type_added = build_ele.join4_type_active.value
        join4_type_select = 1

        upper_shading_added = build_ele.upper_shading_active.value
        lower_shading_added = build_ele.lower_shading_active.value
        shading_back_added = build_ele.upper_shading_back_active.value
        
        


        #------------------------------------ Create wall------------------------------------------#

        wall = AllplanGeo.Polyhedron3D.CreateCuboid(wall_length, wall_thickness, wall_width)
        trans_to_ref_point_1 = AllplanGeo.Matrix3D()
        trans_to_ref_point_1.Translate(AllplanGeo.Vector3D(0, 0, 0))
        wall = AllplanGeo.Transform(wall, trans_to_ref_point_1)
        

        #----------------------------Create Component Property--------------------------------------#
        com_prop_base_bodies = AllplanBaseElements.CommonProperties()
        com_prop_base_bodies.GetGlobalProperties()
        com_prop_base_bodies.Color = 1

        com_prop_stroke = AllplanBaseElements.CommonProperties()
        com_prop_stroke.GetGlobalProperties()
        com_prop_stroke.Stroke = 9 # dots
        com_prop_stroke.HelpConstruction = True

        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, wall))

        #------------------ Append Element to Wall -------------------------------------------------#
        if (void_active) :
          void = self.add_windows(build_ele, com_prop_stroke, wall_length, wall_width, wall_thickness)
          err, wall = AllplanGeo.MakeSubtraction(wall ,void)

        if (door_active) :
          door = self.add_door(build_ele, com_prop_stroke, wall_length, wall_width, wall_thickness)
          err, wall = AllplanGeo.MakeSubtraction(wall ,door)

        if (join1_type_added) :
          join1 = self.add_joins_left(build_ele, com_prop_stroke,type=join1_type_select)
          err, wall = AllplanGeo.MakeSubtraction(wall ,join1)

        if (join2_type_added) :
          join2 = self.add_joins_right(build_ele, com_prop_stroke,type=join2_type_select)
          err, wall = AllplanGeo.MakeSubtraction(wall ,join2)

        if (upper_shading_added) :
          upper_shading = self.add_upper_shading(build_ele, com_prop_stroke)
          err, wall = AllplanGeo.MakeUnion(wall ,upper_shading)

        if (lower_shading_added) :
          lower_shading = self.add_lower_shading(build_ele, com_prop_stroke)
          err, wall = AllplanGeo.MakeUnion(wall ,lower_shading)
          #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_base_bodies, lower_shading))

        if (join3_type_added) :
          upper_join = self.add_upper_join(build_ele, com_prop_stroke, type=join3_type_select)
          err, wall = AllplanGeo.MakeUnion(wall ,upper_join)

        if (join4_type_added) :
          lower_join = self.add_lower_join(build_ele, com_prop_stroke, type=join4_type_select)
          err, wall = AllplanGeo.MakeSubtraction(wall ,lower_join)

        if (shading_back_added) :
          shading_back = self.add_shading_back(build_ele, com_prop_stroke)
          err, wall = AllplanGeo.MakeUnion(wall ,shading_back)

        if (1) :
          ver1_shading,ver2_shading,ver3_shading,ver4_shading = self.add_ver_shading(build_ele, com_prop_stroke)
          err, wall = AllplanGeo.MakeUnion(wall ,ver1_shading)
          err, wall = AllplanGeo.MakeUnion(wall ,ver2_shading)
          err, wall = AllplanGeo.MakeUnion(wall ,ver3_shading)
          err, wall = AllplanGeo.MakeUnion(wall ,ver4_shading)

        #---------------------------------------Add Wall Element----------------------------------------#
        self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_base_bodies, wall))


        #-----------------------------------------------------------------------------------------------#
        #-----------------------------------------wall handle-------------------------------------------#
        #-----------------------------------------------------------------------------------------------#

        origin = AllplanGeo.Point3D(0, 0, 0)
        wall_plength = AllplanGeo.Point3D(wall_length, 0, 0)
        wall_pwidth = AllplanGeo.Point3D(0, 0, wall_width)
        wall_pthickness = AllplanGeo.Point3D(0, wall_thickness, 0)

        handle_walllength = HandleProperties("WallMoveLength",
                                   wall_plength,
                                   origin,
                                   [("Length1_1", HandleDirection.x_dir)],
                                   HandleDirection.x_dir,
                                   True)
        self.handle_list.append(handle_walllength)

        handle_wallwidth = HandleProperties("WallMoveWidth",
                                   wall_pwidth,
                                   origin,
                                   [("Width1_1", HandleDirection.z_dir)],
                                   HandleDirection.z_dir,
                                   True)
        self.handle_list.append(handle_wallwidth)

        handle_wallthickness = HandleProperties("WallMoveThickness",
                                   wall_pthickness,
                                   origin,
                                   [("Thickness1_1", HandleDirection.y_dir)],
                                   HandleDirection.y_dir,
                                   True)
        self.handle_list.append(handle_wallthickness)

