# DXF BEAM GENERATOR

Program służy do tworzenia obrazów wektorowych w formacie .dxf. Moduł ‘BEAM’ przeznaczony jest dla inżynierów budownictwa pomagając w generacji belek żelbetowych z otrzymanych parametrów.
Funkcje programu:
- rysowanie widoku oraz przekroju
- rysowanie prętów
- tworzenie tabeli zbrojenia
- opisy na rysunku w języku polskim, angielskim lub niemieckim
- autorski system rozkładu strzemion. Metoda ‘stirrup_spacing’

Aplikacja tworzona jest w języku Python z użyciem zewnętrznej paczki [EZDXF](https://github.com/mozman/ezdxf)

## Przykład użycia:
W pliku'main.py' ustawić należy odpowiednie wartości:

    DxfElement(
        beam_span=3000,
        beam_height=500,
        beam_width=250,
        width_support_left=250,
        width_support_right=250,
        diameter_main_top=20,
        quantity_main_top=3,
        steel_grade_main_top='B500SP',
        diameter_main_bottom=12,
        quantity_main_bottom=4,
        steel_grade_main_bottom='B500SP',
        diameter_stirrup=8,
        steel_grade_stirrup='B500A',
        cover_view_left=25,
        cover_view_right=30,
        cover_bottom=25,
        cover_top=30,
        cover_left=35,
        cover_right=35,
        first_row_stirrup_range_left=0,
        first_row_stirrup_range_right=0,
        first_row_stirrup_spacing_left=110,
        first_row_stirrup_spacing_right=100,
        secondary_stirrup_spacing=400,
        name="BŻ-1",
        number_of_elements=5,
        language='pl')

Otrzymany plik 'BŻ-1.dxf' można otworzyć przy pomocy internetowych przeglądarek plików CAD.