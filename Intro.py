import cocos
from cocos.director import director
from cocos.scene import Scene
from cocos.sprite import Sprite
from cocos.scenes.transitions import *
from cocos.menu import *
from cocos.text import Label
import pygame
import subprocess  
import accion

class MenuIntro(Menu):
    def __init__(self):
        super().__init__("Menú principal")

        # Opciones del menú
        item_jugar = MenuItem('Jugar', self.on_jugar)
        item_opciones = MenuItem('Opciones', self.on_opciones)
        
        # Menú de dificultad
        dificultades = ['Soldado', 'Centurión', 'General', 'Pretoriano']
        self.dificultad_actual = 0
        item_dificultad = MultipleMenuItem('Dificultad: ', self.eleccion_dificultad, dificultades)

        item_salir = MenuItem('Salir', self.salir)

        self.create_menu([item_jugar, item_opciones, item_dificultad, item_salir],
                         layout_strategy=fixedPositionMenuLayout([(320, 250), (320, 200), (320, 150), (320, 100)]))

    def on_jugar(self):
        # Llamar a accion.main() para iniciar el juego
        subprocess.Popen(["python", "accion.py"])  # Ejecuta el archivo accion.py
        print("Has elegido Jugar")

    def on_opciones(self):
        print("Has elegido Opciones")

    def eleccion_dificultad(self, idx):
        self.dificultad_actual = idx
        print(f'Has elegido la dificultad: {idx + 1}')

    def salir(self):
        director.window.close()
        print('Has elegido salir')

class Capa1(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self):
        super().__init__()

        pygame.mixer.init()
        self.background_music = pygame.mixer.Sound('Epic_Music_intro.wav')
        self.background_music.play()

        window_size = director.get_window_size()

        # Cargar imagen y escalarla al tamaño de la pantalla
        mi_sprite = Sprite('Emperador.png')
        mi_sprite.scale_x = window_size[0] / mi_sprite.width
        mi_sprite.scale_y = window_size[1] / mi_sprite.height
        mi_sprite.position = window_size[0] // 2, window_size[1] // 2
        self.add(mi_sprite)

        # Texto en párrafos pequeños, distribuidos de arriba hacia abajo
        parrafos = [
            "Roma está en peligro.",
            "Después de una campaña por las tierras bárbaras.",
            "La Decimo Cuarta Legión de Roma se encuentra con algo terrible."
        ]

        # Color azul
        color_azul = (0, 0, 255, 255)

        # Posicionar cada párrafo uno debajo del otro
        for i, parrafo in enumerate(parrafos):
            texto = Label(parrafo,
                          font_size=24,
                          anchor_x='center', anchor_y='center',
                          color=color_azul,
                          position=(window_size[0] // 2, window_size[1] - 150 - i * 150))
            self.add(texto)

        self.schedule_interval(self.Cambio, 15)

    def Cambio(self, dt):
        # Cambiar CornerMoveTransition por FadeTransition o alguna otra transición
        director.replace(FadeTransition(Scene(Capa2()), duration=3))

class Capa2(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self):
        super().__init__()

        window_size = director.get_window_size()

        mi_sprite = Sprite('Marcha.png')
        mi_sprite.scale_x = window_size[0] / mi_sprite.width
        mi_sprite.scale_y = window_size[1] / mi_sprite.height
        mi_sprite.position = window_size[0] // 2, window_size[1] // 2
        self.add(mi_sprite)

        parrafos = [
           "Las tribus de Germania han formado un gran ejército.",
           "Las mil tribus, la Decimo Cuarta intenta detenerlos.",
           "La Décima Compañía de la Legión es emboscada y aniquilada.",
           "Solo queda un sobreviviente: Luis Dante."
        ]

        color_azul = (0, 0, 255, 255)

        for i, parrafo in enumerate(parrafos):
            texto = Label(parrafo,
                          font_size=24,
                          anchor_x='center', anchor_y='center',
                          color=color_azul,
                          position=(window_size[0] // 2, window_size[1] - 50 - i * 50))
            self.add(texto)

        self.schedule_interval(self.Cambio, 15)

    def Cambio(self, dt):
        director.replace(FadeTransition(Scene(Capa3()), duration=2))

class Capa3(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self):
        super().__init__()

        window_size = director.get_window_size()

        mi_sprite = Sprite('Gladiador.png')
        mi_sprite.scale_x = window_size[0] / mi_sprite.width
        mi_sprite.scale_y = window_size[1] / mi_sprite.height
        mi_sprite.position = window_size[0] // 2, window_size[1] // 2
        self.add(mi_sprite)

        parrafos = [
            "Luis Dante, el centurión de la compañía, descubre la ubicación del rey bárbaro.",
            "Osvaldo el Terrible, con poco tiempo, Dante se adentra en territorio bárbaro.",
            "Su derrota podría significar la caída de Roma."
        ]

        color_azul = (0, 0, 255, 255)

        for i, parrafo in enumerate(parrafos):
            texto = Label(parrafo,
                          font_size=24,
                          anchor_x='center', anchor_y='center',
                          color=color_azul,
                          position=(window_size[0] // 2, window_size[1] - 50 - i * 50))
            self.add(texto)

        self.schedule_interval(self.Cambio, 10)

    def Cambio(self, dt):
        director.replace(FadeTransition(Scene(Capa4()), duration=2))

class Capa4(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self):
        super().__init__()

        window_size = director.get_window_size()

        fondo = Sprite('Legion (2).png')
        fondo.scale_x = window_size[0] / fondo.width
        fondo.scale_y = window_size[1] / fondo.height
        fondo.position = window_size[0] // 2, window_size[1] // 2
        self.add(fondo)

        # Añadir el menú a la última capa
        menu_layer = MenuIntro()
        self.add(menu_layer)

if __name__ == "__main__":
    director.init(caption='Intro', fullscreen=True)
    director.run(Scene(Capa1()))
