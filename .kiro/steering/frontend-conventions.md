# Convenciones de Frontend

## Reglas

- HTML libre de estilos inline y JavaScript embebido — todo CSS va en `/static/css/`, todo JS en `/static/js/`
- Priorizar lógica backend (server-rendered) sobre JavaScript del lado del cliente, a menos que la interacción lo requiera explícitamente

## Detalle

| Aspecto | Regla |
|--------|------|
| Estilos CSS | Siempre en archivos separados dentro de `/static/css/` |
| JavaScript | Siempre en archivos separados dentro de `/static/js/` |
| Renderizado | Server-side por defecto (templates Django) |
| JS del cliente | Solo cuando la interacción del usuario lo requiera explícitamente |
| Atributos `style=""` | Prohibidos en HTML |
| Tags `<script>` inline | Prohibidos en HTML |

---

## Herencia de Templates (Django Template Inheritance)

Esta regla aplica únicamente cuando una Spec futura incluya Django Templates dentro de su alcance. **No autoriza crear templates, vistas ni frontend real en `data-model-core`.** Tampoco autoriza introducir React, Next.js u otro frontend alternativo -- el renderizado sigue siendo server-side con Django Templates.

Cuando se implementen templates:

- Se debe usar el sistema nativo de **Django Template Inheritance** (`{% extends %}` / `{% block %}` / `{% include %}`).
- El template base compartido (`base.html`) reside en `apps/beauty_app/templates/`, coherente con `architecture.md` y con el rol de `beauty_app` como app reservada para elementos globales/compartidos del proyecto.
- Los componentes globales reutilizables (navbar, footer, mensajes) residen en `apps/beauty_app/templates/components/`.
- Los templates propios de cada dominio permanecen **namespaced** dentro de `apps/<app>/templates/<app>/` (p. ej. `apps/servicios/templates/servicios/`), de modo que cada app de dominio siga siendo autocontenida y reutilizable.
- Las páginas heredan del base mediante `{% extends %}`.
- Se usan `{% block %}` para las áreas extensibles (por ejemplo: `title`, `extra_css`, `content`, `extra_js`).
- Se usa `{% include %}` para componentes reutilizables cuando corresponda.
- Se evita duplicar estructura HTML global, navegación, footer o CSS/JS compartido entre páginas.
- Se evita una jerarquía de herencia innecesariamente profunda (como referencia, no más de 2-3 niveles de `{% extends %}` encadenados).

### Ubicación de templates

| Tipo de template | Ubicación |
|----------------|----------|
| `base.html` (estructura global) | `apps/beauty_app/templates/base.html` |
| Componentes globales (navbar, footer, mensajes) | `apps/beauty_app/templates/components/` |
| Templates de dominio | `apps/<app>/templates/<app>/` (namespaced) |

> **Motivo de la ubicación:** `apps/beauty_app` ya está establecida como la app reservada para elementos globales/compartidos. Mantener `base.html` y `components/` allí evita duplicar ese propósito en un `templates/` adicional a nivel de proyecto, y respeta `architecture.md` sin modificarlo.

---

## Responsividad / Mobile-first

- El diseño visual de BeautyFull —y de cualquier proyecto futuro similar— debe construirse **mobile-first / responsive** desde el inicio.
- Aunque el trabajo de diseño se realice primero en navegador de escritorio, el objetivo final del producto es funcionar como experiencia de celular; el layout debe priorizar la pantalla pequeña y escalar hacia arriba.
- Este principio se reflejará en las specs futuras de frontend cuando se definan breakpoints, unidades relativas y la estructura de CSS.
- Este turno no requiere ninguna decisión técnica de CSS ni de framework; solo deja el principio establecido como convención a seguir.

---

> **Gobernanza:** Si en cualquier spec futuro una instrucción contradice este steering file, Kiro debe detenerse y pedir clarificación explícita antes de continuar — nunca resolver la contradicción por su cuenta ni ignorar silenciosamente ninguna fuente.
