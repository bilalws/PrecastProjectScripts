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

print('Load wall3.py')

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
        self.wall_length2  = 860
        self.wall_angle  = 40

        self.wall_l2_x = 552.8
        self.wall_l2_y = 658.8

        self.wall_width = build_ele.Width1_1.value
        self.wall_thickness = build_ele.Thickness1_1.value

        # get windows
        self.windows_refx = build_ele.win_x.value
        self.windows_refz = build_ele.win_z.value
        self.windows_width = build_ele.win_width.value
        self.windows_length  = build_ele.win_length.value


        # get rein
        self.rein = True
        self.concrete_grade        = 4
        self.concrete_cover        = 0
        self.diameter              = 10.0
        self.bending_roller        = 4.0
        self.steel_grade           = 4
        self.distance              = 150.0
        self.mesh_type             = None

        self.start_hook            = True
        self.start_hook_angle      = AllplanGeo.Angle()
        self.end_hook              = True
        self.end_hook_angle        = AllplanGeo.Angle()


        self.distance_longbar       = 50
        self.distance_rein_shading  = 200

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
        reinforcement = []
        self.start_hook_angle.Deg = 180
        self.end_hook_angle.Deg = 180


        #reinforcement.extend( self.create_rein_shading_back() )
        reinforcement.extend( self.create_rein_wall() )

        return reinforcement

    def create_rein_shading_back(self):
        rein_shading_back = []

        return rein_shading_back

    def create_rein_wall(self):
        rein_wall = []
        rein_wall.extend( self.create_rein_ver_longbar() )
        rein_wall.extend( self.create_rein_hori_longbar() )
        rein_wall.extend( self.create_rein_ver_stirrup() )
        rein_wall.extend( self.create_rein_hori_stirrup() )
        return rein_wall

    def create_rein_ver_stirrup(self):
        rein_ver_stirrup = []
        return rein_ver_stirrup

    def create_rein_hori_stirrup(self):
        rein_hori_stirrup = []
        return rein_hori_stirrup

    def create_rein_ver_longbar(self):
        rein_ver_longbar = []

        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        x1_ref= 0
        y1_ref= 0
        z1_ref= 0

        x2_ref= 0
        y2_ref= self.wall_thickness
        z2_ref= 0

        x3_ref= 0
        y3_ref= 0
        z3_ref= 0

        x4_ref= 0
        y4_ref= self.wall_thickness
        z4_ref= 0

        x5_ref= 0
        y5_ref= 0
        z5_ref= 0

        x6_ref= 0
        y6_ref= self.wall_thickness
        z6_ref= 0

        offset_x = 0
        offset_y =20
        offset_z = 10

        ver_longbar = self.wall_width

        ver_longbar_start_point1 = AllplanGeo.Point3D(x1_ref-offset_x                 , y1_ref+offset_y   , z1_ref + offset_z)
        ver_longbar_end_point1 = AllplanGeo.Point3D(x1_ref-self.windows_refx          , y1_ref+offset_y   , z1_ref + offset_z)

        ver_longbar_start_point2 = AllplanGeo.Point3D(x2_ref-offset_x                 , y2_ref-offset_y   , z2_ref + offset_z)
        ver_longbar_end_point2 = AllplanGeo.Point3D(x2_ref-self.windows_refx          , y2_ref-offset_y   , z2_ref + offset_z)

        ver_longbar_start_point3 = AllplanGeo.Point3D(x3_ref-self.windows_refx - self.windows_length, y3_ref+offset_y, z3_ref + offset_z)
        ver_longbar_end_point3 = AllplanGeo.Point3D(x3_ref-self.wall_length                         , y3_ref+offset_y, z3_ref + offset_z)

        ver_longbar_start_point4 = AllplanGeo.Point3D(x4_ref-self.windows_refx - self.windows_length, y4_ref-offset_y, z4_ref + offset_z)
        ver_longbar_end_point4 = AllplanGeo.Point3D(x4_ref-self.wall_length                         , y4_ref-offset_y, z4_ref + offset_z)



        ver_longbar_start_point5 = AllplanGeo.Point3D(x5_ref-self.wall_length+10   , y5_ref+offset_y+10                   , z5_ref + offset_z)
        ver_longbar_end_point5 = AllplanGeo.Point3D(x5_ref-self.wall_length-self.wall_l2_x+10       , y5_ref+self.wall_l2_y + offset_y+10  , z5_ref + offset_z)

        ver_longbar_start_point6 = AllplanGeo.Point3D(x6_ref-self.wall_length+50   , y6_ref+offset_y-55                   , z6_ref + offset_z)
        ver_longbar_end_point6 = AllplanGeo.Point3D(x6_ref-self.wall_length-self.wall_l2_x+50       , y6_ref+self.wall_l2_y +offset_y-55   , z6_ref + offset_z)

        ver_longbarlongbar_angles = RotationAngles(0, -90, 0)
        ver_longbarlongbar_dist = 150

        ver_longbar_shape = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(ver_longbar,
                                                                               ver_longbarlongbar_angles,
                                                                               shape_props_longbar,
                                                                               concrete_cover_props)

        rein_ver_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, ver_longbar_shape,
                ver_longbar_start_point1,
                ver_longbar_end_point1,
                self.concrete_cover,
                self.concrete_cover,
                ver_longbarlongbar_dist) )

        rein_ver_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, ver_longbar_shape,
                ver_longbar_start_point2,
                ver_longbar_end_point2,
                self.concrete_cover,
                self.concrete_cover,
                ver_longbarlongbar_dist) )

        rein_ver_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, ver_longbar_shape,
                ver_longbar_start_point3,
                ver_longbar_end_point3,
                self.concrete_cover,
                self.concrete_cover,
                ver_longbarlongbar_dist) )

        rein_ver_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, ver_longbar_shape,
                ver_longbar_start_point4,
                ver_longbar_end_point4,
                self.concrete_cover,
                self.concrete_cover,
                ver_longbarlongbar_dist) )

        rein_ver_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, ver_longbar_shape,
                ver_longbar_start_point5,
                ver_longbar_end_point5,
                self.concrete_cover,
                self.concrete_cover,
                ver_longbarlongbar_dist) )

        rein_ver_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, ver_longbar_shape,
                ver_longbar_start_point6,
                ver_longbar_end_point6,
                self.concrete_cover,
                self.concrete_cover,
                ver_longbarlongbar_dist) )

        return rein_ver_longbar

    def create_rein_hori_longbar(self):
        rein_hori_longbar = []

        concrete_cover_props = ConcreteCoverProperties(self.concrete_cover, self.concrete_cover,
                                                       self.concrete_cover, self.concrete_cover)

        shape_props_longbar = ReinforcementShapeProperties.rebar(self.diameter, self.bending_roller,
                                                         self.steel_grade, self.concrete_grade,
                                                         AllplanReinf.BendingShapeType.LongitudinalBar)

        x1_ref= 0
        y1_ref= 0
        z1_ref= 0

        x1_2_ref= 0
        y1_2_ref= self.wall_thickness
        z1_2_ref= 0

        x2_ref= 0 -self.windows_refx - self.windows_length
        y2_ref= 0
        z2_ref= self.windows_refz

        x3_ref= 0
        y3_ref= 0
        z3_ref= 0

        offset_x = 0
        offset_y = 30
        offset_z = 10

        hori_longbar_1 = self.wall_length - 60 #60 just manualy adjust
        hori_longbar_2 = self.wall_length - self.windows_refx - self.windows_length - 60 #60 just manualy adjust
        hori_longbar_3 = self.wall_length - self.windows_refx - self.windows_length
        hori_longbar_4 = self.wall_length - self.windows_refx - self.windows_length + 20

        z_end_point_offset = 100
        hori_longbar_start_point1 = AllplanGeo.Point3D(x1_ref-offset_x      , y1_ref+offset_y   , z1_ref + offset_z)
        hori_longbar_end_point1 = AllplanGeo.Point3D(x1_ref-offset_x        , y1_ref+offset_y   , z1_ref + self.windows_refz - z_end_point_offset - offset_z)

        z1_2_offset = 20
        hori_longbar_start_point1_2 = AllplanGeo.Point3D(x1_2_ref-offset_x      , y1_2_ref-offset_y   , z1_2_ref + offset_z + z1_2_offset)
        hori_longbar_end_point1_2 = AllplanGeo.Point3D(x1_2_ref-offset_x        , y1_2_ref-offset_y   , z1_2_ref + self.windows_refz - z_end_point_offset + offset_z + z1_2_offset)

        hori_longbar_start_point2 = AllplanGeo.Point3D(x2_ref-offset_x      , y2_ref+offset_y   , z2_ref + offset_z)
        hori_longbar_end_point2 = AllplanGeo.Point3D(x2_ref-offset_x        , y2_ref+offset_y   , z2_ref + self.windows_width - offset_z)

        hori_longbar_start_point3 = AllplanGeo.Point3D(x3_ref-offset_x      , y3_ref+offset_y   , z3_ref + self.windows_refz + self.windows_width + offset_z)
        hori_longbar_end_point3 = AllplanGeo.Point3D(x3_ref-offset_x        , y3_ref+offset_y   , z3_ref + self.wall_width - offset_z)

        hori_longbar_start_point4 = AllplanGeo.Point3D(x3_ref-offset_x      , y3_ref+offset_y   , z3_ref + self.windows_refz + self.windows_width + offset_z)
        hori_longbar_end_point4 = AllplanGeo.Point3D(x3_ref-offset_x        , y3_ref+offset_y   , z3_ref + self.wall_width - offset_z)

        hori_longbar_start_poin5 = AllplanGeo.Point3D(x3_ref-offset_x      , y3_ref+offset_y   , z3_ref + self.windows_refz + self.windows_width + offset_z)
        hori_longbar_end_point5 = AllplanGeo.Point3D(x3_ref-offset_x        , y3_ref+offset_y   , z3_ref + self.wall_width - offset_z)



        hori_longbarlongbar_angles = RotationAngles(0, 0, 180)
        hori_longbarlongbar_dist = 150
        hori_longbarlongbar_dist2 = 300

        theta = 40
        end_angle = -90 + theta

        hori_longbar_shape1 = create_longitudinal_shape_with_hooks_edit(hori_longbar_1,
                                                                               hori_longbarlongbar_angles,
                                                                               shape_props_longbar,
                                                                               concrete_cover_props,
                                                                               start_hook=0,
                                                                               end_hook=self.wall_length2,
                                                                               start_angle=0,
                                                                               end_angle=end_angle)

        hori_longbar_shape1_2 = GeneralShapeBuilder.create_longitudinal_shape_with_hooks(hori_longbar_1,
                                                                               hori_longbarlongbar_angles,
                                                                               shape_props_longbar,
                                                                               concrete_cover_props)

        hori_longbar_shape2 = create_longitudinal_shape_with_hooks_edit(hori_longbar_2,
                                                                               hori_longbarlongbar_angles,
                                                                               shape_props_longbar,
                                                                               concrete_cover_props,
                                                                               start_hook=0,
                                                                               end_hook=self.wall_length2,
                                                                               start_angle=0,
                                                                               end_angle=end_angle)

        hori_longbar_shape3 = create_longitudinal_shape_with_hooks_edit(hori_longbar_3,
                                                                               hori_longbarlongbar_angles,
                                                                               shape_props_longbar,
                                                                               concrete_cover_props,
                                                                               start_hook=0,
                                                                               end_hook=self.wall_length2,
                                                                               start_angle=0,
                                                                               end_angle=end_angle)

        hori_longbar_shape4 = create_longitudinal_shape_with_hooks_edit(hori_longbar_4,
                                                                               hori_longbarlongbar_angles,
                                                                               shape_props_longbar,
                                                                               concrete_cover_props,
                                                                               start_hook=0,
                                                                               end_hook=self.wall_length2,
                                                                               start_angle=0,
                                                                               end_angle=end_angle)

        rein_hori_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, hori_longbar_shape1,
                hori_longbar_start_point1,
                hori_longbar_end_point1,
                self.concrete_cover,
                self.concrete_cover,
                hori_longbarlongbar_dist) )

        rein_hori_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, hori_longbar_shape1_2,
                hori_longbar_start_point1_2,
                hori_longbar_end_point1_2,
                self.concrete_cover,
                self.concrete_cover,
                hori_longbarlongbar_dist) )

        rein_hori_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, hori_longbar_shape2,
                hori_longbar_start_point2,
                hori_longbar_end_point2,
                self.concrete_cover,
                self.concrete_cover,
                hori_longbarlongbar_dist2) )

        rein_hori_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, hori_longbar_shape1,
                hori_longbar_start_point3,
                hori_longbar_end_point3,
                self.concrete_cover,
                self.concrete_cover,
                hori_longbarlongbar_dist) )

        rein_hori_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, hori_longbar_shape3,
                hori_longbar_start_point3,
                hori_longbar_end_point3,
                self.concrete_cover,
                self.concrete_cover,
                hori_longbarlongbar_dist) )

        rein_hori_longbar.append(LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
                1, hori_longbar_shape4,
                hori_longbar_start_point3,
                hori_longbar_end_point3,
                self.concrete_cover,
                self.concrete_cover,
                hori_longbarlongbar_dist) )

        return rein_hori_longbar


    def add_windows(self, build_ele, com_prop_stroke, wall_length, wall_width, wall_thickness):
        
        void_length  = build_ele.win_length.value
        void_width = build_ele.win_width.value
        void_thickness = wall_thickness

        p_x = build_ele.win_x.value+void_length
        p_y = 0
        p_z = build_ele.win_z.value

        void = AllplanGeo.Polyhedron3D.CreateCuboid(void_length, void_thickness, void_width)
        trans_to_ref_point_2 = AllplanGeo.Matrix3D()
        trans_to_ref_point_2.Translate(AllplanGeo.Vector3D(-p_x, p_y, p_z))
        void = AllplanGeo.Transform(void, trans_to_ref_point_2)

        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, void))

        #--------------------------------------------------------------------------------------#
        #----------------------------------Void Handle-----------------------------------------#
        #--------------------------------------------------------------------------------------#
        # origin = AllplanGeo.Point3D(0, 0, 0)

        # originwin = AllplanGeo.Point3D(-p_x, 0, p_z)
        # win_plength = AllplanGeo.Point3D(-p_x+void_length, 0, p_z)
        # win_pwidth = AllplanGeo.Point3D(-p_x, 0, p_z+void_width)
        # win_pointx = AllplanGeo.Point3D(-p_x+void_length/2, 0, p_z)
        # win_pointz = AllplanGeo.Point3D(-p_x, 0, p_z+void_width/2)

        # handle_winlength = HandleProperties("windowsMoveLength",
        #                            win_plength,
        #                            originwin,
        #                            [("win_length", HandleDirection.x_dir)],
        #                            HandleDirection.x_dir,
        #                            True)
        # self.handle_list.append(handle_winlength)

        # handle_winwidth = HandleProperties("windowsMoveWidth",
        #                            win_pwidth,
        #                            originwin,
        #                            [("win_width", HandleDirection.z_dir)],
        #                            HandleDirection.z_dir,
        #                            True)
        # self.handle_list.append(handle_winwidth)

        # handle_winx = HandleProperties("windowsMoveX",
        #                            win_pointx,
        #                            originwin,
        #                            [("win_x", HandleDirection.x_dir)],
        #                            HandleDirection.x_dir,
        #                            False)
        # self.handle_list.append(handle_winx)

        # handle_winz = HandleProperties("windowsMoveZ",
        #                            win_pointz,
        #                            origin,
        #                            [("win_z", HandleDirection.z_dir)],
        #                            HandleDirection.z_dir,
        #                            False)
        # self.handle_list.append(handle_winz)

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

        upper_join_l=build_ele.type3_length.value
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

        offset=0
        
        z_ref= windows_refz + windows_width + offset
        x_ref= -windows_refx - windows_length/2   - shading_l/2

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
        shading_l=build_ele.shading2_length.value

        windows_refx = build_ele.win_x.value
        windows_refz = build_ele.win_z.value
        windows_length  = build_ele.win_length.value
        windows_width = build_ele.win_width.value

        lower_shading_point = AllplanGeo.Polygon3D()
        lower_shading_path = AllplanGeo.Polyline3D()
        
        #offset from windows
        offset = 0

        z_ref= windows_refz - shading_t - offset
        x_ref= -windows_refx - windows_length/2    - shading_l/2

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
        

        shading_back1_point = AllplanGeo.Polygon3D()
        shading_back2_point = AllplanGeo.Polygon3D()

        shading_back_path1 = AllplanGeo.Polyline3D()
        shading_back_path2 = AllplanGeo.Polyline3D()
        
        #offset from windows
        offset_z = 0
        offset_x = 450

        shading_back_l2_x = 289.25
        shading_back_l2_y = 344.72

        x1_ref= 0
        y1_ref= wall_thickness
        z1_ref= windows_refz + windows_width + offset_z

        x2_ref= -offset_x
        #x2_ref= 0
        y2_ref= wall_thickness
        z2_ref= windows_refz + windows_width + offset_z + shading_back_h1
        

        shading_back1_point += AllplanGeo.Point3D(x1_ref, y1_ref, z1_ref)
        shading_back1_point += AllplanGeo.Point3D(x1_ref, y1_ref, z1_ref+shading_back_h1)
        shading_back1_point += AllplanGeo.Point3D(x1_ref, y1_ref+shading_back_d, z1_ref+shading_back_h1)
        shading_back1_point += AllplanGeo.Point3D(x1_ref, y1_ref+shading_back_d, z1_ref)
        shading_back1_point += AllplanGeo.Point3D(x1_ref, y1_ref, z1_ref)

        shading_back2_point += AllplanGeo.Point3D(x2_ref, y2_ref, z2_ref)
        shading_back2_point += AllplanGeo.Point3D(x2_ref, y2_ref, z2_ref+shading_back_h2)
        shading_back2_point += AllplanGeo.Point3D(x2_ref, y2_ref+shading_back_d, z2_ref+shading_back_h2)
        shading_back2_point += AllplanGeo.Point3D(x2_ref, y2_ref+shading_back_d, z2_ref)
        shading_back2_point += AllplanGeo.Point3D(x2_ref, y2_ref, z2_ref)
        

        if not GeometryValidate.is_valid(shading_back1_point):
          return

        if not GeometryValidate.is_valid(shading_back2_point):
          return

        shading_back_path1 += AllplanGeo.Point3D(0, 0, z1_ref)
        shading_back_path1 += AllplanGeo.Point3D(0-self.wall_length, 0, z1_ref)
        shading_back_path1 += AllplanGeo.Point3D(0-self.wall_length-self.wall_l2_x, 0+self.wall_l2_y, z1_ref)

        shading_back_path2 += AllplanGeo.Point3D(x2_ref, 0, z1_ref)
        shading_back_path2 += AllplanGeo.Point3D(-self.wall_length, 0, z1_ref)
        shading_back_path2 += AllplanGeo.Point3D(-self.wall_length-shading_back_l2_x, 0+shading_back_l2_y, z1_ref)


        err, shading_back1 = AllplanGeo.CreatePolyhedron(shading_back1_point, shading_back_path1)
        if not GeometryValidate.polyhedron(err):
            return
        err, shading_back2 = AllplanGeo.CreatePolyhedron(shading_back2_point, shading_back_path2)
        if not GeometryValidate.polyhedron(err):
            return

        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, shading_back))
        return shading_back1,shading_back2


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

        #wall = AllplanGeo.Polyhedron3D.CreateCuboid(wall_length, wall_thickness, wall_width)
        #trans_to_ref_point_1 = AllplanGeo.Matrix3D()
        #trans_to_ref_point_1.Translate(AllplanGeo.Vector3D(0, 0, 0))
        #wall = AllplanGeo.Transform(wall, trans_to_ref_point_1)


        wall_point = AllplanGeo.Polygon3D()
        wall_path_path = AllplanGeo.Polyline3D()

        x_ref = 0
        y_ref = 0
        z_ref = 0

        wall_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref)
        wall_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+self.wall_width)
        wall_point += AllplanGeo.Point3D(x_ref, y_ref+self.wall_thickness, z_ref+self.wall_width)
        wall_point += AllplanGeo.Point3D(x_ref, y_ref+self.wall_thickness, z_ref)
        wall_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref)

        if not GeometryValidate.is_valid(wall_point):
          return

        wall_path_path += AllplanGeo.Point3D(x_ref,y_ref,z_ref)
        wall_path_path += AllplanGeo.Point3D(x_ref-self.wall_length,y_ref,z_ref)
        wall_path_path += AllplanGeo.Point3D(x_ref-self.wall_length-self.wall_l2_x,y_ref+self.wall_l2_y,z_ref)

        err, wall = AllplanGeo.CreatePolyhedron(wall_point, wall_path_path)
        if not GeometryValidate.polyhedron(err):
            return


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

        # if (door_active) :
        #   door = self.add_door(build_ele, com_prop_stroke, wall_length, wall_width, wall_thickness)
        #   err, wall = AllplanGeo.MakeSubtraction(wall ,door)

        # if (join1_type_added) :
        #   join1 = self.add_joins_left(build_ele, com_prop_stroke,type=join1_type_select)
        #   err, wall = AllplanGeo.MakeSubtraction(wall ,join1)

        # if (join2_type_added) :
        #   join2 = self.add_joins_right(build_ele, com_prop_stroke,type=join2_type_select)
        #   err, wall = AllplanGeo.MakeSubtraction(wall ,join2)

        if (upper_shading_added) :
          upper_shading = self.add_upper_shading(build_ele, com_prop_stroke)
          err, wall = AllplanGeo.MakeUnion(wall ,upper_shading)

        if (lower_shading_added) :
          lower_shading = self.add_lower_shading(build_ele, com_prop_stroke)
          err, wall = AllplanGeo.MakeUnion(wall ,lower_shading)
          #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_base_bodies, lower_shading))

        # if (join3_type_added) :
        #   upper_join = self.add_upper_join(build_ele, com_prop_stroke, type=join3_type_select)
        #   err, wall = AllplanGeo.MakeUnion(wall ,upper_join)

        # if (join4_type_added) :
        #   lower_join = self.add_lower_join(build_ele, com_prop_stroke, type=join4_type_select)
        #   err, wall = AllplanGeo.MakeSubtraction(wall ,lower_join)

        if (shading_back_added) :
          shading_back1,shading_back2 = self.add_shading_back(build_ele, com_prop_stroke)

          err, shading_back = AllplanGeo.MakeUnion(shading_back1 ,shading_back2)
          err, wall = AllplanGeo.MakeUnion(wall ,shading_back)

        #---------------------------------------Add Wall Element----------------------------------------#
        self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_base_bodies, wall))


        #-----------------------------------------------------------------------------------------------#
        #-----------------------------------------wall handle-------------------------------------------#
        #-----------------------------------------------------------------------------------------------#

        origin = AllplanGeo.Point3D(0, 0, 0)
        wall_plength = AllplanGeo.Point3D(-wall_length, 0, 0)
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

