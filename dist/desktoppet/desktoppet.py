import tkinter as tk
from tkinter import Menu
import random
from PIL import Image, ImageTk, ImageOps
from screeninfo import get_monitors
import pygame

class DesktopPetAnimator:
    """Clase dedicada exclusivamente a gestionar los fotogramas y tiempos de animación."""
    def __init__(self, canvas_widget, size_idle, size_walk):
        self.canvas = canvas_widget
        self.current_frame_index = 0
        self.last_state = None
        self.is_facing_right = True
        self.tk_image_ref = None

        filtro_escalado = Image.Resampling.NEAREST 

        try:
            raw_idle = Image.open("quieto.png")
            self.img_idle = raw_idle.resize(size_idle, filtro_escalado)
            
            self.frames_walk = []
            for i in range(10):
                raw_frame = Image.open(f"frame{i}.png")
                resized_frame = raw_frame.resize(size_walk, filtro_escalado)
                self.frames_walk.append(resized_frame)
                
        except FileNotFoundError as e:
            print(f"Error Crítico: Falta un archivo de imagen. Detalle: {e}")
            raise

    def update_animation(self, state, facing_right, canvas_image_id):
        if state != self.last_state:
            self.current_frame_index = 0
            self.last_state = state

        if state == 'quieto':
            raw_image = self.img_idle
        elif state == 'caminando':
            raw_image = self.frames_walk[self.current_frame_index]
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames_walk)
        else:
            return # Si está 'saliendo', no actualizar la animación normal

        if not facing_right:
            processed_image = ImageOps.mirror(raw_image)
        else:
            processed_image = raw_image

        self.tk_image_ref = ImageTk.PhotoImage(processed_image)
        self.canvas.itemconfig(canvas_image_id, image=self.tk_image_ref)


class DesktopPet:
    def __init__(self):
        # --- CONFIGURACIÓN DE COMPORTAMIENTO (PANEL DE CONTROL) ---
        
        # 1. Frecuencia de decisiones (Probabilidades)
        self.probabilidad_quieto = 0.5  
        self.probabilidad_mover = 0.5   
        
        # 2. Tiempos de reposo (Milisegundos)
        self.tiempo_reposo_min = 1000   
        self.tiempo_reposo_max = 4000   
        
        # 3. Distancia de viaje (Píxeles)
        self.distancia_min = 50         
        self.distancia_max = 300        
        
        # 4. Velocidad de desplazamiento
        self.velocidad_paso = 6         
        self.tasa_refresco_fisica = 30  
        
        # ---------------------------------------------------------

        self.root = tk.Tk()
        
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        self.transparency_key = '#FF00FF' 
        self.root.config(bg=self.transparency_key)
        self.root.wm_attributes('-transparentcolor', self.transparency_key)

        self.size_idle = (115, 99)     
        self.size_walk = (133, 115)     

        self.max_w = max(self.size_idle[0], self.size_walk[0])
        self.max_h = max(self.size_idle[1], self.size_walk[1])

        self.canvas = tk.Canvas(self.root, width=self.max_w, height=self.max_h, 
                                bg=self.transparency_key, highlightthickness=0)
        self.canvas.pack()
        
        self.canvas_image_id = self.canvas.create_image(
            self.max_w // 2, 
            self.max_h, 
            anchor=tk.S, 
            image=None
        )

        try:
            self.animator = DesktopPetAnimator(self.canvas, self.size_idle, self.size_walk)
        except:
            self.root.destroy()
            return

        # VINCULAR EL CLIC DERECHO A LA ANIMACIÓN DE SALIDA
        self.root.bind('<Button-3>', self.iniciar_salida_animada)

        monitores = get_monitors()
        self.limite_izquierdo = min(m.x for m in monitores)
        self.limite_derecho = max(m.x + m.width for m in monitores)

        self.x = 0
        self.y = self.root.winfo_screenheight() - self.max_h + 5
        
        self.is_facing_right = True
        self.current_state = 'quieto'
        self.anim_timer = None 

        # --- SISTEMA DE AUDIO (NUEVO) ---
        try:
            pygame.mixer.init()
            self.sonido_estrella = pygame.mixer.Sound("warpstar.mp3")
            
            # Establecer el volumen inicial. 
            # 0.3 equivale al 30% del volumen original del archivo MP3.
            self.sonido_estrella.set_volume(0.1)
            
        except Exception as e:
            print(f"Advertencia: No se pudo inicializar el audio o falta 'warpstar.mp3'. Detalle: {e}")
            self.sonido_estrella = None
        # --------------------------------
        
        self.root.geometry(f'+{self.x}+{self.y}')
        self.update_state_machine() 
        self.animate_loop()  
        self.mantener_siempre_arriba()       
        
        self.root.mainloop()

    # --- SISTEMA DE ANIMACIÓN DE SALIDA ---

    def iniciar_salida_animada(self, event=None):
        """Prepara el entorno para la cinemática de cierre."""
        # 1. Bloquear interacciones y matar procesos paralelos
        if self.current_state == 'saliendo': return # Evitar spam de clics
        self.current_state = 'saliendo'
        self.root.unbind('<Button-3>') 
        if self.anim_timer:
            self.root.after_cancel(self.anim_timer)
            
        # 2. Cargar imagen de la estrella (Fallback si no existe)
        try:
            # Aseguramos el formato RGBA y usamos NEAREST para bordes duros
            self.img_star_raw = Image.open("warpstar.png").convert("RGBA")
            self.img_star_raw = self.img_star_raw.resize((80, 80), Image.Resampling.NEAREST)
        except FileNotFoundError:
            print("Aviso: 'warpstar.png' no encontrada. Forzando cierre seguro.")
            self.salir()
            return

        # 3. Configurar física del Tiro Parabólico
        self.vel_y = -18 # Impulso hacia arriba (negativo en coordenadas de pantalla)
        self.gravedad = 2
        # La estrella vuela hacia donde Kirby estaba mirando
        self.vel_x = 12 if self.is_facing_right else -12 
        
        # 4. Configurar transformaciones gráficas
        self.escala_estrella = 1.0
        self.angulo_estrella = 0
        
        # 5. Corrección Geométrica: Cambiar ancla al centro para rotación perfecta
        self.canvas.itemconfig(self.canvas_image_id, anchor=tk.CENTER)
        self.canvas.coords(self.canvas_image_id, self.max_w // 2, self.max_h // 2)

        # 6. DISPARO DE AUDIO CON FADE-OUT (NUEVO)
        if self.sonido_estrella:
            canal = self.sonido_estrella.play()
            if canal:
                canal.fadeout(1000)

        # Disparar bucle
        self.loop_salida()

    def loop_salida(self):
        """Calcula el vector de movimiento, la rotación y el tamaño fotograma a fotograma."""
        # Condición de destrucción (cuando desaparece visualmente)
        if self.escala_estrella <= 0.05:
            self.salir()
            return

        # FÍSICA: Actualizar coordenadas de la ventana del SO
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += self.gravedad # Aplicar aceleración gravitatoria
        self.root.geometry(f'+{self.x}+{self.y}')
        
        # MATEMÁTICAS: Actualizar escalado y rotación
        self.escala_estrella -= 0.04  # Reducir 4% por fotograma
        self.angulo_estrella = (self.angulo_estrella - 25) % 360 # Girar 25 grados
        
        # RENDERIZADO: Aplicar transformaciones mediante Pillow
        w_actual = int(80 * self.escala_estrella)
        h_actual = int(80 * self.escala_estrella)
        
        if w_actual > 0 and h_actual > 0:
            # 1. Redimensionar sin suavizado (NEAREST)
            img_frame = self.img_star_raw.resize((w_actual, h_actual), Image.Resampling.NEAREST)
            
            # 2. CRÍTICO: Rellenar la expansión de la rotación con magenta transparente
            img_frame = img_frame.rotate(
                self.angulo_estrella, 
                expand=True, 
                fillcolor=(255, 0, 255, 0)
            )
            
            # Actualizar Canvas
            self.animator.tk_image_ref = ImageTk.PhotoImage(img_frame)
            self.canvas.itemconfig(self.canvas_image_id, image=self.animator.tk_image_ref)
        
        # Bucle a ~30 FPS
        self.root.after(30, self.loop_salida)

    # --- LÓGICA PRINCIPAL ---

    def update_state_machine(self):
        if self.current_state == 'saliendo': return

        # Usar las probabilidades del panel de control
        decision = random.choices(
            ['quieto', 'moverse'], 
            weights=[self.probabilidad_quieto, self.probabilidad_mover]
        )[0]

        if decision == 'quieto':
            self.current_state = 'quieto'
            # Calcular tiempo de reposo dinámico
            tiempo_dormido = random.randint(self.tiempo_reposo_min, self.tiempo_reposo_max)
            self.root.after(tiempo_dormido, self.update_state_machine)
            return

        self.current_state = 'caminando'
        # Calcular distancia dinámica
        distancia = random.randint(self.distancia_min, self.distancia_max)

        # ... (Mantén el resto del método intacto a partir de aquí) ...

        if self.x < self.limite_izquierdo + 100: 
            self.is_facing_right = True 
        elif self.x > self.limite_derecho - self.max_w - 100: 
            self.is_facing_right = False 
        else: 
            self.is_facing_right = random.choice([True, False])

        if self.anim_timer: self.root.after_cancel(self.anim_timer)
        self.animate_loop()
        self.ejecutar_desplazamiento(distancia)

    def ejecutar_desplazamiento(self, pixeles_restantes):
        # Interrupción de seguridad si el usuario hizo clic derecho mientras caminaba
        if self.current_state == 'saliendo': return 

        if pixeles_restantes <= 0 or self.current_state == 'quieto':
            self.current_state = 'quieto'
            if self.anim_timer: self.root.after_cancel(self.anim_timer)
            self.animate_loop()
            self.update_state_machine() 
            return

        # SUSTITUCIÓN 1: Leer la velocidad desde el panel de control
        velocidad = self.velocidad_paso
        paso = velocidad if self.is_facing_right else -velocidad
        self.x += paso
        
        if self.x < self.limite_izquierdo: 
            self.x = self.limite_izquierdo; pixeles_restantes = 0
        if self.x > self.limite_derecho - self.max_w: 
            self.x = self.limite_derecho - self.max_w; pixeles_restantes = 0
            
        self.root.geometry(f'+{self.x}+{self.y}')
        
        # SUSTITUCIÓN 2: Leer la tasa de refresco desde el panel de control
        self.root.after(self.tasa_refresco_fisica, lambda: self.ejecutar_desplazamiento(pixeles_restantes - velocidad))

    def animate_loop(self):
        if self.current_state == 'saliendo': return # Interrupción visual

        fps = 100 if self.current_state == 'caminando' else 500
        self.animator.update_animation(self.current_state, self.is_facing_right, self.canvas_image_id)
        self.anim_timer = self.root.after(fps, self.animate_loop)

    def mantener_siempre_arriba(self):
        """Fuerza a Windows a devolver la ventana a la capa absoluta superior."""
        if self.current_state != 'saliendo':
            # lift() empuja la ventana hacia el usuario
            self.root.lift()
            # Reafirma el atributo a nivel de sistema operativo
            self.root.attributes('-topmost', True)
            
            # Repite la comprobación cada 2 segundos (2000 ms)
            self.root.after(2000, self.mantener_siempre_arriba)

    def salir(self):
        self.root.destroy()

if __name__ == '__main__':
    DesktopPet()