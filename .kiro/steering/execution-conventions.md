# Convenciones de Ejecución

Reglas operativas derivadas de problemas reales ocurridos durante la ejecución de la spec `django-foundation`. Se aplican a todas las specs presentes y futuras de este proyecto.

---

## Reglas

### 1. Edición de archivos de texto — siempre con herramientas nativas del IDE

Toda edición de archivos `.md`, `.py`, `.html`, `.txt` y cualquier otro archivo de texto debe hacerse **exclusivamente** con las herramientas nativas de archivo del IDE (lectura, escritura completa, reemplazo de fragmento).

**Prohibido** usar comandos de PowerShell para editar texto:
- `Set-Content`
- `.Replace()` encadenado con `Get-Content`
- Heredocs (`@"..."@`, `@'...'@`)
- `[System.IO.File]::WriteAllText`
- Redirecciones (`>`, `>>`)

**PowerShell (`execute_pwsh`) se reserva exclusivamente** para operaciones que requieren shell real:
- Instalar dependencias (`pip install`, `npm install`, etc.)
- Ejecutar `manage.py`, `django-admin`, servidores de desarrollo
- Crear directorios (`New-Item`, `mkdir`)
- Correr tests y comandos de verificación

**Motivo:** PowerShell en Windows no maneja UTF-8 de forma confiable por defecto. En este proyecto ya causó pérdida de tildes y caracteres especiales (é, ó, ú, í, á, ñ, →, —) que requirieron corrección manual.

---

### 2. Verificación con evidencia antes de reportar éxito

Nunca marcar una tarea como completa, ni reportar que un cambio "funcionó", sin **releer el resultado** con la herramienta de lectura correspondiente.

- Después de editar un archivo: releerlo con la herramienta nativa de lectura y mostrar el fragmento relevante.
- Después de ejecutar un comando de shell: mostrar el output completo y textual devuelto por el terminal.
- Un comando que no arroja error **no es evidencia** de que hizo lo esperado — confirmar el resultado real antes de reportarlo.

---

### 3. Ante fallos repetidos — reportar antes de reintentar

Si una herramienta falla dos veces con el mismo enfoque, **detenerse** y reportar:

1. El comando o llamada exacta del último intento (sin resumir).
2. El mensaje de error completo y textual devuelto (sin reinterpretar).
3. El paso específico de la tarea donde ocurrió.

Solo después de reportar esto, diagnosticar la causa raíz y proponer un enfoque diferente.

Después de dos fallos consecutivos del mismo enfoque, no volver a intentar ese mismo enfoque. El paso de "detenerse y reportar antes de continuar" aplica únicamente cuando NO existe una alternativa ya autorizada: es decir, cuando se requiere nueva autorización, una excepción de steering, una operación destructiva, cuando se amplía el alcance o el riesgo, o cuando hay incertidumbre sobre el estado de los archivos o del sistema. Cuando SÍ existe una alternativa claramente distinta ya permitida por el steering/autorización vigente, que no amplía el alcance ni el riesgo, Kiro puede usarla sin detenerse a reportar primero, pero debe documentar en el reporte final tanto los fallos como el cambio de estrategia.

---

### 4. Verificar precondiciones de entorno antes de ejecutar

Si una tarea requiere Python, pip, un entorno virtual, o cualquier dependencia de entorno, **confirmar explícitamente** que están disponibles y en el estado esperado antes de ejecutar el comando principal.

Ejemplo obligatorio al inicio de cualquier tarea que use el venv:
```powershell
.\venv\Scripts\python.exe --version
```

No asumir que el entorno de la sesión anterior sigue vigente — entre tareas o sesiones del IDE, el estado del entorno puede haber cambiado.

---

## Gobernanza

> **Gobernanza:** Si en cualquier spec futuro una instrucción contradice este steering file, Kiro debe detenerse y pedir clarificación explícita antes de continuar — nunca resolver la contradicción por su cuenta ni ignorar silenciosamente ninguna fuente.
