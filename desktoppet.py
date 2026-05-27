import tkinter as tk
from tkinter import Menu, messagebox
import random
import json
import sys
import os
from PIL import Image, ImageTk, ImageOps
from screeninfo import get_monitors
import pygame
import math
import time
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class DesktopPetAnimator:
    """Clase dedicada exclusivamente a gestionar los fotogramas dinámicos de animación."""
    def __init__(self, canvas_widget, config_img, size_idle, size_walk):
        self.canvas = canvas_widget
        self.current_frame_index = 0
        self.last_state = None
        self.is_facing_right = True
        self.tk_image_ref = None
        
        # EL NÚCLEO DEL RELOJ: Registramos el momento exacto de nacimiento
        self.last_frame_time = time.time()

        self.invertir_eje_x = config_img.get("invertir_eje_x", False)
        self.idle_is_animated = config_img.get("idle_is_animated", False)
        self.directional_walk = config_img.get("directional_walk", False)
        self.fijar_direccion_reposo = config_img.get("fijar_direccion_reposo", False)

        filtro_escalado = Image.Resampling.NEAREST 

        def limpiar_alfa(imagen):
            img = imagen.convert("RGBA")
            r, g, b, a = img.split()
            a = a.point(lambda p: 255 if p > 127 else 0) 
            return Image.merge("RGBA", (r, g, b, a))

        try:
            # 1. Cargar animación de REPOSO
            if self.idle_is_animated:
                self.frames_idle = []
                pref_idle = config_img.get("idle_prefix", "idle_")
                suf_idle = config_img.get("idle_suffix", ".png")
                num_idle = config_img.get("idle_frames", 4)
                for i in range(num_idle):
                    raw_frame = limpiar_alfa(Image.open(f"{pref_idle}{i}{suf_idle}"))
                    self.frames_idle.append(raw_frame.resize(size_idle, filtro_escalado))
            else:
                img_idle_path = config_img.get("idle", "quieto.png")
                raw_idle = limpiar_alfa(Image.open(img_idle_path))
                self.img_idle = raw_idle.resize(size_idle, filtro_escalado)
            
            # 2. Cargar animación de CAMINATA (Direccional o Simétrica)
            sufijo = config_img.get("walk_suffix", ".png")
            if self.directional_walk:
                self.frames_walk_right = []
                pref_r = config_img.get("walk_right_prefix", "walk_r_")
                num_r = config_img.get("walk_right_frames", 10)
                for i in range(num_r):
                    raw_frame = limpiar_alfa(Image.open(f"{pref_r}{i}{sufijo}"))
                    self.frames_walk_right.append(raw_frame.resize(size_walk, filtro_escalado))

                self.frames_walk_left = []
                pref_l = config_img.get("walk_left_prefix", "walk_l_")
                num_l = config_img.get("walk_left_frames", 10)
                for i in range(num_l):
                    raw_frame = limpiar_alfa(Image.open(f"{pref_l}{i}{sufijo}"))
                    self.frames_walk_left.append(raw_frame.resize(size_walk, filtro_escalado))
            else:
                self.frames_walk = []
                prefijo = config_img.get("walk_prefix", "frame")
                num_frames = config_img.get("walk_frames", 10)
                for i in range(num_frames):
                    raw_frame = limpiar_alfa(Image.open(f"{prefijo}{i}{sufijo}"))
                    self.frames_walk.append(raw_frame.resize(size_walk, filtro_escalado))
                
        except FileNotFoundError as e:
            tk.Tk().withdraw()
            messagebox.showerror("Error Crítico de Assets", f"Falta un archivo de imagen en la carpeta.\nDetalle: {e}")
            sys.exit(1)

    # NUEVO PARÁMETRO AÑADIDO: fps_ms (La tasa que dicta el archivo JSON)
    def update_animation(self, state, facing_right, canvas_image_id, animar_reposo, fps_ms):
        if state == 'saliendo': return

        # CÁLCULO DE DELTA TIME: Miramos el reloj del sistema operativo
        tiempo_actual = time.time()
        tiempo_transcurrido_ms = (tiempo_actual - self.last_frame_time) * 1000
        cambio_estado = state != self.last_state

        # LA BARRERA DE RENDIMIENTO: Si no ha pasado el tiempo real, cancelamos el renderizado.
        if not cambio_estado and tiempo_transcurrido_ms < fps_ms:
            return 

        if cambio_estado:
            transicion_fluida = (not self.idle_is_animated) and animar_reposo and state in ['quieto', 'caminando'] and self.last_state in ['quieto', 'caminando']
            if not transicion_fluida:
                self.current_frame_index = 0
            self.last_state = state

        # Reiniciamos el cronómetro solo porque hemos decidido dibujar un nuevo fotograma
        self.last_frame_time = tiempo_actual

        deshabilitar_espejo = False

        # 3. LÓGICA DE SELECCIÓN DE FOTOGRAMAS
        if state == 'caminando':
            if self.directional_walk:
                deshabilitar_espejo = True
                matriz_activa = self.frames_walk_right if facing_right else self.frames_walk_left
                if self.current_frame_index >= len(matriz_activa): 
                    self.current_frame_index = 0
                raw_image = matriz_activa[self.current_frame_index]
                self.current_frame_index = (self.current_frame_index + 1) % len(matriz_activa)
            else:
                raw_image = self.frames_walk[self.current_frame_index]
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames_walk)
            
        elif state == 'quieto':
            if self.idle_is_animated:
                raw_image = self.frames_idle[self.current_frame_index]
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames_idle)
            elif animar_reposo:
                if self.directional_walk:
                    deshabilitar_espejo = True
                    matriz_activa = self.frames_walk_right if facing_right else self.frames_walk_left
                    if self.current_frame_index >= len(matriz_activa): 
                        self.current_frame_index = 0
                    raw_image = matriz_activa[self.current_frame_index]
                    self.current_frame_index = (self.current_frame_index + 1) % len(matriz_activa)
                else:
                    raw_image = self.frames_walk[self.current_frame_index]
                    self.current_frame_index = (self.current_frame_index + 1) % len(self.frames_walk)
            else:
                raw_image = self.img_idle

        # 4. ESPEJADO MATEMÁTICO
        if deshabilitar_espejo:
            processed_image = raw_image
        else:
            if state == 'quieto' and self.fijar_direccion_reposo:
                direccion_efectiva = True 
            else:
                direccion_efectiva = facing_right
            
            debe_espejar = direccion_efectiva if self.invertir_eje_x else (not direccion_efectiva)
            
            if debe_espejar:
                processed_image = ImageOps.mirror(raw_image)
            else:
                processed_image = raw_image

        self.tk_image_ref = ImageTk.PhotoImage(processed_image)
        self.canvas.itemconfig(canvas_image_id, image=self.tk_image_ref)


class DesktopPet:
    def __init__(self):
        # 1. SEGURIDAD: Comprobar existencia del archivo de configuración
        if not os.path.exists("config.json"):
            tk.Tk().withdraw()
            messagebox.showerror("Fallo de Inicialización", "No se encuentra el archivo 'config.json'. El motor de la mascota no puede arrancar.")
            sys.exit(1)

        # 2. CARGA DE DATOS: Inyectar el JSON en memoria
        try:
            with open("config.json", "r", encoding="utf-8") as archivo:
                config = json.load(archivo)
        except json.JSONDecodeError as e:
            tk.Tk().withdraw()
            messagebox.showerror("Error de Sintaxis", f"El archivo 'config.json' está mal escrito. Revisa las comas y corchetes.\nDetalle: {e}")
            sys.exit(1)

        # 3. EXTRACCIÓN DE PARÁMETROS
        c_comp = config.get("comportamiento", {})
        c_geo = config.get("geometria", {})
        self.c_img = config.get("imagenes", {})
        self.c_aud = config.get("audio", {})

        self.animar_en_reposo = c_comp.get("animar_en_reposo", False)
        self.vuelo_amplitud = c_comp.get("vuelo_amplitud", 0)
        self.vuelo_frecuencia = c_comp.get("vuelo_frecuencia", 5.0)

        self.probabilidad_quieto = c_comp.get("probabilidad_quieto", 0.5)
        self.probabilidad_mover = c_comp.get("probabilidad_mover", 0.5)
        self.tiempo_reposo_min = c_comp.get("tiempo_reposo_min", 1000)
        self.tiempo_reposo_max = c_comp.get("tiempo_reposo_max", 4000)
        self.distancia_min = c_comp.get("distancia_min", 50)
        self.distancia_max = c_comp.get("distancia_max", 300)
        self.velocidad_paso = c_comp.get("velocidad_paso", 6)
        self.tasa_refresco_fisica = c_comp.get("tasa_refresco_fisica", 30)

        self.size_idle = (c_geo.get("size_idle_w", 115), c_geo.get("size_idle_h", 99))
        self.size_walk = (c_geo.get("size_walk_w", 133), c_geo.get("size_walk_h", 115))
        self.offset_y = c_geo.get("offset_y", 5)

        self.frame_rate_activo = self.c_img.get("frame_rate_activo", 100)
        self.frame_rate_reposo = self.c_img.get("frame_rate_reposo", 500)

        # 4. INICIALIZACIÓN DE LA VENTANA (Lo que se había borrado)
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        self.transparency_key = '#FF00FF' 
        self.root.config(bg=self.transparency_key)
        self.root.wm_attributes('-transparentcolor', self.transparency_key)

        # Expandir la ventana para dar espacio al aleteo sin que se corte la imagen
        self.max_w = max(self.size_idle[0], self.size_walk[0])
        self.max_h = max(self.size_idle[1], self.size_walk[1]) + (self.vuelo_amplitud * 2)

        self.canvas = tk.Canvas(self.root, width=self.max_w, height=self.max_h, 
                                bg=self.transparency_key, highlightthickness=0)
        self.canvas.pack()
        
        # El ancla es SUR, bajamos la base usando la amplitud
        self.y_ancla_base = self.max_h - self.vuelo_amplitud
        self.canvas_image_id = self.canvas.create_image(
            self.max_w // 2, 
            self.y_ancla_base, 
            anchor=tk.S, 
            image=None
        )

        # 5. INICIALIZAR SUBSISTEMAS
        self.animator = DesktopPetAnimator(self.canvas, self.c_img, self.size_idle, self.size_walk)
        self.root.bind('<Button-3>', self.iniciar_salida_animada)

        monitores = get_monitors()
        self.limite_izquierdo = min(m.x for m in monitores)
        self.limite_derecho = max(m.x + m.width for m in monitores)

        # Compensa el Y de la ventana con el espacio extra de vuelo
        self.x = 0
        self.y = self.root.winfo_screenheight() - self.max_h + self.offset_y + (self.vuelo_amplitud * 2)
        
        self.is_facing_right = True
        self.current_state = 'quieto'
        self.anim_timer = None 

        # AUDIO DINÁMICO
        self.sonido_estrella = None 
        try:
            pygame.mixer.init()
            archivo_audio = self.c_aud.get("exit_sound", "warpstar.mp3")
            volumen_audio = self.c_aud.get("volumen", 0.1)
            
            self.sonido_estrella = pygame.mixer.Sound(archivo_audio)
            self.sonido_estrella.set_volume(volumen_audio)
        except Exception as e:
            print(f"Advertencia: No se pudo cargar el subsistema de audio. Detalle: {e}")
        
        # 6. ARRANQUE
        self.root.geometry(f'+{self.x}+{self.y}')
        self.update_state_machine() 
        self.animate_loop()  
        self.mantener_siempre_arriba()
        
        # Iniciar bucle físico de vuelo solo si tiene amplitud
        if self.vuelo_amplitud > 0:
            self.loop_vuelo()
            
        self.root.mainloop()

    def iniciar_salida_animada(self, event=None):
        if self.current_state == 'saliendo': return 
        self.current_state = 'saliendo'
        self.root.unbind('<Button-3>') 
        if self.anim_timer: self.root.after_cancel(self.anim_timer)
            
        try:
            img_salida = self.c_img.get("exit_anim", "warpstar.png")
            self.img_star_raw = Image.open(img_salida).convert("RGBA")
            self.img_star_raw = self.img_star_raw.resize((80, 80), Image.Resampling.NEAREST)
        except FileNotFoundError:
            self.salir()
            return

        self.vel_y = -18 
        self.gravedad = 2
        self.vel_x = 12 if self.is_facing_right else -12 
        self.escala_estrella = 1.0
        self.angulo_estrella = 0
        
        self.canvas.itemconfig(self.canvas_image_id, anchor=tk.CENTER)
        self.canvas.coords(self.canvas_image_id, self.max_w // 2, self.max_h // 2)

        if self.sonido_estrella:
            canal = self.sonido_estrella.play()
            if canal: canal.fadeout(1000)

        self.loop_salida()

    def loop_salida(self):
        if self.escala_estrella <= 0.05:
            self.salir()
            return

        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += self.gravedad 
        self.root.geometry(f'+{self.x}+{self.y}')
        
        self.escala_estrella -= 0.04  
        self.angulo_estrella = (self.angulo_estrella - 25) % 360 
        
        w_actual = int(80 * self.escala_estrella)
        h_actual = int(80 * self.escala_estrella)
        
        if w_actual > 0 and h_actual > 0:
            img_frame = self.img_star_raw.resize((w_actual, h_actual), Image.Resampling.NEAREST)
            img_frame = img_frame.rotate(self.angulo_estrella, expand=True, fillcolor=(255, 0, 255, 0))
            self.animator.tk_image_ref = ImageTk.PhotoImage(img_frame)
            self.canvas.itemconfig(self.canvas_image_id, image=self.animator.tk_image_ref)
        
        self.root.after(30, self.loop_salida)

    def update_state_machine(self):
        if self.current_state == 'saliendo': return
        decision = random.choices(['quieto', 'moverse'], weights=[self.probabilidad_quieto, self.probabilidad_mover])[0]

        if decision == 'quieto':
            self.current_state = 'quieto'
            tiempo_dormido = random.randint(self.tiempo_reposo_min, self.tiempo_reposo_max)
            self.root.after(tiempo_dormido, self.update_state_machine)
            return

        self.current_state = 'caminando'
        distancia = random.randint(self.distancia_min, self.distancia_max)

        if self.x < self.limite_izquierdo + 100: self.is_facing_right = True 
        elif self.x > self.limite_derecho - self.max_w - 100: self.is_facing_right = False 
        else: self.is_facing_right = random.choice([True, False])

        if self.anim_timer: self.root.after_cancel(self.anim_timer)
        self.animate_loop()
        self.ejecutar_desplazamiento(distancia)

    def ejecutar_desplazamiento(self, pixeles_restantes):
        if self.current_state == 'saliendo': return 
        if pixeles_restantes <= 0 or self.current_state == 'quieto':
            self.current_state = 'quieto'
            if self.anim_timer: self.root.after_cancel(self.anim_timer)
            self.animate_loop()
            self.update_state_machine() 
            return

        velocidad = self.velocidad_paso
        paso = velocidad if self.is_facing_right else -velocidad
        self.x += paso
        
        if self.x < self.limite_izquierdo: self.x = self.limite_izquierdo; pixeles_restantes = 0
        if self.x > self.limite_derecho - self.max_w: self.x = self.limite_derecho - self.max_w; pixeles_restantes = 0
            
        self.root.geometry(f'+{self.x}+{self.y}')
        self.root.after(self.tasa_refresco_fisica, lambda: self.ejecutar_desplazamiento(pixeles_restantes - velocidad))

    def animate_loop(self):
        if self.current_state == 'saliendo': return 
        
        # Extraemos la velocidad que desea el JSON
        if self.current_state == 'caminando' or (self.current_state == 'quieto' and self.animar_en_reposo):
            velocidad_objetivo_ms = self.frame_rate_activo
        else:
            velocidad_objetivo_ms = self.frame_rate_reposo
            
        # Le enviamos el objetivo al animador. Él mirará el reloj y decidirá si pintar o ignorar.
        self.animator.update_animation(self.current_state, self.is_facing_right, self.canvas_image_id, self.animar_en_reposo, velocidad_objetivo_ms)
        
        # Obligamos a Tkinter a procesar el motor visual a 60 FPS fijos (~16ms).
        # Esto elimina de cuajo la desincronización por bloqueos del hilo principal.
        self.anim_timer = self.root.after(16, self.animate_loop)

    def mantener_siempre_arriba(self):
        if self.current_state != 'saliendo':
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after(2000, self.mantener_siempre_arriba)

    def loop_vuelo(self):
        """Aplica una onda sinusoidal a la posición Y de la imagen interna."""
        if self.current_state == 'saliendo': return

        # Cálculo de la oscilación armónica
        tiempo_actual = time.time()
        desplazamiento_y = math.sin(tiempo_actual * self.vuelo_frecuencia) * self.vuelo_amplitud
        
        # Actualizar las coordenadas dentro del Canvas sin mover la ventana principal
        self.canvas.coords(self.canvas_image_id, self.max_w // 2, self.y_ancla_base + desplazamiento_y)
        
        # Refresco a 30 ms (aprox 33 FPS) para movimiento fluido
        self.root.after(30, self.loop_vuelo)

    def salir(self):
        self.root.destroy()


# --- NUEVA ARQUITECTURA: EL LAUNCHER ---

class PetLauncher:
    """Ventana inicial que escanea directorios y lanza la mascota seleccionada."""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Selector de Mascotas")
        # Geometría expandida para alojar la barra de desplazamiento
        self.root.geometry("320x450")
        self.root.resizable(False, False)
        
        color_borde = "#000000"  
        color_fondo = "#F4D03F"  
        grosor_borde = 8         
        
        self.root.config(bg=color_borde)
        self.root.eval('tk::PlaceWindow . center')

        self.container = tk.Frame(self.root, bg=color_fondo)
        self.container.pack(fill=tk.BOTH, expand=True, padx=grosor_borde, pady=grosor_borde)

        tk.Label(self.container, text="Elige tu mascota", font=("Helvetica", 14, "bold"), bg=color_fondo).pack(pady=15)

        self.mascotas_disponibles = self.escanear_mascotas()

        if not self.mascotas_disponibles:
            tk.Label(self.container, text="No se encontraron mascotas.", fg="red", bg=color_fondo).pack(pady=10)
            tk.Label(self.container, text="Crea subcarpetas que contengan\nun archivo 'config.json'.", bg=color_fondo).pack()
        else:
            # 1. Crear un marco dedicado para albergar el Canvas y la Scrollbar
            frame_lista = tk.Frame(self.container, bg=color_fondo)
            frame_lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # 2. Inicializar Canvas y Scrollbar
            canvas = tk.Canvas(frame_lista, bg=color_fondo, highlightthickness=0)
            scrollbar = tk.Scrollbar(frame_lista, orient="vertical", command=canvas.yview)
            
            # 3. Contenedor interno desplazable
            self.scrollable_frame = tk.Frame(canvas, bg=color_fondo)

            # Recalcular el área de desplazamiento dinámicamente cada vez que se añade un botón
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            # Anclar el marco al Canvas (width=250 asegura que el botón ocupe todo el ancho útil)
            canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=250)
            canvas.configure(yscrollcommand=scrollbar.set)

            # Empaquetar elementos de la lista
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # 4. Captura del evento de la rueda del ratón (Windows)
            def _on_mousewheel(event):
                # El divisor 120 es el estándar de hardware en Windows para un "clic" de la rueda
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

            # 5. Generación iterativa de botones
            for nombre_mascota, ruta_carpeta in self.mascotas_disponibles.items():
                btn = tk.Button(
                    self.scrollable_frame, 
                    text=nombre_mascota, 
                    font=("Helvetica", 12),
                    command=lambda ruta=ruta_carpeta: self.lanzar_mascota(ruta, canvas)
                )
                btn.pack(fill=tk.X, padx=10, pady=5)

        self.root.mainloop()

    def escanear_mascotas(self):
        mascotas = {}
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        for nombre_carpeta in os.listdir(base_dir):
            ruta_carpeta = os.path.join(base_dir, nombre_carpeta)
            if os.path.isdir(ruta_carpeta):
                if os.path.exists(os.path.join(ruta_carpeta, "config.json")):
                    mascotas[nombre_carpeta] = ruta_carpeta
                    
        return mascotas

    def lanzar_mascota(self, ruta_mascota, canvas=None):
        """Mata el menú, limpia la caché de eventos e inicializa el motor físico."""
        if canvas:
            # Desvincular evento global para evitar interferencias con el motor de la mascota
            canvas.unbind_all("<MouseWheel>")
            
        os.chdir(ruta_mascota) 
        self.root.destroy()
        DesktopPet()

if __name__ == '__main__':
    PetLauncher()