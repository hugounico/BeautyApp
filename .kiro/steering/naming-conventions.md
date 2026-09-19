# Convenciones de Nombrado

## Reglas

- **Clases** (modelos, vistas basadas en clase, formularios, serializadores) → PascalCase
- **Variables, funciones, nombres de apps y nombres de archivos** → snake_case, siguiendo PEP8 y la convención estándar de Django

## Ejemplos

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Modelo | PascalCase | `ServiceCategory` |
| Vista basada en clase | PascalCase | `ProfessionalListView` |
| Formulario | PascalCase | `BookingForm` |
| Serializador | PascalCase | `UserSerializer` |
| Función/método | snake_case | `get_active_professionals` |
| Variable | snake_case | `service_count` |
| App Django | snake_case | `beauty_app` |
| Archivo | snake_case | `service_views.py` |
| Proyecto Django (paquete raíz) | snake_case | `beautyfull` |

---

> **Gobernanza:** Si en cualquier spec futuro una instrucción contradice este steering file, Kiro debe detenerse y pedir clarificación explícita antes de continuar — nunca resolver la contradicción por su cuenta ni ignorar silenciosamente ninguna fuente.
