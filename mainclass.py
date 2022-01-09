import math

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
                 name: str = "Belka",
                 dxfversion: str = 'R2018',
                 start_point_x: int = 0,
                 start_point_y: int = 0):

        self.name = name
        self.cover_right = cover_right
        self.cover_left = cover_left
        self.diameter_main_bottom = diameter_main_bottom
        self.beam_width = beam_width
        self.cover_view_right = cover_view_right
        self.cover_top = cover_top
        self.beam_height = beam_height
        self.cover_bottom = cover_bottom
        self.cover_view_left = cover_view_left
        self.diameter_main_top = diameter_main_top
        self.diameter_stirrup = diameter_stirrup
        self.start_point_y = start_point_y
        self.start_point_x = start_point_x
        self.width_support_right = width_support_right
        self.width_support_left = width_support_left
        self.beam_span = beam_span
        self.beam_height = beam_height

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
        self.save()

    @staticmethod
    def bar_bending(diameter: int):
        """Obliczanie wygięcia pręta związanego ze średnicą pręta"""
        if diameter <= 16:
            return diameter * 2.5
        else:
            return diameter * 4.0

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


draw = DxfElement(3000, 500, 250, 250, 250, 20, 12, 8, 25, 30, 25, 30, 35, 35)
# draw.initial_drawing(LTSCALE=20, INSUNITS=0)
