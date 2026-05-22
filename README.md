```python
readme_content = """# Guía de Actualización - Desktop Pet

Este documento contiene los comandos esenciales y el flujo de trabajo obligatorio para modificar, probar y volver a compilar tu mascota virtual de escritorio sin romper el ejecutable.

---

## 🔄 Flujo de Trabajo para Actualizaciones

### Paso 1: Fase de Desarrollo (Probar cambios al instante)
**NO compiles el ejecutable después de cada pequeño cambio.** Para probar si tus modificaciones de velocidad, tamaño o comportamiento funcionan, ejecuta el script directamente con Python desde tu terminal o VS Code:


```

````text
File generated successfully.

```bash
python desktoppet.py

````

_Si esto falla por configuración de Windows, usa:_ `py desktoppet.py`

---

### Paso 2: Fase de Despliegue (Volver a generar el `.exe`)

Cuando el código esté listo y quieras congelarlo en un ejecutable autónomo que funcione sin VS Code abierto, ejecuta el comando de empaquetado:

```bash
python -m PyInstaller --noconsole desktoppet.py

```

> 💡 **Nota de Respaldo:** Si tu terminal vuelve a perder la ruta del módulo por problemas del PATH de Windows, usa el comando de ruta absoluta que resolvió el entorno:
>
> ```bash
> C:\\Users\\MSI\\AppData\\Roaming\\Python\\Python313\\Scripts\\pyinstaller.exe --noconsole desktoppet.py
>
> ```

---

### Paso 3: ⚠️ Regla Innegociable de los Assets (¡Muy Importante!)

Cada vez que ejecutas el comando del Paso 2, PyInstaller **limpia y borra por completo** la carpeta `dist/desktoppet/` para meter el nuevo código compilado.

Si intentas abrir el `.exe` directamente, crasheará en silencio porque no tiene las imágenes al lado. **Debes hacer esto manualmente tras cada compilación:**

1. Ve a la raíz de tu proyecto (`C:\\Users\\MSI\\Desktop\\Archivos\\pet`).
2. Copia tus **12 archivos de imagen**:

- `quieto.png`
- `warpstar.png`
- `frame0.png` hasta `frame9.png`

3. Pégalos dentro de la nueva carpeta: **`dist/desktoppet/`** (justo al lado del archivo `desktoppet.exe`).

---

## ⚙️ Panel de Control Rápido (En el código)

Recuerda que para cambiar la personalidad de tu mascota, solo debes editar las variables de la cabecera dentro del método `__init__` de la clase `DesktopPet`:

- `self.probabilidad_quieto` / `self.probabilidad_mover` -> Controla la hiperactividad (deben sumar 1.0).
- `self.tiempo_reposo_min` / `self.tiempo_reposo_max` -> Cuánto tiempo duerme (en milisegundos).
- `self.distancia_min` / `self.distancia_max` -> Cuánto camina antes de detenerse (en píxeles).
- `self.velocidad_paso` -> Rapidez física del desplazamiento (píxeles por ciclo).
  """

with open("README.md", "w", encoding="utf-8") as f:
f.write(readme_content)

print("File generated successfully.")

```
Your MD file is ready
[file-tag: code-generated-file-0-1779399849003321375]

Aquí tienes el mini README.md estructurado y directo al grano. Incluye el flujo de trabajo dividido en desarrollo y producción, los comandos exactos de PyInstaller que sortean el problema de variables de entorno de tu sistema, y el recordatorio técnico fundamental sobre reubicar los archivos `.png` tras cada recompilación para evitar el colapso silencioso del ejecutable. Guárdalo en la raíz de tu proyecto para consultarlo siempre que modifiques el código.

```
