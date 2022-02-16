import math
import re
import ezdxf
import ezdxf.math

lang = 'pl'

LANG_PL = {
    'bending_schedule': 'WYKAZ ZBROJENIA',
    'mark': 'Poz.\nnr',
    'dia': 'Średnica\n%%c',
    'lenght_bar': 'Długość',
    'number_in_element': 'Liczba w\n1 elem.',
    'total_number': 'Liczba\nogólna',
    'tolat_lenght': 'Długość całkowita',
    'mass_1m': 'Masa 1m pręta',
    'mass_according_dia': 'Masa prętów wg średnic',
    'mass_total': 'Masa całkowita',
    'element:': 'Element:',
    'comments': 'Uwagi',
    'make': 'Wykonac',
    'pcs': '[szt.]',
    'mass': '[kg]',
    'lenght_m': '[m]',
    'lenght_mm': '[mm]',
}
LANG_ENG = {
    'bending_schedule': 'BENDING SCHEDULE',
    'mark': 'Mark',
    'dia': 'DIA',
}

LANG_DE = {
    'bending_schedule': 'STAHLLISTE',
    'mark': 'Pos.\nNR.',
    'dia': '%%c',
}
LANG = dict()
if lang == 'pl':
    LANG = LANG_PL
elif lang == 'eng':
    LANG = LANG_ENG
elif lang == 'de':
    LANG = LANG_DE
else:
    LANG = LANG_ENG


# from ezdxf.tools.standards import linetypes

def point_position(x0: float, y0: float, distance: float, theta: float = 60) -> tuple[float, float]:
    """theta zgodna z ruchem wskazowek zegara. godzina 12:00 to 0st, 3:00 to 90st, 6:00 to 180st, 9:00 to 270st"""
    theta_rad = math.pi / 2 - math.radians(theta)
    return x0 + distance * math.cos(theta_rad), y0 + distance * math.sin(theta_rad)


def tuple_dest(tuple_start: tuple[float, float], width: float = 0, height: float = 0) -> tuple[float, float]:
    return tuple_start[0] + width, tuple_start[1] + height


# todo: 1. przekrój. generator odstępów między prętami oraz pręty w dwóch warstwach
# todo: 3. Generacja tabel zbrojenia


class DxfElement:
    def __init__(self,
                 beam_span: float,
                 beam_height: float,
                 beam_width: float,
                 width_support_left: int,
                 width_support_right: int,
                 diameter_main_top: int,
                 diameter_main_bottom: int,
                 diameter_stirrup: int,
                 cover_view_left: int,
                 cover_view_right: int,
                 cover_bottom: int,
                 cover_top: int,
                 cover_left: int,
                 cover_right: int,
                 first_row_stirrup_range_left: int,
                 first_row_stirrup_range_right: int,
                 first_row_stirrup_spacing_left: int,
                 first_row_stirrup_spacing_right: int,
                 secondary_stirrup_spacing: int,
                 number_of_elements: int = 1,
                 name: str = "Belka",
                 dxfversion: str = 'R2018',
                 start_point_x: float = 0,
                 start_point_y: float = 0):

        self.first_row_stirrup_spacing_right = self._is_valid_value(first_row_stirrup_spacing_right, 0, 400)
        self.first_row_stirrup_spacing_left = self._is_valid_value(first_row_stirrup_spacing_left, 0, 400)
        self.first_row_stirrup_range_right = self._is_valid_value(first_row_stirrup_range_right, 0, 15000)
        self.first_row_stirrup_range_left = self._is_valid_value(first_row_stirrup_range_left, 0, 15000)
        self.name = self._is_valid_path_name(name)
        self.number_of_elements = self._is_valid_value(number_of_elements, 1, 1000)
        self.cover_right = self._is_valid_value(cover_right, 5, 100)
        self.cover_left = self._is_valid_value(cover_left, 5, 100)
        self.beam_width = self._is_valid_value(beam_width, 100, 1000)
        self.cover_top = self._is_valid_value(cover_top, 5, 100)
        self.cover_bottom = self._is_valid_value(cover_bottom, 5, 100)
        self.cover_view_right = self._is_valid_value(cover_view_right, 5, 100)
        self.cover_view_left = self._is_valid_value(cover_view_left, 5, 100)
        self.diameter_main_bottom = self._is_valid_value(diameter_main_bottom, 1, 100)
        self.diameter_main_top = self._is_valid_value(diameter_main_top, 1, 100)
        self.diameter_stirrup = self._is_valid_value(diameter_stirrup, 1, 100)
        self.start_point_y = start_point_y
        self.start_point_x = start_point_x
        self.width_support_right = self._is_valid_value(width_support_right, 50, 1000)
        self.width_support_left = self._is_valid_value(width_support_left, 50, 1000)
        self.beam_span = self._is_valid_value_beam(beam_span, first_row_stirrup_range_left,
                                                   first_row_stirrup_range_right, 300, 15000)
        self.beam_height = self._is_valid_value(beam_height, 100, 1500)

        self.secondary_stirrup_spacing = math.floor(
            min(0.75 * self.beam_height * 0.9, self._is_valid_value(secondary_stirrup_spacing, 0, 400)) / 5) * 5
        self.dimension_points = [0.0, float(self.beam_span)]
        self.number_of_stirrups_of_the_second_row = None

        self.counter = None
        self.bar = None
        self.stirrup = None
        self.hatch = None
        self.dimension = None
        self.hidden = None
        self.dim_name = None
        self.dim_name_bar = None
        self.text = None
        self.steel_bill = []
        self.count_stirrups = 0

        self.dxfversion = dxfversion
        self.drawing = ezdxf.new(dxfversion=self.dxfversion, setup=["linetypes"])
        self.initial_drawing()
        self.layer_element()
        self.msp = self.drawing.modelspace()
        self.beam_outline()
        self.view_bottom_bar()
        self.view_top_bar()
        self.view_top_bar(dimension=True, start_point_y=-2 * self.beam_height - 300)
        self.view_bottom_bar(dimension=True, start_point_y=-2 * self.beam_height - 500)
        self.view_bottom_bar(dimension=True, start_point_y=-2 * self.beam_height - 500)
        self.view_bottom_bar(dimension=True, start_point_y=-2 * self.beam_height - 500)
        self.view_bottom_bar(dimension=True, start_point_y=-2 * self.beam_height - 500)
        self.secondary_stirrup_spacing_min()
        self.layout_new()
        self.stirrup_spacing()
        self.supports(self.start_point_x, self.start_point_x + self.width_support_left)
        self.supports(self.start_point_x + self.width_support_left + self.beam_span,
                      self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right)
        self.dimension_main()
        self.dimension_stirrup()
        self.beam_section_rectangular()
        self.view_stirrups_type_2(start_point_x=5000, start_point_y=0)
        self.create_table(steel_bill=self.steel_bill)
        self.save()

    """Część sprawdzająca poprawnośc danych"""

    @staticmethod
    def _is_valid_value(value: float, min_value: float = 0, max_value: float = 99999):
        if type(value) != int or value < min_value or value > max_value:
            raise ValueError(f"{value} max is {max_value}[m]")
        return value

    @staticmethod
    def _is_valid_value_beam(value: float, range_left: float, range_right: float, min_value: float = 0,
                             max_value: float = 99999) -> float or ValueError:
        if type(value) != int or value <= min_value or value > max_value or value - range_left - range_right < 0:
            raise ValueError(f"{value} max is {max_value}[m]")
        return value

    @staticmethod
    def _is_valid_path_name(name: str) -> str or ValueError:
        """todo: poprawić regex, bo wywala błąd"""
        # regex = "^(?:[^/]*(?:/(?:/[^/]*/?)?)?([^?]+)(?:\??.+)?)$"
        regex = "/\\:*?\"<>|"
        if not re.match(regex, name) or name.__len__() > 20:
            raise ValueError("name is not regular expression for os")
        return name

    @staticmethod
    def bar_bending(diameter: float) -> float:
        """Obliczanie wygięcia pręta związanego ze średnicą pręta"""
        if diameter <= 16:
            return diameter * 2.5
        else:
            return diameter * 4.0

    @staticmethod
    def mass_1m_bar(radius: float, mass: float = 7850) -> float:
        return round(mass * math.pi * ((radius/2)/1000)**2, 3)

    def secondary_stirrup_spacing_min(self) -> float:
        self.secondary_stirrup_spacing = math.floor(
            min(self.secondary_stirrup_spacing, 400, int(self.beam_height * 0.75)) / 5) * 5
        return self.secondary_stirrup_spacing

    def initial_drawing(self, LTSCALE: int = 50, INSUNITS: int = 4, MEASUREMENT: int = 1):
        """
        Inicjalizacja pliku rysunku cad
        LTSCALE - skala rysunku powizana z liniami, default=50
        INSUNITS - jednostki rysunkowe, default=4 (mm)
        """
        self.drawing.header['$LTSCALE'] = LTSCALE
        self.drawing.header['$INSUNITS'] = INSUNITS
        self.drawing.header['$MEASUREMENT'] = MEASUREMENT
        return self.drawing

    def layer_element(self,
                      counter: str = 'KONEC-Obrys', color_counter: int = 3,
                      bar: str = 'KONEC-Prety', color_bar: int = 1,
                      stirrup: str = 'KONEC-Strzemiona', color_stirrup: int = 6,
                      hatch: str = 'KONEC-Kreskowanie', color_hatch: int = 7,
                      dimension: str = 'KONEC-Wymiary', color_dimension: int = 4,
                      hidden: str = 'KONEC-Przerywana', color_hidden: int = 8,
                      dim_name: str = 'KONEC_1_20', dim_scale: int = 20,
                      dim_name_bar: str = 'KONEC_BAR_1_20',
                      text: str = 'KONEC-Tekst', font_text: str = 'Arial.ttf'):
        """Tworzenie warstw, styli teksty i wymiarowania"""
        self.counter = counter
        self.bar = bar
        self.stirrup = stirrup
        self.hatch = hatch
        self.dimension = dimension
        self.hidden = hidden
        self.dim_name = dim_name
        self.dim_name_bar = dim_name_bar
        self.text = text

        self.drawing.layers.new(self.counter, dxfattribs={'color': color_counter})
        self.drawing.layers.new(bar, dxfattribs={'color': color_bar})
        self.drawing.layers.new(stirrup, dxfattribs={'color': color_stirrup})
        self.drawing.layers.new(hatch, dxfattribs={'color': color_hatch})
        self.drawing.layers.new(dimension, dxfattribs={'color': color_dimension})
        self.drawing.layers.new(hidden, dxfattribs={'color': color_hidden, 'linetype': 'DASHED'})
        self.drawing.styles.new(text, dxfattribs={'font': font_text})
        self.drawing.dimstyles.new(dim_name,
                                   dxfattribs={'dimjust': 0, 'dimscale': dim_scale, 'dimblk': 'OBLIQUE',
                                               'dimtxsty': text, 'dimtad': 1})
        self.drawing.dimstyles.new(dim_name_bar,
                                   dxfattribs={'dimjust': 0, 'dimscale': dim_scale, 'dimblk': 'NONE', 'dimtxsty': text,
                                               'dimtad': 1,
                                               'dimse1': 1, 'dimse2': 1, 'dimsd1': 1, 'dimsd2': 1, 'dimdle': 0})

    def save(self):
        """Zapisywanie do pliku"""
        print(f"Zapisuje {self.name}.dxf")
        self.drawing.saveas(f'{self.name}.dxf')

    def bar_bulge(self, diameter):
        """funkcja potrzebna aby wyliczyć promień łuku dla wyoblenia"""
        bulge = self.bar_bending(diameter)
        math_bulge = ezdxf.math.arc_to_bulge((bulge, 0), math.pi, math.pi / 2, bulge)
        return -1 / math_bulge[2]

    def beam_outline(self):
        """generowanie obrysu belki"""
        points = [(self.start_point_x, self.start_point_y),
                  (self.start_point_x + self.width_support_left, self.start_point_y),
                  ((self.start_point_x + self.width_support_left + self.beam_span), self.start_point_y),
                  ((self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right),
                   self.start_point_y),
                  ((self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right),
                   self.start_point_y + self.beam_height),
                  (self.start_point_x, self.start_point_y + self.beam_height)]
        return self.msp.add_lwpolyline(points, dxfattribs={'closed': True, 'layer': self.counter})

    def length_bar(self, points: list, diameter: float, angle: int = 90) -> float:
        """angle jest to kąt pod jakim zmieniają się proste"""
        arc_radius = self.bar_bending(diameter)
        total_length_bar = 0
        for i in range(len(points) - 1):
            if len(points[i]) == 5:
                total_length_bar += 2 * (angle / 360) * math.pi * arc_radius
                continue
            total_length_bar += ((points[i][0] - points[i + 1][0]) ** 2 + (points[i][1] - points[i + 1][1]) ** 2) ** 0.5
        return round(total_length_bar)

    def list_bar(self, diameter: float = None, quantity_bar: int = None, length: float = None, steel_grade: str = None,
                 name: str = None):
        self.steel_bill = [dict(t) for t in {tuple(d.items()) for d in self.steel_bill}]

        bar = {
            'name_element': self.name if name is None else self._is_valid_path_name(name),
            'number': len(self.steel_bill) + 1,
            'diameter': diameter,
            'quantity_bar': quantity_bar,
            'length': length,
            'steel_grade': steel_grade,
        }
        self.steel_bill.append(bar)
        self.steel_bill.sort(key=(lambda x: x['number']))

    def view_top_bar(self, dimension: bool = False, start_point_x: float = None, start_point_y: float = None):
        """generowanie pręta górnego"""

        if start_point_x is None:
            start_point_x = self.start_point_x
        if start_point_y is None:
            start_point_y = self.start_point_y

        bugle = self.bar_bulge(self.diameter_main_top)
        bending = self.bar_bending(self.diameter_main_top)
        points = [((start_point_x + self.cover_view_left + 0.5 * self.diameter_main_top),
                   start_point_y + self.cover_bottom, self.diameter_main_top,
                   self.diameter_main_top),
                  ((start_point_x + self.cover_view_left + 0.5 * self.diameter_main_top),
                   (
                           start_point_y + self.beam_height - self.cover_top - self.diameter_stirrup - 0.5 * self.diameter_main_top - bending),
                   self.diameter_main_top, self.diameter_main_top, bugle),
                  ((start_point_x + self.cover_view_left + 0.5 * self.diameter_main_top + bending),
                   (
                           start_point_y + self.beam_height - self.cover_top - self.diameter_stirrup - 0.5 * self.diameter_main_top),
                   self.diameter_main_top,
                   self.diameter_main_top),
                  ((
                           start_point_x + self.width_support_left + self.beam_span + self.width_support_right - self.cover_view_right - 0.5 * self.diameter_main_top - bending),
                   (
                           start_point_y + self.beam_height - self.cover_top - self.diameter_stirrup - 0.5 * self.diameter_main_top),
                   self.diameter_main_top,
                   self.diameter_main_top, bugle),
                  ((
                           start_point_x + self.width_support_left + self.beam_span + self.width_support_right - self.cover_view_right - 0.5 * self.diameter_main_top),
                   (
                           start_point_y + self.beam_height - self.cover_top - self.diameter_stirrup - 0.5 * self.diameter_main_top - bending),
                   self.diameter_main_top, self.diameter_main_top),
                  ((
                           start_point_x + self.width_support_left + self.beam_span + self.width_support_right - self.cover_view_right - 0.5 * self.diameter_main_top),
                   start_point_y + self.cover_bottom)]
        self.msp.add_lwpolyline(points, dxfattribs={'closed': False, 'layer': self.bar})

        length_bar = self.length_bar(points=points, diameter=self.diameter_main_top)

        if dimension:
            self.list_bar(diameter=self.diameter_main_top, quantity_bar=2, length=length_bar, steel_grade='B500SP')
            half = 0.5 * self.diameter_main_top
            self.dimension_generator(
                (points[0][0] - 25, points[0][1]), points[0][:2], (points[2][0], points[2][1] + half), angle=90,
                dimstyle=self.dim_name_bar
            )
            self.dimension_generator(
                (points[3][0], points[3][1] - 100), (points[1][0] - half, points[1][1]),
                (points[4][0] + half, points[4][1]), dimstyle=self.dim_name_bar
            )
            self.dimension_generator(
                (points[5][0] + 100, points[5][1]), (points[3][0], points[3][1] + half), points[5][:2], angle=90,
                dimstyle=self.dim_name_bar
            )

    def view_bottom_bar(self, dimension: bool = False, start_point_x: float = None, start_point_y: float = None):
        """generowanie pręta dolnego"""

        if start_point_x is None:
            start_point_x = self.start_point_x
        if start_point_y is None:
            start_point_y = self.start_point_y

        points = [((start_point_x + self.cover_view_left),
                   (start_point_y + self.cover_bottom + self.diameter_stirrup + 0.5 * self.diameter_main_bottom),
                   self.diameter_main_bottom, self.diameter_main_bottom),
                  (
                      start_point_x + self.width_support_left + self.beam_span + self.width_support_right - self.cover_view_right,
                      (start_point_y + self.cover_bottom + self.diameter_stirrup + 0.5 * self.diameter_main_bottom))]
        self.msp.add_lwpolyline(points, dxfattribs={'closed': False, 'layer': self.bar})

        length_bar = self.length_bar(points=points, diameter=self.diameter_main_bottom)

        if dimension:
            self.list_bar(diameter=self.diameter_main_bottom, quantity_bar=3, length=length_bar, steel_grade='B500SP')
            self.dimension_generator(
                (points[0][0], points[0][1] - 100), points[0][:2], points[1][:2], dimstyle=self.dim_name_bar
            )

    def distance_from_supports(self, distance):
        value = 0

        if self.first_row_stirrup_range_left != 0 and self.first_row_stirrup_spacing_left != 0:
            value += math.ceil(
                self.first_row_stirrup_range_left / self.first_row_stirrup_spacing_left) * self.first_row_stirrup_spacing_left
        else:
            value += 0

        if self.first_row_stirrup_range_right != 0 and self.first_row_stirrup_spacing_right != 0:
            value += math.ceil(
                self.first_row_stirrup_range_right / self.first_row_stirrup_spacing_right) * self.first_row_stirrup_spacing_right
        else:
            value += 0

        return self.beam_span - (value + math.floor((self.beam_span - value) / distance) * distance)

    def stirrup_spacing(self):
        """rozstaw strzemion w belce"""
        "todo: dokonczyc"
        last_stirrup_left: float = 0
        last_stirrup_right: float = self.beam_span
        localization_stirrups = []
        range_first_row = self.distance_from_supports(self.secondary_stirrup_spacing)

        while range_first_row > 60:
            self.secondary_stirrup_spacing -= 5
            range_first_row = self.distance_from_supports(self.secondary_stirrup_spacing)

        if self.first_row_stirrup_range_left != 0 and self.first_row_stirrup_spacing_left != 0:
            for i in range(int(math.ceil(self.first_row_stirrup_range_left / self.first_row_stirrup_spacing_left) + 1)):
                localization_stirrups.append(range_first_row / 2 + i * self.first_row_stirrup_spacing_left)
            last_stirrup_left = localization_stirrups[-1]
            self.dimension_points.append(last_stirrup_left)

        if self.first_row_stirrup_range_right != 0 and self.first_row_stirrup_spacing_right != 0:
            for i in range(
                    int(math.ceil(self.first_row_stirrup_range_right / self.first_row_stirrup_spacing_right) + 1)):
                localization_stirrups.append(
                    self.beam_span - range_first_row / 2 - i * self.first_row_stirrup_spacing_right)
            last_stirrup_right = localization_stirrups[-1]
            self.dimension_points.append(last_stirrup_right)

        self.dimension_points.append(range_first_row / 2)
        self.dimension_points.append(self.beam_span - range_first_row / 2)

        self.dimension_points = list(dict.fromkeys(self.dimension_points))
        self.dimension_points.sort()

        for i in range(int((self.beam_span - last_stirrup_left - (
                (
                        self.beam_span - last_stirrup_right) if last_stirrup_right > 0 else 0)) / self.secondary_stirrup_spacing) + 1):
            localization_stirrups.append((
                                             last_stirrup_left if last_stirrup_left > 0 else range_first_row / 2) + i * self.secondary_stirrup_spacing)

        localization_stirrups = list(dict.fromkeys(localization_stirrups))
        localization_stirrups.sort()

        self.number_of_stirrups_of_the_second_row = math.ceil(
            (last_stirrup_right - last_stirrup_left) / self.secondary_stirrup_spacing)

        for i in localization_stirrups:
            points_stirrups = [
                ((self.width_support_left + i), self.cover_bottom, self.diameter_stirrup, self.diameter_stirrup),
                ((self.width_support_left + i), (self.beam_height - self.cover_top))]
            self.msp.add_lwpolyline(points_stirrups, dxfattribs={'layer': self.stirrup})
        self.count_stirrups = len(localization_stirrups)

    def supports(self, value_left: float, value_right: float, height: int = 200):
        hatch = self.msp.add_hatch(dxfattribs={'layer': self.hatch})
        hatch.set_pattern_fill('ANSI33', scale=20, color=-1)
        hatch.paths.add_polyline_path(
            [(value_left, self.start_point_y), (value_left, self.start_point_y - height),
             (value_right, self.start_point_y - height), (value_right, self.start_point_y)]
        )

        line_point_left = [(value_left, self.start_point_y), (value_left, self.start_point_y - height)]
        line_point_right = [(value_right, self.start_point_y), (value_right, self.start_point_y - height)]

        self.msp.add_lwpolyline(line_point_left, dxfattribs={'layer': self.counter})
        self.msp.add_lwpolyline(line_point_right, dxfattribs={'layer': self.counter})

        line_hidden = [(value_left - 200, self.start_point_y - height),
                       (value_right + 200, self.start_point_y - height)]

        self.msp.add_lwpolyline(line_hidden, dxfattribs={'layer': self.hidden})

    def dimension_generator(self, base: tuple, p1: tuple, p2: tuple, angle: float = 0, text: str = "<>",
                            dimstyle=None) -> object:
        if dimstyle is None:
            dimstyle = self.dim_name
        return self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle, dimstyle=dimstyle,
                                       dxfattribs={'layer': self.dimension},
                                       text=text)

    def dimension_main(self, height: int = 400):
        self.dimension_generator(
            (self.start_point_x, self.start_point_y - height),
            (self.start_point_x, self.start_point_y - height),
            (self.start_point_x + self.width_support_left, self.start_point_y - height)
        )

        self.dimension_generator(
            (self.start_point_x, self.start_point_y - height),
            (self.start_point_x + self.width_support_left, self.start_point_y - height),
            (self.start_point_x + self.width_support_left + self.beam_span, self.start_point_y - height)
        )

        self.dimension_generator(
            (self.start_point_x, self.start_point_y - height),
            (self.start_point_x + self.width_support_left + self.beam_span, self.start_point_y - height),
            (self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right,
             self.start_point_y - height)
        )

        self.dimension_generator(
            (self.start_point_x - 200, self.start_point_y),
            (self.start_point_x, self.start_point_y),
            (self.start_point_x, self.start_point_y + self.beam_height),
            90
        )

    def dimension_stirrup(self, height: float = 300):
        value1, value2, value3, value4, value5, value6 = 0, 0, 0, 0, 0, self.beam_span
        start_end_dimension: bool = False

        if len(self.dimension_points) == 2:
            value3 = 0
            value4 = self.beam_span
            self.number_of_stirrups_of_the_second_row += 1
        elif len(
                self.dimension_points) == 3 and self.first_row_stirrup_range_left != 0 and self.first_row_stirrup_spacing_left != 0:
            value3 = 0
            value4 = self.dimension_points[1]
            value5 = self.beam_span
        elif len(
                self.dimension_points) == 3 and self.first_row_stirrup_range_right != 0 and self.first_row_stirrup_spacing_right != 0:
            value2 = 0
            value3 = self.dimension_points[1]
            value4 = self.beam_span
        elif len(self.dimension_points) == 4 and (self.dimension_points[1] - self.dimension_points[0]) > 30:
            value2 = self.dimension_points[0]
            value3 = self.dimension_points[1]
            value4 = self.dimension_points[2]
            value5 = self.dimension_points[3]
        elif len(self.dimension_points) == 4:
            value2 = self.dimension_points[1]
            value3 = self.dimension_points[1]
            value4 = self.dimension_points[2]
            value5 = self.dimension_points[2]
            start_end_dimension = True
            self.number_of_stirrups_of_the_second_row -= 1
        elif len(
                self.dimension_points) == 5 and self.first_row_stirrup_range_left != 0 and self.first_row_stirrup_spacing_left != 0:
            value2 = self.dimension_points[1]
            value3 = self.dimension_points[2]
            value4 = self.dimension_points[3]
            value5 = self.dimension_points[3]
            start_end_dimension = True
            self.number_of_stirrups_of_the_second_row -= 1
        elif len(
                self.dimension_points) == 5 and self.first_row_stirrup_range_right != 0 and self.first_row_stirrup_spacing_right != 0:
            value2 = self.dimension_points[1]
            value3 = self.dimension_points[1]
            value4 = self.dimension_points[2]
            value5 = self.dimension_points[3]
            start_end_dimension = True
            self.number_of_stirrups_of_the_second_row -= 1
        elif len(self.dimension_points) == 6:
            value2 = self.dimension_points[1]
            value3 = self.dimension_points[2]
            value4 = self.dimension_points[3]
            value5 = self.dimension_points[4]
            start_end_dimension = True
        else:
            print('error 1. Błąd generatora wumiarowania', self.dimension_points)

        if start_end_dimension:
            self.dimension_generator(
                (self.start_point_x, self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value1, self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value2, self.start_point_y - height)
            )

            self.dimension_generator(
                (self.start_point_x, self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value5, self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value6, self.start_point_y - height)
            )

        if self.first_row_stirrup_range_left != 0 and self.first_row_stirrup_spacing_left != 0:
            self.dimension_generator(
                (self.start_point_x, self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value2,
                 self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value3,
                 self.start_point_y - height),
                text=f'{math.ceil((value3 - value2) / self.first_row_stirrup_spacing_left)} x {self.first_row_stirrup_spacing_left} = <>'
            )

        if self.first_row_stirrup_range_right != 0 and self.first_row_stirrup_spacing_right != 0:
            self.dimension_generator(
                (self.start_point_x, self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value5,
                 self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value4,
                 self.start_point_y - height),
                text=f'{math.ceil((value5 - value4) / self.first_row_stirrup_spacing_right)} x {self.first_row_stirrup_spacing_right} = <>'
            )

        if self.number_of_stirrups_of_the_second_row != 0:
            self.dimension_generator(
                (self.start_point_x, self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value3,
                 self.start_point_y - height),
                (self.start_point_x + self.width_support_left + value4,
                 self.start_point_y - height),
                text=f'{math.ceil((value4 - value3) / self.number_of_stirrups_of_the_second_row)} x {self.number_of_stirrups_of_the_second_row} = <>'
            )

    def beam_section_rectangular(self, between_element: float = 500):
        start_point_x = self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right + between_element
        start_point_y = self.start_point_y

        points_beam_section = [(start_point_x, start_point_y),
                               (start_point_x + self.beam_width, start_point_y),
                               (start_point_x + self.beam_width, start_point_y + self.beam_height),
                               (start_point_x, start_point_y + self.beam_height)]

        self.msp.add_lwpolyline(points_beam_section, dxfattribs={'closed': True, 'layer': self.counter})
        self.view_stirrups_type_1(start_point_x, start_point_y)

    def view_stirrups_type_1(self, start_point_x: float, start_point_y: float, anchoring_stirrup: float = 80):

        bending_stirrup = self.bar_bending(self.diameter_stirrup)
        bending_arrow = self.bar_bulge(bending_stirrup)

        points = [
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup - bending_stirrup - anchoring_stirrup,
             self.diameter_stirrup, self.diameter_stirrup),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup - bending_stirrup,
             self.diameter_stirrup, self.diameter_stirrup, bending_arrow),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup + bending_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup, self.diameter_stirrup,
             self.diameter_stirrup),
            (start_point_x + self.beam_width - self.cover_right - 0.5 * self.diameter_stirrup - bending_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup, self.diameter_stirrup,
             self.diameter_stirrup, bending_arrow),
            (start_point_x + self.beam_width - self.cover_right - 0.5 * self.diameter_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup - bending_stirrup,
             self.diameter_stirrup, self.diameter_stirrup),
            (start_point_x + self.beam_width - self.cover_right - 0.5 * self.diameter_stirrup,
             start_point_y + self.cover_bottom + 0.5 * self.diameter_stirrup + bending_stirrup, self.diameter_stirrup,
             self.diameter_stirrup, bending_arrow),
            (start_point_x + self.beam_width - self.cover_right - 0.5 * self.diameter_stirrup - bending_stirrup,
             start_point_y + self.cover_bottom + 0.5 * self.diameter_stirrup, self.diameter_stirrup,
             self.diameter_stirrup),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup + bending_stirrup,
             start_point_y + self.cover_bottom + 0.5 * self.diameter_stirrup, self.diameter_stirrup,
             self.diameter_stirrup, bending_arrow),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup,
             start_point_y + self.cover_bottom + 0.5 * self.diameter_stirrup + bending_stirrup, self.diameter_stirrup,
             self.diameter_stirrup),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup - bending_stirrup,
             self.diameter_stirrup, self.diameter_stirrup, bending_arrow),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup + bending_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup, self.diameter_stirrup,
             self.diameter_stirrup),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup + bending_stirrup + anchoring_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup, self.diameter_stirrup,
             self.diameter_stirrup)
        ]
        length_bar = self.length_bar(points=points, diameter=self.diameter_stirrup)

        self.list_bar(diameter=self.diameter_stirrup, quantity_bar=self.count_stirrups, length=length_bar,
                      steel_grade='B500A')

        self.msp.add_lwpolyline(points, dxfattribs={'layer': self.bar})

    def view_stirrups_type_2(self, start_point_x: float, start_point_y: float, anchoring_stirrup: float = (10 * 8)):
        bending_stirrup = self.bar_bending(self.diameter_stirrup)

        theta = 60

        point_1 = point_position(start_point_x + self.cover_left + 0.5 * self.diameter_stirrup,
                                 start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup,
                                 self.beam_width - self.diameter_stirrup - self.cover_left - self.cover_right, theta)

        point_2 = point_position(point_1[0], point_1[1], bending_stirrup + anchoring_stirrup, 90 + theta)

        points = [(
            start_point_x + self.beam_width - self.cover_left - 0.5 * self.diameter_stirrup - bending_stirrup - anchoring_stirrup,
            start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup,
            self.diameter_stirrup,
            self.diameter_stirrup),
            (start_point_x + self.beam_width - self.cover_left - 0.5 * self.diameter_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup,
             self.diameter_stirrup,
             self.diameter_stirrup),
            (start_point_x + self.beam_width - self.cover_left - 0.5 * self.diameter_stirrup,
             start_point_y + self.cover_bottom + 0.5 * self.diameter_stirrup,
             self.diameter_stirrup,
             self.diameter_stirrup
             ),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup,
             start_point_y + self.cover_bottom + 0.5 * self.diameter_stirrup,
             self.diameter_stirrup,
             self.diameter_stirrup
             ),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup,
             self.diameter_stirrup,
             self.diameter_stirrup
             ),
            (start_point_x + self.cover_left + 0.5 * self.diameter_stirrup,
             start_point_y + self.beam_height - self.cover_top - 0.5 * self.diameter_stirrup,
             self.diameter_stirrup,
             self.diameter_stirrup
             ),
            (
                point_1[0],
                point_1[1],
                self.diameter_stirrup,
                self.diameter_stirrup
            ),
            (
                point_2[0],
                point_2[1],
                self.diameter_stirrup,
                self.diameter_stirrup
            )

        ]

        self.msp.add_lwpolyline(points, dxfattribs={'layer': self.bar})

        self.msp.add_linear_dim((start_point_x, start_point_y - 50),
                                (start_point_x + self.cover_left, start_point_y + self.cover_bottom), (
                                    start_point_x + self.beam_width - self.cover_right,
                                    start_point_y + self.cover_bottom), dimstyle=self.dim_name_bar,
                                dxfattribs={'layer': self.dimension}, angle=0, text='<>')
        # dimension left
        self.msp.add_linear_dim(
            (start_point_x + self.cover_left - 25, start_point_y),
            (start_point_x + self.cover_left, start_point_y + self.cover_bottom),
            (start_point_x + self.cover_left, start_point_y + self.beam_height - self.cover_top),
            dimstyle=self.dim_name_bar,
            dxfattribs={'layer': self.dimension}, angle=90, text='<>')

    # def generate_cell(self, points: list[tuple[float, float]], scale: int = 20, text: str = "__"):

    def generate_cell(self, point_top_left: tuple[float, float], width: float, height: float, scale: int = 20,
                      text: str = "__", height_text: float = 2.5, attachment_point: int = 5):

        """ MTEXT_TOP_LEFT          1
            MTEXT_TOP_CENTER        2
            MTEXT_TOP_RIGHT         3
            MTEXT_MIDDLE_LEFT       4
            MTEXT_MIDDLE_CENTER     5
            MTEXT_MIDDLE_RIGHT      6
            MTEXT_BOTTOM_LEFT       7
            MTEXT_BOTTOM_CENTER     8
            MTEXT_BOTTOM_RIGHT      9
        """

        points = [point_top_left,
                  (point_top_left[0] + width * scale, point_top_left[1]),
                  (point_top_left[0] + width * scale, point_top_left[1] - height * scale),
                  (point_top_left[0], point_top_left[1] - height * scale)]

        self.msp.add_lwpolyline(points, dxfattribs={'closed': True, 'layer': self.counter})

        if attachment_point == 5:
            location = (tuple(map(lambda x: sum(x) / float(len(x)), zip(*points[:3:2]))))
        elif attachment_point == 4:
            location = (point_top_left[0] + 1 * scale, point_top_left[1] - height / 2 * scale)
        elif attachment_point == 6:
            location = (point_top_left[0] + (width - 1) * scale, point_top_left[1] - height / 2 * scale)
        else:
            location = (tuple(map(lambda x: sum(x) / float(len(x)), zip(*points[:3:2]))))

        self.msp.add_mtext(text,
                           dxfattribs={'style': self.text,
                                       'char_height': scale * height_text,
                                       'attachment_point': attachment_point,
                                       'layer': self.counter}) \
            .set_location(location)

    def create_table(self, steel_bill: list, start_point_x: float = None, start_point_y: float = None, scale: int = 20):
        start_point_x = \
            (
                        self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right + 2000 + self.beam_width * 2) if start_point_x is None else start_point_x
        start_point_y = self.start_point_y if start_point_y is None else start_point_y

        steel_grade = {}
        for i in steel_bill:
            value_grade = i['steel_grade']
            if value_grade not in steel_grade:
                steel_grade[value_grade] = []

        for i in steel_bill:
            value_diameter = i['diameter']
            value_grade = i['steel_grade']
            for j in steel_grade:
                if value_grade == j:
                    if value_diameter not in steel_grade[value_grade]:
                        steel_grade[value_grade].append(value_diameter)

        count_column = sum(len(value) for value in steel_grade.values())
        count_row = len(steel_bill)

        column_width = [10, 15, 15, 15, 15, 15 * count_column, 20]
        row_height = [10, 5, 5, 5, 5, 5 * count_row, 5]

        start_point = (start_point_x, start_point_y)

        # title
        self.generate_cell(point_top_left=start_point, width=sum(column_width), height=row_height[0],
                           text=LANG['bending_schedule'], height_text=5)
        # header
        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:1]) * scale),
                           width=column_width[0],
                           height=sum(row_height[1:4]),
                           text=LANG['mark'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:1]) * scale,
                                                     width=sum(column_width[:1]) * scale),
                           width=column_width[1],
                           height=sum(row_height[1:3]),
                           text=LANG['dia'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:3]) * scale,
                                                     width=sum(column_width[:1]) * scale),
                           width=column_width[1],
                           height=sum(row_height[3:4]),
                           text=LANG['lenght_mm'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:1]) * scale,
                                                     width=sum(column_width[:2]) * scale),
                           width=column_width[2],
                           height=sum(row_height[1:3]),
                           text=LANG['lenght_bar'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:3]) * scale,
                                                     width=sum(column_width[:2]) * scale),
                           width=column_width[2],
                           height=sum(row_height[3:4]),
                           text=LANG['lenght_mm'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:1]) * scale,
                                                     width=sum(column_width[:3]) * scale),
                           width=column_width[3],
                           height=sum(row_height[1:3]),
                           text=LANG['number_in_element'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:3]) * scale,
                                                     width=sum(column_width[:3]) * scale),
                           width=column_width[3],
                           height=sum(row_height[3:4]),
                           text=LANG['pcs'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:1]) * scale,
                                                     width=sum(column_width[:4]) * scale),
                           width=column_width[4],
                           height=sum(row_height[1:3]),
                           text=LANG['total_number'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:3]) * scale,
                                                     width=sum(column_width[:4]) * scale),
                           width=column_width[4],
                           height=sum(row_height[3:4]),
                           text=LANG['pcs'])

        self.generate_cell(point_top_left=tuple_dest(start_point,
                                                     height=-sum(row_height[:1]) * scale,
                                                     width=sum(column_width[:5]) * scale),
                           width=column_width[5],
                           height=sum(row_height[3:4]),
                           text=LANG['tolat_lenght'])

        # nie należy tak tworzyć tablic, listy należy tworzyć przez list comprechention
        # array_bending_schedule = count_column * [count_row * [0]]

        array_bending_schedule = [['-' for i in range(count_column)] for j in range(count_row)]
        count_count_grade_value = 0

        for i in steel_grade:
            count_column_grade = column_width[5] * count_count_grade_value / count_column

            self.generate_cell(point_top_left=tuple_dest(start_point,
                                                         height=-sum(row_height[:2]) * scale,
                                                         width=(sum(column_width[:5]) + count_column_grade) * scale),
                               width=column_width[5] / count_column * len(steel_grade[i]),
                               height=sum(row_height[3:4]),
                               text=i)

            for j in range(len(steel_grade[i])):
                self.generate_cell(point_top_left=tuple_dest(start_point,
                                                             height=-sum(row_height[:3]) * scale,
                                                             width=(sum(column_width[
                                                                        :5]) + column_width[
                                                                        5] * count_count_grade_value / count_column) * scale),
                                   width=column_width[5] / count_column,
                                   height=sum(row_height[4:5]),
                                   text=f'%%c{steel_grade[i][j]}')

                for k in range(len(steel_bill)):
                    if steel_bill[k]['steel_grade'] == i and steel_bill[k]['diameter'] == steel_grade[i][j]:
                        array_bending_schedule[k][count_count_grade_value] = round(
                            steel_bill[k]['length'] / 1000 * steel_bill[k]['quantity_bar'] * self.number_of_elements, 2)

                count_count_grade_value += 1

        if column_width[6] > 0:
            self.generate_cell(point_top_left=tuple_dest(start_point,
                                                         height=-sum(row_height[:1]) * scale,
                                                         width=sum(column_width[:6]) * scale),
                               width=column_width[6],
                               height=sum(row_height[1:4]),
                               text=LANG['comments'])

        elements = []
        for i in steel_bill:
            value_element = i['name_element']
            if value_element not in elements:
                elements.append(value_element)
        elements.sort()

        for i in range(len(elements)):
            self.generate_cell(point_top_left=tuple_dest(start_point,
                                                         height=-sum(row_height[:4]) * scale),
                               width=sum(column_width[:]),
                               height=sum(row_height[4:5]),
                               attachment_point=4,
                               text=f"{LANG['element:']} {self.name}")
            self.generate_cell(point_top_left=tuple_dest(start_point,
                                                         height=-sum(row_height[:4]) * scale),
                               width=sum(column_width[:]),
                               height=sum(row_height[4:5]),
                               attachment_point=6,
                               text=f"{LANG['make']} {self.number_of_elements} {LANG['pcs']}")
            for j in range(count_row):
                self.generate_cell(point_top_left=tuple_dest(start_point,
                                                             height=-(sum(row_height[:5]) + row_height[
                                                                 5] * j / count_row) * scale),
                                   width=column_width[0],
                                   height=row_height[5] / count_row,
                                   text=steel_bill[j]['number'])

                self.generate_cell(point_top_left=tuple_dest(start_point,
                                                             height=-(sum(row_height[:5]) + row_height[
                                                                 5] * j / count_row) * scale,
                                                             width=sum(column_width[:1]) * scale),

                                   width=column_width[1],
                                   height=row_height[5] / count_row,
                                   text=f"%%c {steel_bill[j]['diameter']}")

                self.generate_cell(point_top_left=tuple_dest(start_point,
                                                             height=-(sum(row_height[:5]) + row_height[
                                                                 5] * j / count_row) * scale,
                                                             width=sum(column_width[:2]) * scale),

                                   width=column_width[2],
                                   height=row_height[5] / count_row,
                                   text=steel_bill[j]['length'])

                self.generate_cell(point_top_left=tuple_dest(start_point,
                                                             height=-(sum(row_height[:5]) + row_height[
                                                                 5] * j / count_row) * scale,
                                                             width=sum(column_width[:3]) * scale),

                                   width=column_width[3],
                                   height=row_height[5] / count_row,
                                   text=steel_bill[j]['quantity_bar'])

                self.generate_cell(point_top_left=tuple_dest(start_point,
                                                             height=-(sum(row_height[:5]) + row_height[
                                                                 5] * j / count_row) * scale,
                                                             width=sum(column_width[:4]) * scale),

                                   width=column_width[4],
                                   height=row_height[5] / count_row,
                                   text=f"{steel_bill[j]['quantity_bar'] * self.number_of_elements}")

                for k in range(count_column):
                    self.generate_cell(point_top_left=tuple_dest(start_point,
                                                                 height=-(sum(row_height[:5]) + row_height[
                                                                     5] * j / count_row) * scale,
                                                                 width=(sum(column_width[:5]) + column_width[
                                                                     5] * k / count_column) * scale),

                                       width=column_width[5] / count_column,
                                       height=row_height[5] / count_row,
                                       text=f"{array_bending_schedule[j][k]}")

                if column_width[6] > 0:
                    self.generate_cell(point_top_left=tuple_dest(start_point,
                                                                 height=-(sum(row_height[:5]) + row_height[
                                                                     5] * j / count_row) * scale,
                                                                 width=sum(column_width[:6]) * scale),
                                       width=column_width[6],
                                       height=row_height[5] / count_row,
                                       text='')
        # footer
        array_total_mass = [[0 for i in range(count_column)] if j < 3 else [] for j in range(4)]
        print(array_bending_schedule)
        # todo: zrobić generkę dla stopki
        for i in range(len(array_bending_schedule[0])):
            for j in array_bending_schedule:
                print(j)
                if type(j[i]) is not str:
                    pass


        print(array_total_mass)
        print(steel_bill)

    def layout_new(self):
        """layauty, początki"""
        name = f"{self.name}"
        if name in self.drawing.layouts:
            layout = self.drawing.layouts.get(name)
        else:
            layout = self.drawing.layouts.new(name)

        layout.page_setup(
            size=(420, 297), margins=(0.5, 0.5, 0.5, 0.5), units="mm", scale=50
        )


# testy plików
draw = DxfElement(3450, 500, 250, 250, 250, 16, 12, 8, 25, 30, 25, 30, 35, 35, 1000, 1350, 250, 125, 400, name="BŻ-3",
                  number_of_elements=4)
# draw1 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1000, 1250, 250, 100, 400, name="BŻ-2")
# draw4 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 300, name="BŻ-21")
# draw41 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 310, name="BŻ-23")
# draw5 = DxfElement(3020, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 600, 600, 150, 150, 200, name="BŻ-22")
# draw2 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 0, 1250, 110, 100, 400, name="BŻ-3")
# draw3 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 0, 0, 110, 100, 400, name="BŻ-4")
# draw31 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1000, 0, 250, 0, 400, name="BŻ-5")
# draw.initial_drawing(LTSCALE=20, INSUNITS=0)
