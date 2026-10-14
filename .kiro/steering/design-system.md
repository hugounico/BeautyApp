# Design System — BeautyFull

## Principios

- Mobile-first: diseñar primero para pantalla de smartphone.
- El color nunca es el único medio para comunicar estado, selección,
  error o significado: acompañar siempre con texto, ícono o etiqueta.
- Ratios calculados con la fórmula WCAG 2.x. Toda combinación de texto
  y fondo que no figure aquí debe calcularse antes de usarse.
  Umbrales AA: 4.5:1 texto normal; 3:1 texto grande (≥24px, o ≥18.66px
  negrita), bordes, íconos e indicadores de foco.
- Cualquier variación de un fondo con texto (opacidad, aclarado,
  oscurecido) exige recalcular su ratio.

## Paleta

Marca:

- Moss Green `#4F6650` — primario, acción
- Beige `#F3ECE1` — fondo general
- Rosy Brown `#B98076` — acento secundario
- Midnight Green `#1B271C` — texto principal
- Violet Dream `#8C7AA0` — acento decorativo
- Lilac Cloud `#CDC2E6` — tinte suave
- Orchid Mist `#D7B9C8` — tinte suave

Neutro:

- Blanco `#FFFFFF` — texto sobre Moss Green; fondo de mensajes

Tinte derivado:

- Sage Mist `#DAD8CB` — Moss Green mezclado 85% con Beige

## Combinaciones aprobadas

| Texto | Fondo | Ratio | Uso |
|---|---|---|---|
| Midnight Green | Beige | 13.22 | Cuerpo y encabezados |
| Midnight Green | Blanco | 15.51 | Mensajes, tarjetas |
| Blanco | Moss Green | 6.27 | Botones primarios |
| Moss Green | Beige | 5.34 | Enlaces, navegación activa |
| Midnight Green | Rosy Brown | 4.74 | Badges, botones secundarios |
| Midnight Green | Lilac Cloud | 9.20 | Tarjetas de categoría |
| Midnight Green | Orchid Mist | 8.62 | Tarjetas de categoría |
| Midnight Green | Sage Mist | 10.83 | Tarjetas de categoría |

## Combinaciones prohibidas

- Rosy Brown como texto sobre Beige (2.79).
- Blanco sobre Rosy Brown (3.28), salvo texto ≥24px.
- Cualquier texto sobre Violet Dream (Midnight 3.99, blanco 3.88).
- Advertencia `#9A6B1E` como texto sobre Beige (3.98).

## Roles

- Moss Green: único color de acción primaria ("Reservar", "Ingresar"),
  enlaces, navegación activa.
- Rosy Brown: badges, etiquetas, botones secundarios; siempre con texto
  Midnight Green.
- Lilac Cloud, Orchid Mist, Sage Mist: fondos de tarjetas o bloques de
  categoría, asignados en rotación. Sin significado fijo: no existe
  "Peluquería = color X".
- Violet Dream: solo decorativo (bordes, íconos, ilustración); nunca
  fondo con texto.

## Mensajes (Django messages)

Fondo Blanco, texto Midnight Green, borde izquierdo de 4px del color
funcional, y una palabra o ícono que indique el tipo.

- Error `#B3261E` (borde 6.54 sobre blanco)
- Éxito Moss Green `#4F6650` (6.27)
- Advertencia `#9A6B1E` (4.67)

## Estados interactivos

- Hover/active: con texto blanco, oscurecer el fondo (Moss Green 15% =
  `#435744`, 7.82); con texto Midnight Green, aclararlo hacia Beige
  (Rosy Brown 15% = `#C29086`, 5.64). Rosy Brown oscurecido cae a 3.90.
- Foco: `:focus-visible` con outline 2px sólido Midnight Green y
  outline-offset 2px (el contorno queda sobre Beige: 13.22). El offset
  es obligatorio: pegado a Moss Green el contorno solo da 2.47.
  Nunca `outline: none` sin reemplazo.
- Disabled: atributo `disabled` real más aspecto inactivo; no comunicarlo
  solo con opacidad.

## Tipografía

- Encabezados (h1, h2, títulos destacados): `Fraunces, Georgia, serif`.
- Todo lo demás (cuerpo, navegación, botones, formularios, labels,
  precios): `"Work Sans", system-ui, -apple-system, "Segoe UI", sans-serif`.
- Mínimo 16px en texto de cuerpo e inputs (bajo 16px, iOS hace zoom
  automático al enfocar un input). line-height ≥ 1.5 en cuerpo.
- Jerarquía mediante tamaño, peso y espaciado, no sumando colores.
- La forma de cargar las fuentes se decide en el Design de catalog-ui.

---

> **Gobernanza:** Si en cualquier spec futuro una instrucción contradice este steering file, Kiro debe detenerse y pedir clarificación explícita antes de continuar — nunca resolver la contradicción por su cuenta ni ignorar silenciosamente ninguna fuente.
