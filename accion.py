import pyglet
from pyglet.window import key
from cocos.sprite import Sprite
from cocos.scene import Scene
from cocos.layer import ScrollableLayer, Layer, ColorLayer
from cocos.text import Label
from cocos.director import director
from cocos.tiles import load_tmx
from cocos.layer import ScrollingManager
import cocos
from pyglet.window import mouse

# Animaciones de Dante y enemigos
animaciones_dante = {
    'idle': pyglet.image.load_animation('inactivo.gif'),
    'walk': pyglet.image.load_animation('caminar.gif'),
    'attack': pyglet.image.load_animation('movimiento.gif'),
    'hurt': pyglet.image.load_animation('Herido.gif'),
    'death': pyglet.image.load_animation('muerte.gif')
}

animaciones_enemigos = {
    'idle': pyglet.image.load_animation('Inactivo1.gif'), 
    'walk': pyglet.image.load_animation('Caminata1.gif'),
    'attack': pyglet.image.load_animation('Golpe1.gif'),
    'hurt': pyglet.image.load_animation('Herido1.gif'),
    'death': pyglet.image.load_animation('Muerte1.gif')
}



class Dante(Sprite):
    def __init__(self, capa_terreno, capa_colisiones, teclado, stats_layer):
        super().__init__(animaciones_dante['idle'])
        self.velocidad = [0, 0]
        self.vida = 3
        self.en_suelo = True
        self.teclado = teclado
        self.velocidad_salto = 250
        self.gravedad = -800
        self.ataque_activo = False
        self.stats_layer = stats_layer
        self.puntos = 0
        self.golpes_recibidos = 0  # Nuevo contador de golpes
        self.actualizar_stats()
        self.capa_terreno = capa_terreno
        self.capa_colisiones = capa_colisiones
        self.limite_izquierdo = 50
        self.limite_derecho = 1200

    def actualizar_stats(self):
        self.stats_layer.update_stats(self.vida, self.puntos)

    def update(self, dt):
        # Movimiento horizontal
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
        else:
            self.ataque_activo = False

        # Aplicar gravedad solo si no está en el suelo
        if not self.en_suelo:
            self.velocidad[1] += self.gravedad * dt


       # Actualizar posición
        nueva_x = self.position[0] + self.velocidad[0] * dt
        nueva_y = self.position[1] + self.velocidad[1] * dt

        # Limitar la posición de Dante en el mapa
        if nueva_x < self.limite_izquierdo:
            nueva_x = self.limite_izquierdo
        elif nueva_x > self.limite_derecho:
            nueva_x = self.limite_derecho

        if nueva_y < 50:
            nueva_y = 50
            self.en_suelo = True
            self.velocidad[1] = 0


        # Detectar colisión con capa de colisiones
        if self.detectar_colision((nueva_x, nueva_y)):
            nueva_y = self.position[1]
            self.velocidad[1] = 0
            self.en_suelo = True

        self.position = (nueva_x, nueva_y)

    def detectar_colision(self, nueva_pos):
        x, y = nueva_pos
        for obj in self.capa_colisiones.objects:
            if obj.x <= x <= obj.x + obj.width and obj.y <= y <= obj.y + obj.height:
                return True
        return False

    def atacar(self):
        self.image = animaciones_dante['attack']
        self.ataque_activo = True
        self.verificar_ataque()  

    def verificar_ataque(self):
       if hasattr(self.parent, 'enemigos'):  
        for enemigo in self.parent.enemigos:  
            if self.enemigo_en_rango(enemigo):  
                enemigo.recibir_dano()

    def enemigo_en_rango(self, enemigo):
        # Detecta si un enemigo está cerca (en rango de ataque)
        distancia_x = abs(self.position[0] - enemigo.position[0])
        distancia_y = abs(self.position[1] - enemigo.position[1])
        return distancia_x < 50 and distancia_y < 50  # Rango de proximidad para atacar
    
    def recibir_dano(self):
        self.golpes_recibidos += 1  # Incrementa el contador de golpes recibidos
        if self.golpes_recibidos >= 3:  # Si ha recibido 3 golpes, pierde una vida
            self.vida -= 1
            self.golpes_recibidos = 0  # Reinicia el contador de golpes
            self.image = animaciones_dante['hurt']
            self.actualizar_stats()
            if self.vida <= 0:
                self.morir()

    def morir(self):
        self.image = animaciones_dante['death']
        self.unschedule(self.update)
        director.replace(GameOverScene())


class Enemigo(Sprite):
    def __init__(self, position, dante, stats_layer, numero):
        super().__init__(animaciones_enemigos['idle'])  # Animación inicial de inactividad
        self.position = position
        self.dante = dante
        self.stats_layer = stats_layer
        self.numero = numero
        self.velocidad = 80  # Velocidad de movimiento hacia Dante (ajusta este valor según prefieras)
        self.vida = 3
        self.en_persecucion = False

    def perseguir_dante(self, dt):
        # Calcular la dirección hacia Dante
        direccion_x = self.dante.position[0] - self.position[0]
        direccion_y = self.dante.position[1] - self.position[1]

        # Calcular la distancia y normalizar la dirección
        distancia = (direccion_x**2 + direccion_y**2) ** 0.5
        if distancia > 0:
            direccion_x /= distancia
            direccion_y /= distancia

        # Aplicar movimiento hacia Dante
        nueva_x = self.position[0] + direccion_x * self.velocidad * dt
        nueva_y = self.position[1] + direccion_y * self.velocidad * dt
        self.position = (nueva_x, nueva_y)
        
        
        self.image = animaciones_enemigos['walk']
    
    def update(self, dt):
        # Siempre persigue a Dante
        self.perseguir_dante(dt)
        # Ejecuta la persecución si está activada
        if self.en_persecucion:
            self.perseguir_dante(dt)
        else:
            self.image = animaciones_enemigos['idle']  

    

    



    def update(self, dt):
        distancia_dante = abs(self.dante.position[0] - self.position[0])
        if distancia_dante < 50 and not self.attacking:
            self.atacar()
        elif distancia_dante >= 50:
            self.attacking = False
            self.image = animaciones_enemigos['walk']

    def atacar(self):
     if self.vida > 0:
        self.attacking = True
        self.image = animaciones_enemigos['attack']
        self.dante.recibir_dano()  # Dante recibe un golpe

    def recibir_dano(self):
     if self.vida > 0:
        self.vida -= 1
        self.image = animaciones_enemigos['hurt']
        if self.vida <= 0:
            self.eliminar()

    def eliminar(self):
     if self.vida <= 0:  # Verificar que la vida es cero antes de reproducir la animación de muerte
        self.image = animaciones_enemigos['death']
        self.unschedule(self.update)
        self.parent.remove(self)  # Elimina el enemigo de la capa de personajes
        self.stats_layer.update_points(100, self.numero)

class StatsLayer(Layer):
    def __init__(self):
        super().__init__()
        self.vidas_label = Label("Vidas: 3", font_size=18, color=(255, 255, 255, 255), anchor_x='center', anchor_y='top')
        self.vidas_label.position = (100, 700)
        self.puntos_label = Label("Puntos: 0", font_size=18, color=(255, 255, 255, 255), anchor_x='center', anchor_y='top')
        self.puntos_label.position = (200, 700)
        self.add(self.vidas_label)
        self.add(self.puntos_label)
        self.enemigos_derrotados = 0

    def update_stats(self, vidas, puntos):
        self.vidas_label.element.text = f"Vidas: {vidas}"
        self.puntos_label.element.text = f"Puntos: {puntos}"

    def update_points(self, puntos, numero_enemigo):
        self.enemigos_derrotados += 1
        if self.enemigos_derrotados == 3:
            # Cambiar a la escena de victoria y cargar el siguiente nivel
            director.replace(VictoryScene(siguiente_nivel='Nivel2.tmx'))
        else:
            if hasattr(self.parent.parent, 'spawn_next_enemy'):
                self.parent.parent.spawn_next_enemy(numero_enemigo + 1)

class GameOverScene(Scene):
    def __init__(self):
        super().__init__()
        layer = ColorLayer(0, 0, 0, 255)
        label = Label('Game Over', font_size=52, anchor_x='center', anchor_y='center')
        label.position = (640, 360)
        layer.add(label)
        self.add(layer)

class VictoryScene(Scene):
    def __init__(self, siguiente_nivel):
        super().__init__()
        self.siguiente_nivel = siguiente_nivel  # Guardar el nivel que se cargará

        # Crear el fondo de la escena
        fondo = ColorLayer(0, 0, 0, 255)
        self.add(fondo)

        # Título de la escena
        titulo = Label('¡Nivel Completado!', font_size=52, anchor_x='center', anchor_y='center', color=(255, 255, 255, 255))
        titulo.position = (640, 360)
        fondo.add(titulo)

        # Botón "Continuar"
        self.continuar_label = Label('Continuar', font_size=36, anchor_x='center', anchor_y='center', color=(0, 255, 0, 255))
        self.continuar_label.position = (640, 300)
        fondo.add(self.continuar_label)

        # Hacer que este layer sea interactivo
        self.interactivo = InteractiveLayer(self.continuar_label, self.ir_al_siguiente_nivel)
        self.add(self.interactivo)


    def ir_al_siguiente_nivel(self):
        cargar_nivel(self.siguiente_nivel)

class InteractiveLayer(Layer):
    is_event_handler = True  # Permitir que esta capa maneje eventos

    def __init__(self, label, callback):
        super().__init__()
        self.label = label
        self.callback = callback

    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & mouse.LEFT:  # Verificar si es clic izquierdo
            # Verificar si el clic está dentro del área del label
            x_min = self.label.x - self.label.element.content_width / 2
            x_max = self.label.x + self.label.element.content_width / 2
            y_min = self.label.y - self.label.element.content_height / 2
            y_max = self.label.y + self.label.element.content_height / 2

            if x_min <= x <= x_max and y_min <= y <= y_max:
                self.callback()  # Llamar al callback asociado

class PersonajesLayer(ScrollableLayer):
    def __init__(self, dante, enemigos):
        super().__init__()
        self.dante = dante
        self.enemigos = enemigos  # Almacena la lista de enemigos
        self.add(dante)
        for enemigo in self.enemigos:
            self.add(enemigo)
            enemigo.schedule(enemigo.update)  

def cargar_nivel(mapa_archivo, siguiente_nivel=None):
    escena = MapaJuego(mapa_archivo, siguiente_nivel)
    director.replace(escena)          
   
   

class MapaJuego(Scene):
    def __init__(self, mapa_archivo, siguiente_nivel=None):
        super().__init__()
        self.siguiente_nivel = siguiente_nivel
        mapa_tmx = load_tmx(mapa_archivo)
        
        # Cargar las capas de acuerdo con la nueva configuración
        capa_fondo = mapa_tmx['Capa de patrones 1']    # El fondo del mapa
        capa_terreno_1 = mapa_tmx['Capa de patrones 2']  # Primer terreno
        capa_terreno_2 = mapa_tmx['Capa de patrones 3']  # Segundo terreno
        capa_colisiones = mapa_tmx['Capa de Objetos 1']  # Capa de objetos y colisiones

        # Crear el manejador de scroll y agregar las capas en orden
        self.manejador_scroll = ScrollingManager()
        self.manejador_scroll.add(capa_fondo, z=0)       # Capa de fondo
        self.manejador_scroll.add(capa_terreno_1, z=1)   # Primer terreno
        self.manejador_scroll.add(capa_terreno_2, z=2)   # Segundo terreno
        self.manejador_scroll.add(capa_colisiones, z=3)  # Capa de colisiones

        # Configurar el teclado
        self.teclado = key.KeyStateHandler()
        director.window.push_handlers(self.teclado)

        # Crear y agregar la capa de estadísticas
        self.stats_layer = StatsLayer()
        self.add(self.stats_layer)

        # Crear a Dante y establecer su posición inicial
        self.dante = Dante(capa_terreno_1, capa_colisiones, self.teclado, self.stats_layer)
        self.dante.position = (100, 300)  

        # Crear enemigos y establecer sus posiciones
        self.enemigos = [
            Enemigo((680, 300), self.dante, self.stats_layer, numero=0),
            Enemigo((740, 300), self.dante, self.stats_layer, numero=1),
            Enemigo((800, 300), self.dante, self.stats_layer, numero=2)
        ]

        # Crear la capa de personajes y agregarla al manejador de scroll
        self.personajes_layer = PersonajesLayer(self.dante, self.enemigos)
        self.manejador_scroll.add(self.personajes_layer, z=4)  # Capa de personajes encima de las demás

        # Agregar el manejador de scroll a la escena
        self.add(self.manejador_scroll)
        self.schedule(self.update)

    def update(self, dt):
        self.dante.update(dt)
        self.manejador_scroll.set_focus(self.dante.position[0], self.dante.position[1])

    def spawn_next_enemy(self, numero):
        if numero < len(self.enemigos):
            enemigo = self.enemigos[numero]
            self.personajes_layer.add(enemigo)
            enemigo.schedule(enemigo.update)

    

if __name__ == '__main__':
    director.init(width=1280, height=720)
    escena = MapaJuego('Nivel1.tmx')
    director.run(escena)