import math
import re
import ezdxf
import ezdxf.math
from ezdxf.tools.standards import linetypes
from math import pi, floor
from random import randrange, choice


class DxfElement:
    def __init__(self,
                 beam_span: int,
                 beam_height: int,
                 beam_width: int,
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
                 name: str = "Belka",
                 dxfversion: str = 'R2004',
                 start_point_x: int = 0,
                 start_point_y: int = 0):

        self.first_row_stirrup_spacing_right = self._is_valid_value(first_row_stirrup_spacing_right, 0, 400)
        self.first_row_stirrup_spacing_left = self._is_valid_value(first_row_stirrup_spacing_left, 0, 400)
        self.first_row_stirrup_range_right = self._is_valid_value(first_row_stirrup_range_right, 0, 15000)
        self.first_row_stirrup_range_left = self._is_valid_value(first_row_stirrup_range_left, 0, 15000)
        self.name = self._is_valid_path_name(name)
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

        self.counter = None
        self.bar = None
        self.stirrup = None
        self.hatch = None
        self.dimension = None
        self.hidden = None
        self.dim_name = None
        self.text = None

        self.dxfversion = dxfversion
        self.drawing = ezdxf.new(dxfversion=self.dxfversion, setup=["linetypes"])
        self.initial_drawing()
        self.layer_element()
        self.msp = self.drawing.modelspace()
        self.beam_outline()
        self.view_top_bar()
        self.view_bottom_bar()
        self.secondary_stirrup_spacing_min()
        self.layout_new()
        self.stirrup_spacing()
        self.supports(self.start_point_x, self.start_point_x + self.width_support_left)
        self.supports(self.start_point_x + self.width_support_left + self.beam_span,
                      self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right)
        self.save()

    """Część sprawdzająca poprawnośc danych"""

    def _is_valid_value(self, value, min_value=0, max_value=99999):
        if type(value) != int or value < min_value or value > max_value:
            raise ValueError(f"{value} max is {max_value}[m]")
        return value

    def _is_valid_value_beam(self, value, range_left, range_right, min_value=0, max_value=99999):
        if type(value) != int or value <= min_value or value > max_value or value - range_left - range_right < 0:
            raise ValueError(f"{value} max is {max_value}[m]")
        return value

    def _is_valid_path_name(self, name):
        """todo: poprawić regex, bo wywala błąd"""
        # regex = "^(?:[^/]*(?:/(?:/[^/]*/?)?)?([^?]+)(?:\??.+)?)$"
        regex = "/\\:*?\"<>|"
        if not re.match(regex, name) or name.__len__() > 20:
            raise ValueError("name is not regular expression for os")
        return name

    @staticmethod
    def bar_bending(diameter: int):
        """Obliczanie wygięcia pręta związanego ze średnicą pręta"""
        if diameter <= 16:
            return diameter * 2.5
        else:
            return diameter * 4.0

    def secondary_stirrup_spacing_min(self):
        self.secondary_stirrup_spacing = math.floor(
            min(self.secondary_stirrup_spacing, 400, (self.beam_height * 0.75)) / 5) * 5
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
                      text: str = 'KONEC-Tekst', font_text: str = 'Arial.ttf'):
        """Tworzenie warstw, styli teksty i wymiarowania"""
        self.counter = counter
        self.bar = bar
        self.stirrup = stirrup
        self.hatch = hatch
        self.dimension = dimension
        self.hidden = hidden
        self.dim_name = dim_name
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
                                               'dimtxsty': text})

    def save(self):
        """Zapisywanie do pliku"""
        print(f"Zapisuje {self.name}.dxf")
        self.drawing.saveas(f'{self.name}.dxf')

    def bar_bulge(self, diameter):
        """funkcja potrzebna aby wyliczyć promień łuku dla wyoblenia"""
        bulge = self.bar_bending(diameter)
        math_bulge = ezdxf.math.arc_to_bulge((bulge, 0), pi, pi / 2, bulge)
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

    def view_top_bar(self):
        """generowanie pręta górnego"""
        bugle = self.bar_bulge(self.diameter_main_top)
        bending = self.bar_bending(self.diameter_main_top)
        points = [((self.start_point_x + self.cover_view_left + 0.5 * self.diameter_main_top),
                   self.start_point_y + self.cover_bottom, self.diameter_main_top,
                   self.diameter_main_top),
                  ((self.start_point_x + self.cover_view_left + 0.5 * self.diameter_main_top),
                   (
                           self.start_point_y + self.beam_height - self.cover_top - self.diameter_stirrup - 0.5 * self.diameter_main_top - bending),
                   self.diameter_main_top, self.diameter_main_top, bugle),
                  ((self.start_point_x + self.cover_view_left + 0.5 * self.diameter_main_top + bending),
                   (
                           self.start_point_y + self.beam_height - self.cover_top - self.diameter_stirrup - 0.5 * self.diameter_main_top),
                   self.diameter_main_top,
                   self.diameter_main_top),
                  ((
                           self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right - self.cover_view_right - 0.5 * self.diameter_main_top - bending),
                   (
                           self.start_point_y + self.beam_height - self.cover_top - self.diameter_stirrup - 0.5 * self.diameter_main_top),
                   self.diameter_main_top,
                   self.diameter_main_top, bugle),
                  ((
                           self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right - self.cover_view_right - 0.5 * self.diameter_main_top),
                   (
                           self.start_point_y + self.beam_height - self.cover_top - self.diameter_stirrup - 0.5 * self.diameter_main_top - bending),
                   self.diameter_main_top, self.diameter_main_top),
                  ((
                           self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right - self.cover_view_right - 0.5 * self.diameter_main_top),
                   self.start_point_y + self.cover_bottom)]
        return self.msp.add_lwpolyline(points, dxfattribs={'closed': False, 'layer': self.bar})

    def view_bottom_bar(self):
        """generowanie pręta dolnego"""
        points = [((self.start_point_x + self.cover_view_left),
                   (self.start_point_y + self.cover_bottom + self.diameter_stirrup + 0.5 * self.diameter_main_bottom),
                   self.diameter_main_bottom, self.diameter_main_bottom),
                  (
                      self.start_point_x + self.width_support_left + self.beam_span + self.width_support_right - self.cover_view_right,
                      (
                              self.start_point_y + self.cover_bottom + self.diameter_stirrup + 0.5 * self.diameter_main_bottom))]
        return self.msp.add_lwpolyline(points, dxfattribs={'closed': False, 'layer': self.bar})

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
        last_stirrup_left = 0
        last_stirrup_right = 0
        localization_stirrups = []
        range_first_row = self.distance_from_supports(self.secondary_stirrup_spacing)

        while range_first_row > 60:
            self.secondary_stirrup_spacing -= 5
            range_first_row = self.distance_from_supports(self.secondary_stirrup_spacing)

        if self.first_row_stirrup_range_left != 0 and self.first_row_stirrup_spacing_left != 0:
            for i in range(int(math.ceil(self.first_row_stirrup_range_left / self.first_row_stirrup_spacing_left) + 1)):
                localization_stirrups.append(range_first_row / 2 + i * self.first_row_stirrup_spacing_left)
            last_stirrup_left = localization_stirrups[-1]

        if self.first_row_stirrup_range_right != 0 and self.first_row_stirrup_spacing_right != 0:
            for i in range(
                    int(math.ceil(self.first_row_stirrup_range_right / self.first_row_stirrup_spacing_right) + 1)):
                localization_stirrups.append(
                    self.beam_span - range_first_row / 2 - i * self.first_row_stirrup_spacing_right)
            last_stirrup_right = localization_stirrups[-1]

        for i in range(int((self.beam_span - last_stirrup_left - (
                (
                        self.beam_span - last_stirrup_right) if last_stirrup_right > 0 else 0)) / self.secondary_stirrup_spacing)):
            localization_stirrups.append((
                                             last_stirrup_left if last_stirrup_left > 0 else range_first_row / 2) + i * self.secondary_stirrup_spacing)

        localization_stirrups = list(dict.fromkeys(localization_stirrups))
        localization_stirrups.sort()
        global Number_of_stirrups_of_the_second_row
        Number_of_stirrups_of_the_second_row = math.ceil(
            (last_stirrup_right - last_stirrup_left) / self.secondary_stirrup_spacing)
        for i in localization_stirrups:
            points_stirrups = [
                ((self.width_support_left + i), self.cover_bottom, self.diameter_stirrup, self.diameter_stirrup),
                ((self.width_support_left + i), (self.beam_height - self.cover_top))]
            self.msp.add_lwpolyline(points_stirrups, dxfattribs={'layer': self.stirrup})

    def supports(self, value_left: int, value_right: int, height: int = 200):
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

        line_hidden = [(value_left - 200, self.start_point_y - height), (value_right + 200, self.start_point_y - height)]

        self.msp.add_lwpolyline(line_hidden, dxfattribs={'layer': self.hidden})



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
# draw = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1000, 0, 250, 0, 400, name="BŻ-1")
draw1 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1000, 1250, 250, 100, 400, name="BŻ-2")
# draw4 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 300, name="BŻ-21")
# draw41 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 310,
#                     name="BŻ-22")
# draw42 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 320,
#                     name="BŻ-23")
# draw43 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 330,
#                     name="BŻ-24")
# draw44 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 340,
#                     name="BŻ-25")
# draw45 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 350,
#                     name="BŻ-26")
# draw46 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1150, 1250, 250, 150, 360,
#                     name="BŻ-27")
# draw5 = DxfElement(3020, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 600, 600, 150, 150, 200, name="BŻ-22")
# draw2 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 0, 1250, 110, 100, 400, name="BŻ-3")
# draw3 = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 0, 0, 110, 100, 400, name="BŻ-4")
# draw = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35, 1000, 0, 250, 0, 400, name="BŻ-1")
# draw.initial_drawing(LTSCALE=20, INSUNITS=0)
