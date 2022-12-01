# DXF BEAM GENERATOR

Program służy do tworzenia obrazów wektorowych w formacie .dxf. Moduł ‘BEAM’ przeznaczony jest dla inżynierów budownictwa pomagając w generacji belek żelbetowych z otrzymanych parametrów.
Funkcje programu:
- rysowanie widoku oraz przekroju
- rysowanie prętów
- tworzenie tabeli zbrojenia
- opisy na rysunku w języku polskim, angielskim lub niemieckim
- autorski system rozkładu strzemion. Metoda ‘stirrup_spacing’

Aplikacja tworzona jest w języku Python z użyciem zewnętrznej paczki [EZDXF](https://github.com/mozman/ezdxf).

## Przykład użycia:
W pliku'main.py' ustawić należy odpowiednie wartości:

    DxfElement(
        beam_span=3000,                         - szerokość przęsła między podporami
        beam_height=500,                        - wysokość belki
        beam_width=250,                         - szerokość belki
        width_support_left=250,                 - szerokość podpory z lewej strony
        width_support_right=250                 - szerokość podpory z prawej strony
        diameter_main_top=20,                   - średnica zbrojenia głornego
        quantity_main_top=3,                    - ilość prętów zbrojenia górnego
        steel_grade_main_top='B500SP',          - klasa stali prętów górnych
        diameter_main_bottom=12,                - średnica prętów zbrojenia dolnego
        quantity_main_bottom=4,                 - ilość prętów zbrojenia dolnego
        steel_grade_main_bottom='B500SP',       - klasa stali prętów dolnych
        diameter_stirrup=8,                     - średnica strzemion
        steel_grade_stirrup='B500A',            - klasa stali strzemion
        cover_view_left=25,                     - otulina w widoku z lewej
        cover_view_right=30,                    - otulina w widoku z prawej
        cover_bottom=25,                        - otulina dolna
        cover_top=30,                           - otulina górna
        cover_left=35,                          - otulina w przekroju z lewej
        cover_right=35,                         - otulina w przekroju z prawej
        first_row_stirrup_range_left=0,         - zasięg strzemion pierwszego rzędu z lewej
        first_row_stirrup_range_right=0,        - zasięg strzemion pierwszego rzędu z prawej
        first_row_stirrup_spacing_left=110,     - rozstaw strzemion pierwszego rzedu z lewej
        first_row_stirrup_spacing_right=100,    - rozstaw strzemion pierwszego rzędu z prawej
        secondary_stirrup_spacing=400,          - rozstaw strzemion drugiego rzędu
        name="BŻ-1",                            - nazwa belki/pliku
        number_of_elements=5,                   - ilość elementów
        dxfversion: str = 'R2010',              - wersja plików dxf. POzostawić domyślne
        start_point_x: float = 0,               - punk początkowy rysunku na osi x. Pozostawic domyślne
        start_point_y: float = 0,               - punk początkowy rysunku na osi y. Pozostawic domyślne
        language='pl'                           - język opisu
        )                          



Otrzymany plik 'BŻ-1.dxf' można otworzyć przy pomocy internetowych przeglądarek plików CAD.