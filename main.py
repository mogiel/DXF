import ezdxf
import ezdxf.math
from ezdxf.tools.standards import linetypes
from math import pi, floor
from random import randrange, choice

drawing = ezdxf.new(dxfversion='R2000', setup=["linetypes"])
drawing.header['$LTSCALE'] = 50
drawing.header['$INSUNITS'] = 4
drawing.header['$MEASUREMENT'] = 1

msp = drawing.modelspace()

drawing.layers.new('KONEC-Obrys', dxfattribs={'color': 3})
drawing.layers.new('KONEC-Prety', dxfattribs={'color': 1})
drawing.layers.new('KONEC-Strzemiona', dxfattribs={'color': 6})
drawing.layers.new('KONEC-Kreskowanie', dxfattribs={'color': 7})
drawing.layers.new('KONEC-Wymiary', dxfattribs={'color': 4})
drawing.layers.new('KONEC-Przerywana', dxfattribs={'color': 8, 'linetype': 'DASHED'})

drawing.styles.new('KONEC-TEKST', dxfattribs={'font': 'Arial.ttf'})

drawing.dimstyles.new('KONEC_1_50',
                      dxfattribs={'dimjust': 0, 'dimscale': 20, 'dimblk': 'OBLIQUE', 'dimtxsty': 'KONEC-TEKST'})

srednice_prętów = (12, 16, 20, 24, 28, 32)
# rozpietoscBelki
rB = randrange(400, 6000, 50)
# wysokoscBelki
wB = randrange(200, 800, 50)
# szerokoscBelki
sB = randrange(150, 500, 50)
# szerokoscPodporyLewej
sPL = randrange(150, 500, 50)
# szerokoscPodporyPrawej
sPP = randrange(150, 500, 50)
# srednicaPretaGlownegoGornego
sPGG = choice(srednice_prętów)
# srednicaPretaGlownegoDolnego
sPGD = choice(srednice_prętów)
# średnicaStrzemienia
sS = choice((6, 8))
# otulinaGorna
oG = randrange(15, 80, 5)
# otulinaDolna
oD = randrange(15, 80, 5)
# otulinaBocznaLewa
oBL = randrange(15, 80, 5)
# otulinaBocznaPrawa
oBP = randrange(15, 80, 5)

# # rozpietoscBelki
# rB = int(input("wpisz rozpiętość belki w świetle [mm]: "))
# # wysokoscBelki
# wB = int(input("wpisz wysokoSC belki [mm]: "))
# # szerokoscBelki
# sB = int(input("wpisz szerokosc belki [mm]: "))
# # szerokoscPodporyLewej
# sPL = int(input("Wpisz szerokość podpory z lewej strony [mm]: "))
# # szerokoscPodporyPrawej
# sPP = int(input("Wpisz szerokość podpory z prawej strony [mm]: "))
# # srednicaPretaGlownegoGornego
# sPGG = int(input("Wpisz średnice prętów głównych górą [mm]: "))
# # srednicaPretaGlownegoDolnego
# sPGD = int(input("Wpisz średnice prętów głównych dołem [mm]: "))
# średnicaStrzemienia
# sS = int(input("Wpisz średnice strzemion [mm]: "))
# # otulinaGorna
# oG = int(input("Otulina górą [mm]: "))
# # otulinaDolna
# oD = int(input("Otulina dołem [mm]: "))
# # otulinaBocznaLewa
# oBL = int(input("Otulina boczną lewą [mm]: "))
# # otulinaBocznaPrawa
# oBP = int(input("Otulina boczną prawą [mm]: "))

# wyokragleniePretagornego
if sPGG <= 16:
    wPG = sPGG * 2.5
else:
    wPG = sPGG * 4.0
# strzalkaWyoblenia
sW1 = ezdxf.math.arc_to_bulge((wPG, 0), pi, pi / 2, wPG)
sW = -1 / sW1[2]
# Obrys belki
pointsObrys = [(0, 0), (sPL, 0), ((sPL + rB), 0), ((sPL + rB + sPP), 0), ((sPL + rB + sPP), wB), (0, wB)]
msp.add_lwpolyline(pointsObrys, dxfattribs={'closed': True, 'layer': 'KONEC-Obrys'})

# Geometria pręta górnego
pointsPretG = [((oBL + 0.5 * sPGG), oD, sPGG, sPGG),
               ((oBL + 0.5 * sPGG), (wB - oG - sS - 0.5 * sPGG - wPG), sPGG, sPGG, sW),
               ((oBL + 0.5 * sPGG + wPG), (wB - oG - sS - 0.5 * sPGG), sPGG, sPGG),
               ((sPL + rB + sPP - oBP - 0.5 * sPGG - wPG), (wB - oG - sS - 0.5 * sPGG), sPGG, sPGG, sW),
               ((sPL + rB + sPP - oBP - 0.5 * sPGG), (wB - oG - sS - 0.5 * sPGG - wPG), sPGG, sPGG),
               ((sPL + rB + sPP - oBP - 0.5 * sPGG), oD)]
msp.add_lwpolyline(pointsPretG, dxfattribs={'layer': 'KONEC-Prety'})
# Geometria pręta górnego
pointsPretD = [(oBL, (oD + sS + 0.5 * sPGD), sPGD, sPGD), (sPL + rB + sPP - oBP, (oD + sS + 0.5 * sPGD))]
msp.add_lwpolyline(pointsPretD, dxfattribs={'layer': 'KONEC-Prety'})

# strzemiona
# rozstawStrzemion
rS = floor(rB / 200)
# pierwszeStrzemieDrugorzedne
pSD = 0.5 * (rB - rS * 200)
for a in range(rS + 1):
    pointsStrzemie = [((sPL + pSD + a * 200), oD, sS, sS), ((sPL + pSD + a * 200), (wB - oG))]
    msp.add_lwpolyline(pointsStrzemie, dxfattribs={'layer': 'KONEC-Strzemiona'})

# podpory
wysokosc_podpory = 200
hatch = msp.add_hatch(dxfattribs={'layer': 'KONEC-Kreskowanie'})
hatch.set_pattern_fill('ANSI33', scale=20, color=-1)
hatch.paths.add_polyline_path(
    [(0, 0), (0, -wysokosc_podpory), (sPL, -wysokosc_podpory), (sPL, 0)]
)
hatch.paths.add_polyline_path(
    [(sPL + rB, 0), (sPL + rB, -wysokosc_podpory), (sPL + rB + sPP, -wysokosc_podpory), (sPL + rB + sPP, 0)]
)

punkty_podpor = (0, sPL, sPL + rB, sPL + rB + sPP)
for a in punkty_podpor:
    punkty = [(a, 0), (a, -wysokosc_podpory)]
    msp.add_lwpolyline(punkty, dxfattribs={'layer': 'KONEC-Obrys'})

linia_1 = [(0 - 200, -wysokosc_podpory), (sPL + 200, -wysokosc_podpory)]
msp.add_lwpolyline(linia_1, dxfattribs={'layer': 'KONEC-Przerywana'})
linia_2 = [(sPL + rB - 200, -wysokosc_podpory), (sPL + rB + sPP + 200, -wysokosc_podpory)]
msp.add_lwpolyline(linia_2, dxfattribs={'layer': 'KONEC-Przerywana'})

# dim = msp.add_linear_dim(base=(0, -wysokosc_podpory - 100), p1=(0, -wysokosc_podpory), p2=(sPL, -wysokosc_podpory),
#                          dimstyle='KONEC_1_50', dxfattribs={'layer': 'KONEC-Wymiary'})

dim = msp.add_multi_point_linear_dim(base=(0, -wysokosc_podpory - 100),
                                points=[(0, -wysokosc_podpory),
                                       (sPL, -wysokosc_podpory),
                                       (sPL + rB, -wysokosc_podpory),
                                       (sPL + rB + sPP, -wysokosc_podpory)],
                               dxfattribs={'layer': 'KONEC-Wymiary'},
                               dimstyle='KONEC_1_50',
                                     override={'dimscale': 20}

                               )

drawing.saveas('test.dxf')
