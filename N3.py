import pyglet
from pyglet.window import key
from cocos.sprite import Sprite
from cocos.scene import Scene
from cocos.layer import ScrollableLayer, Layer, ColorLayer
from cocos.text import Label
from cocos.director import director
from cocos.tiles import load_tmx
from cocos.layer import ScrollingManager
from cocos.actions import Delay, CallFunc

# Animaciones de Dante y enemigos
animaciones_dante = {
    'idle': pyglet.image.load_animation('inactivo.gif'),
    'walk': pyglet.image.load_animation('caminar.gif'),
    'attack': pyglet.image.load_animation('movimiento.gif'),
    'hurt': pyglet.image.load_animation('Herido.gif'),
    'death': pyglet.image.load_animation('muerte.gif'),
}

animaciones_enemigos = {
    'idle': pyglet.image.load_animation('Inactivo1.gif'),
    'walk': pyglet.image.load_animation('Caminata1.gif'),
    'hurt': pyglet.image.load_animation('Herido1.gif'),
    'death': pyglet.image.load_animation('Muerte1.gif'),
}

class Dante(Sprite):
    def __init__(self, capa_colisiones, teclado, stats_layer, game_layer, health_bar):
        super().__init__(animaciones_dante['idle'])
        self.velocidad = [0, 0]
        self.vida = 3
        self.en_suelo = True
        self.teclado = teclado
        self.velocidad_salto = 250
        self.gravedad = -800
        self.ataque_activo = False
        self.stats_layer = stats_layer
        self.capa_colisiones = capa_colisiones
        self.game_layer = game_layer
        self.health_bar = health_bar
        self.actualizar_stats()

    def actualizar_stats(self):
        self.stats_layer.update_stats(self.vida)
        self.health_bar.update_bar(self.vida)


    def update(self, dt):
        # Movimiento
        if self.teclado[key.LEFT]:
            self.velocidad[0] = -200
            self.image = animaciones_dante['walk']
        elif self.teclado[key.RIGHT]:
            self.velocidad[0] = 200
            self.image = animaciones_dante['walk']
        else:
            self.velocidad[0] = 0
            if not self.ataque_activo:
                self.image = animaciones_dante['idle']

        # Salto
        if self.teclado[key.SPACE] and self.en_suelo:
            self.velocidad[1] = self.velocidad_salto
            self.en_suelo = False

        # Ataque
        if self.teclado[key.S] and not self.ataque_activo:
            self.atacar()

        # Aplicar gravedad
        if not self.en_suelo:
            self.velocidad[1] += self.gravedad * dt

        # Calcular nueva posición
        nueva_x = self.position[0] + self.velocidad[0] * dt
        nueva_y = self.position[1] + self.velocidad[1] * dt

        # Detectar colisión con el suelo o la capa de colisiones
        if nueva_y < 50 or self.detectar_colision((nueva_x, nueva_y), self.capa_colisiones):
            nueva_y = max(50, self.position[1])
            self.velocidad[1] = 0
            self.en_suelo = True

        self.position = (nueva_x, nueva_y)

    def detectar_colision(self, nueva_pos, capa):
        """Detectar colisiones con objetos en la capa especificada."""
        x, y = nueva_pos
        for obj in capa.objects:
            if obj.x <= x <= obj.x + obj.width and obj.y <= y <= obj.y + obj.height:
                return True
        return False

    def atacar(self):
        self.image = animaciones_dante['attack']
        self.ataque_activo = True

        # Programar la finalización del ataque
        self.do(Delay(0.5) + CallFunc(self.finalizar_ataque))

        # Detectar y dañar al jefe
        jefe = self.game_layer.jefe
        if self.detectar_colision_con_enemigo(jefe):
            jefe.recibir_dano()

    def detectar_colision_con_enemigo(self, enemigo):
        distancia = ((self.position[0] - enemigo.position[0])**2 + (self.position[1] - enemigo.position[1])**2) ** 0.5
        return distancia < 50  # Radio de colisión

    def finalizar_ataque(self):
        self.ataque_activo = False
        self.image = animaciones_dante['idle']

    def recibir_dano(self):
        self.vida -= 1
        self.actualizar_stats()
        self.image = animaciones_dante['hurt']
        if self.vida <= 0:
            self.morir()


    def morir(self):
        self.image = animaciones_dante['death']
        self.unschedule(self.update)
        director.replace(GameOverScene())

class Enemigo(Sprite):
    def __init__(self, position, layer, mapa_juego, escala=1.0, vida=2):
        super().__init__(animaciones_enemigos['idle'])
        self.position = position
        self.scale = escala  # Ajustar el tamaño del enemigo
        self.vida = vida
        self.vida_total = vida
        self.vivo = True
        self.layer = layer
        self.mapa_juego = mapa_juego  # Referencia al MapaJuego
        
        # Crear barra de vida roja
        self.barra_vida = ColorLayer(255, 0, 0, 255, width=100, height=10)
        self.barra_vida.position = (self.position[0] - 50, self.position[1] + 60)
        self.layer.add(self.barra_vida)


    def recibir_dano(self):
        self.vida -= 1
        self.image = animaciones_enemigos['hurt']
        self.actualizar_barra_vida()
        if self.vida <= 0:
            self.morir()
        else:
            self.do(Delay(0.5) + CallFunc(self.restaurar_idle))

    def actualizar_barra_vida(self):
        """Actualiza el ancho de la barra de vida en función de la vida restante."""
        porcentaje_vida = self.vida / self.vida_total
        self.barra_vida.width = int(100 * porcentaje_vida)

    def morir(self):
        self.image = animaciones_enemigos['death']
        self.vivo = False
        self.mapa_juego.puntuacion += 500  # Premiar con 500 puntos al derrotar al jefe
        self.do(Delay(0.5) + CallFunc(self.eliminar))
        self.layer.remove(self.barra_vida)  # Eliminar la barra de vida junto con el enemigo

    def restaurar_idle(self):
        """Restaura la animación a 'idle' después de un retraso."""
        self.image = animaciones_enemigos['idle']    

    
    def eliminar(self):
        if self in self.layer.children:
            self.layer.remove(self)

    def update(self, dt, dante):
        if self.vivo:
            distancia = ((dante.position[0] - self.position[0])**2 + (dante.position[1] - self.position[1])**2) ** 0.5
            if distancia > 10:
                dx = (dante.position[0] - self.position[0]) / distancia * 100 * dt
                dy = (dante.position[1] - self.position[1]) / distancia * 100 * dt
                self.position = (self.position[0] + dx, self.position[1] + dy)
                # Actualizar posición de la barra de vida
                self.barra_vida.position = (self.position[0] - 50, self.position[1] + 60)

class StatsLayer(Layer):
    def __init__(self):
        super().__init__()
        self.vidas_label = Label("Vidas: 3", font_size=18, color=(255, 255, 255, 255))
        self.vidas_label.position = (50, 680)
        self.add(self.vidas_label)

    def update_stats(self, vidas):
        self.vidas_label.element.text = f"Vidas: {vidas}"

class HealthBar(Layer):
    def __init__(self):
        super().__init__()
        self.bar = ColorLayer(0, 255, 0, 255, width=150, height=20)
        self.bar.position = (50, 650)
        self.add(self.bar)

    def update_bar(self, vida):
        self.bar.width = vida * 50

class NivelCompletadoScene(Scene):
    def __init__(self, puntos_totales):
        super().__init__()
        ancho, alto = director.get_window_size()

        # Mensaje de nivel completado
        nivel_completado_label = Label(
            "¡Nivel Completado!",
            font_size=50,
            anchor_x='center',
            anchor_y='center',
            color=(255, 255, 255, 255),
        )
        nivel_completado_label.position = ancho // 2, alto // 2 + 50
        self.add(nivel_completado_label)

        # Mostrar los puntos obtenidos
        puntos_label = Label(
            f"Puntos Totales: {puntos_totales}",
            font_size=30,
            anchor_x='center',
            anchor_y='center',
            color=(255, 255, 255, 255),
        )
        puntos_label.position = ancho // 2, alto // 2 - 50
        self.add(puntos_label)

class MapaJuego(Scene):
    def __init__(self, mapa_archivo):
        super().__init__()
        self.puntuacion = 0
        mapa_tmx = load_tmx(mapa_archivo)
        capa_colisiones = mapa_tmx['Capa de Objetos 1']

        self.manejador_scroll = ScrollingManager()
        self.manejador_scroll.add(mapa_tmx['Capa de patrones 1'], z=0)
        self.manejador_scroll.add(mapa_tmx['Capa de patrones 2'], z=1)
        self.manejador_scroll.add(mapa_tmx['Capa de patrones 3'], z=2)

        self.teclado = key.KeyStateHandler()
        director.window.push_handlers(self.teclado)

        self.stats_layer = StatsLayer()
        self.add(self.stats_layer)

        self.health_bar = HealthBar()
        self.add(self.health_bar)

        # Crear capa de personajes y agregar a Dante y al jefe
        self.personajes_layer = ScrollableLayer()

        # Instanciar a Dante
        self.dante = Dante(capa_colisiones, self.teclado, self.stats_layer, self, self.health_bar)
        self.dante.position = (400, 400)  # Posición inicial de Dante
        self.personajes_layer.add(self.dante)

        # Instanciar al jefe
        self.jefe = Enemigo((600, 300), self.personajes_layer, self, escala=1.5, vida=5)  # Jefe
        self.personajes_layer.add(self.jefe)

        self.manejador_scroll.add(self.personajes_layer, z=3)
        self.add(self.manejador_scroll)

        self.schedule(self.update)

    def update(self, dt):
        self.dante.update(dt)
        self.manejador_scroll.set_focus(self.dante.position[0], self.dante.position[1])

        if self.jefe.vivo:
            self.jefe.update(dt, self.dante)
        else:
            self.nivel_completado()  # Completar el nivel cuando el jefe sea derrotado



    def completar_nivel(self):
        # Cambiar a la escena de nivel completado
        director.replace(NivelCompletadoScene(self.puntuacion))

    def actualizar_enemigos(self):
        # Mostrar los próximos enemigos visibles
        if self.enemigos_visibles:
            ultimo_enemigo = self.enemigos_visibles[-1]
            indice = self.todos_enemigos.index(ultimo_enemigo) + 1
        else:
            indice = 0

        self.enemigos_visibles = self.todos_enemigos[indice:indice+2]

        for enemigo in self.enemigos_visibles:
            if enemigo not in self.personajes_layer.children:
                self.personajes_layer.add(enemigo)
        
    def nivel_completado(self):
        director.replace(NivelCompletadoScene(self.puntuacion))

class GameOverScene(Scene):
    def __init__(self):
        super().__init__()
        game_over_label = Label("GAME OVER", font_size=50, anchor_x='center', anchor_y='center')
        game_over_label.position = director.get_window_size()[0] // 2, director.get_window_size()[1] // 2
        self.add(game_over_label)

if __name__ == "__main__":
    director.init(width=800, height=700, caption="Juego de Aventuras")
    escena_principal = MapaJuego('Nivel3.tmx')
    director.run(escena_principal)