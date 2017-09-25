"""
Example Script for PrecastWallBKK
"""

import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import GeometryValidate as GeometryValidate

import NemAll_Python_Utility

from HandleDirection import HandleDirection
from HandleProperties import HandleProperties

from PythonPart import View2D3D, PythonPart

print('Load wall2.py')

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
        self.wall_length2  = 1000
        self.wall_width = build_ele.Width1_1.value
        self.wall_thickness = build_ele.Thickness1_1.value

        self.create_geometry(build_ele)

        views = [View2D3D (self.model_ele_list)]

        pythonpart = PythonPart ("Wall Creation",
                                 parameter_list = build_ele.get_params_list(),
                                 hash_value     = build_ele.get_hash(),
                                 python_file    = build_ele.pyp_file_name,
                                 views          = views)

        self.model_ele_list = pythonpart.create()

        return (self.model_ele_list, self.handle_list)

    def add_windows(self, build_ele, com_prop_stroke, wall_length, wall_width, wall_thickness):
        p_x = build_ele.win_x.value
        p_y = 0
        p_z = build_ele.win_z.value

        void_length  = build_ele.win_length.value
        void_width = build_ele.win_width.value
        #void_thickness = wall_thickness
        void_thickness = self.wall_length2-240

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

        self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, door))

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
        upper_join_h=build_ele.type3_height.value
        upper_join_d1=build_ele.type3_depth1.value
        upper_join_d2=build_ele.type3_depth2.value

        wall_length  = build_ele.Length1_1.value
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value


        upper_join_l=self.wall_length
        upper_join_l2=self.wall_length2

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
        #upper_join_path += AllplanGeo.Point3D(x_ref+upper_join_l,0,0)
        upper_join_path += AllplanGeo.Point3D(x_ref+upper_join_l,0,0)
        upper_join_path += AllplanGeo.Point3D(x_ref+upper_join_l,upper_join_l2,0)


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

        lower__join_l=self.wall_length
        lower__join_l2=self.wall_length2

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
        lower_join_path += AllplanGeo.Point3D(x_ref+lower__join_l,0,0)
        lower_join_path += AllplanGeo.Point3D(x_ref+lower__join_l,lower__join_l2,0)


        err, lower_join = AllplanGeo.CreatePolyhedron(lower_join_point, lower_join_path)
        if not GeometryValidate.polyhedron(err):
            return        
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, lower_join))
        return lower_join

    def add_upper_shading(self, build_ele ,com_prop_stroke) :
        #upper_shading=0

        wall_length  = build_ele.Length1_1.value
        wall_length2  = 1000

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

        offset_z=50
        offset_y=180

        z_ref= windows_refz + windows_width + offset_z
        x_ref= windows_refx + windows_length/2   - shading_l/2

        upper_shading_point += AllplanGeo.Point3D(0, 0, z_ref+0)
        upper_shading_point += AllplanGeo.Point3D(0, -shading_d, z_ref+0)
        upper_shading_point += AllplanGeo.Point3D(0, -shading_d, z_ref+shading_b)
        upper_shading_point += AllplanGeo.Point3D(0, 0, z_ref+shading_t)
        upper_shading_point += AllplanGeo.Point3D(0, 0, z_ref+0)

        if not GeometryValidate.is_valid(upper_shading_point):
          return

        upper_shading_path += AllplanGeo.Point3D(0,0,z_ref)
        #upper_shading_path += AllplanGeo.Point3D(x_ref+shading_l,0,0)
        upper_shading_path += AllplanGeo.Point3D(0+wall_length,0,z_ref)
        upper_shading_path += AllplanGeo.Point3D(0+wall_length,wall_length2-offset_y,z_ref)

        err, upper_shading = AllplanGeo.CreatePolyhedron(upper_shading_point, upper_shading_path)
        if not GeometryValidate.polyhedron(err):
            return        
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, upper_shading))
        return upper_shading

    def add_lower_shading(self, build_ele ,com_prop_stroke) :
        #lower_shading=0

        wall_length  = build_ele.Length1_1.value
        wall_length2  = 1000

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
        #x_ref= windows_refx + windows_length/2   - shading_l/2
        x_ref= windows_refx

        lower_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+0)
        lower_shading_point += AllplanGeo.Point3D(x_ref, -shading_d, z_ref+0)
        lower_shading_point += AllplanGeo.Point3D(x_ref, -shading_d, z_ref+shading_b)
        lower_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+shading_t)
        lower_shading_point += AllplanGeo.Point3D(x_ref, 0, z_ref+0)

        if not GeometryValidate.is_valid(lower_shading_point):
          return

        lower_shading_path += AllplanGeo.Point3D(x_ref,0,0)
        #lower_shading_path += AllplanGeo.Point3D(x_ref+shading_l,0,0)
        lower_shading_path += AllplanGeo.Point3D(x_ref+windows_length,0,0)
        lower_shading_path += AllplanGeo.Point3D(x_ref+windows_length,wall_length2-200,0)

        err, lower_shading = AllplanGeo.CreatePolyhedron(lower_shading_point, lower_shading_path)
        if not GeometryValidate.polyhedron(err):
            return
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, lower_shading))
        return lower_shading

    def add_shading_back(self, build_ele ,com_prop_stroke) :
        #lower_shading=0

        wall_length  = build_ele.Length1_1.value
        wall_length2  = 1000
        wall_thickness = build_ele.Thickness1_1.value

        #shading_back_l1=build_ele.shading_back_l1.value
        shading_back_l2=build_ele.shading_back_l2.value
        shading_back_h1=build_ele.shading_back_h1.value
        shading_back_h2=build_ele.shading_back_h2.value
        shading_back_d=build_ele.shading_back_depth.value

        shading_back_l1=wall_length-wall_thickness-shading_back_d

        wall_length  = build_ele.Length1_1.value
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value

        windows_refz = build_ele.win_z.value
        windows_width = build_ele.win_width.value
        

        shading_back_point = AllplanGeo.Polygon3D()
        shading_back_path = AllplanGeo.Polyline3D()
        
        #offset from windows
        offset = 50

        #x_ref= wall_length/2 - shading_back_l1/2
        #y_ref= wall_thickness
        #z_ref= windows_refz + windows_width + offset

        x_ref= 0
        y_ref= wall_thickness
        z_ref= windows_refz + windows_width + offset
        

        shading_back_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref)
        shading_back_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+shading_back_h1)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1/2 - shading_back_l2/2, y_ref, z_ref+shading_back_h1)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1/2 - shading_back_l2/2, y_ref, z_ref+shading_back_h1+shading_back_h2)
        
        #shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1/2 + shading_back_l2/2, y_ref, z_ref+shading_back_h1+shading_back_h2)
        #shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1/2 + shading_back_l2/2, y_ref, z_ref+shading_back_h1)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1, y_ref, z_ref+shading_back_h1+shading_back_h2)
        shading_back_point += AllplanGeo.Point3D(x_ref+shading_back_l1, y_ref, z_ref+shading_back_h1)

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

        x2_ref= wall_length-wall_thickness
        y2_ref= y_ref
        z2_ref= z_ref

        shading_back2_point = AllplanGeo.Polygon3D()
        shading_back2_path = AllplanGeo.Polyline3D()

        shading_back2_point += AllplanGeo.Point3D(x2_ref, y2_ref, z2_ref)
        shading_back2_point += AllplanGeo.Point3D(x2_ref, y2_ref, z2_ref+shading_back_h1)
        shading_back2_point += AllplanGeo.Point3D(x2_ref-shading_back_d, y2_ref, z2_ref+shading_back_h1)
        shading_back2_point += AllplanGeo.Point3D(x2_ref-shading_back_d, y2_ref, z2_ref)
        shading_back2_point += AllplanGeo.Point3D(x2_ref, y2_ref, z2_ref)

        if not GeometryValidate.is_valid(shading_back2_point):
          return

        shading_back2_path += AllplanGeo.Point3D(x2_ref,y2_ref,z2_ref)
        shading_back2_path += AllplanGeo.Point3D(x2_ref,y2_ref+wall_length2-shading_back_d,z2_ref)

        err, shading_back2 = AllplanGeo.CreatePolyhedron(shading_back2_point, shading_back2_path)
        if not GeometryValidate.polyhedron(err):
            return

        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, shading_back2))
        #self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop_stroke, shading_back))
        

        return shading_back , shading_back2


    def create_geometry(self, build_ele):
        """
        Create the element geometries

        Args:
            build_ele:  the building element.
        """

        #----------------- Extract palette parameter values

        wall_length  = build_ele.Length1_1.value
        wall_length2  = 1000
        wall_width = build_ele.Width1_1.value
        wall_thickness = build_ele.Thickness1_1.value

        void_active = build_ele.chkb_win.value
        door_active = build_ele.chkb_door.value

        join1_type_added = build_ele.join1_type_active.value
        join1_type_select = build_ele.join1_type.value

        join2_type_added = build_ele.join2_type_active.value
        join2_type_select = build_ele.join2_type.value

        join3_type_added = build_ele.join3_type_active.value
        join3_type_select = build_ele.join3_type.value

        join4_type_added = build_ele.join4_type_active.value
        join4_type_select = build_ele.join4_type.value

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
        wall_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref+wall_width)
        wall_point += AllplanGeo.Point3D(x_ref, y_ref+wall_thickness, z_ref+wall_width)
        wall_point += AllplanGeo.Point3D(x_ref, y_ref+wall_thickness, z_ref)
        wall_point += AllplanGeo.Point3D(x_ref, y_ref, z_ref)

        if not GeometryValidate.is_valid(wall_point):
          return

        wall_path_path += AllplanGeo.Point3D(x_ref,y_ref,z_ref)
        wall_path_path += AllplanGeo.Point3D(x_ref+wall_length,y_ref,z_ref)
        wall_path_path += AllplanGeo.Point3D(x_ref+wall_length,y_ref+wall_length2,z_ref)

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

        if (join3_type_added) :
          upper_join = self.add_upper_join(build_ele, com_prop_stroke, type=join3_type_select)
          err, wall = AllplanGeo.MakeUnion(wall ,upper_join)

        if (join4_type_added) :
          lower_join = self.add_lower_join(build_ele, com_prop_stroke, type=join4_type_select)
          err, wall = AllplanGeo.MakeSubtraction(wall ,lower_join)

        if (shading_back_added) :
          shading_back, shading_back2 = self.add_shading_back(build_ele, com_prop_stroke)

          err, wall = AllplanGeo.MakeUnion(wall ,shading_back)
          err, wall = AllplanGeo.MakeUnion(wall ,shading_back2)

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

