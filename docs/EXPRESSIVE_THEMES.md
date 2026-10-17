# Expressive theme redesign

The user's follow-up expands the original MVP: themes must radically change graphics, animation, button silhouettes, surfaces and visual composition, rather than mostly colors and type. The neutral Doodle2Design input wizard stays consistent; the generated Northwind demonstration receives the redesign.

## Acceptance criteria

- A nature direction produces a green botanical design with translucent tree illustrations, pill buttons, organic card shapes and calm motion.
- Cosmic, architectural and warm editorial directions use visibly different illustration systems, layouts, surfaces and interactions.
- The constrained `visuals` token group selects `motif`, `layout`, `motion`, `button_style` and `card_style`. No model-generated code or arbitrary CSS is accepted.
- Offline image analysis and real-model extraction both produce the extended vocabulary. Old JSON lacking `visuals` remains valid with neutral defaults.
- Generated scenes are local SVG, recolored deterministically from validated theme colors. No external fonts, assets or libraries are introduced.
- Live application, reset, before/after and CSS export include every new style. Applying another theme must remove the previous design completely.
- Motion includes entrances, decorative movement, hover and chart growth, with no flashing. OS reduced-motion settings disable it. Below-the-fold content remains accessible.
- Test nature, cosmic, architectural and editorial themes at mobile, intermediate iframe and desktop sizes; no overflow, console errors or interactive graphics blocking controls.

## Sources

- https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion
- https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API
- https://docs.pydantic.dev/latest/concepts/fields/
