# Redrawing and fitting icons

The goal is a recognizable monochrome symbol that feels at home among the user's current native icons. Do not blindly impose dots, red accents, heavy outlines or a circular badge because the phone is a Nothing device.

## Reference and shape

- Prefer the selected app's extracted icon; otherwise use a clean user screenshot or supplied original. Confirm the intended brand/app, especially with similar names.
- Preserve a few distinctive features: silhouette, letter structure, direction or one meaningful internal cutout. Remove fine texture, distress, tiny text, excess outlines and details that collapse at launcher size.
- Keep negative spaces open. Use consistent stroke weight; avoid hairlines, tiny floating fragments and accidental asymmetry. Optical balance matters more than blindly centering the bounding box.
- For letters and motion lines, integrate extensions with the letter's real strokes. If the user wants progressive line lengths, specify the sequence explicitly rather than making the middle line longest by accident.
- Treat angle, stroke weight, overall aspect ratio and displayed scale as separate controls. A wider stroke does not necessarily fix a letter that is too flat. Record the user's requested invariant before each edit.
- Keep the original and approved revisions. Show the revised symbol before treating a new design as user-approved. Within already-authorized iterative installation, the user can judge on the phone; do not claim visual approval merely because a build passed.

## Output layers

Use a clean white symbol on black for a luminance mask, or actual transparent white artwork for alpha mode. Never use an opaque background as the monochrome layer: Android will tint it as a filled square. Do not bake in the colored circle, drop shadow, dark-mode background or screen wallpaper. The adaptive icon provides separate background and foreground, and the native launcher tints the monochrome foreground.

The included build converts only the prepared artwork into a layer; it is not an AI redraw service. The AI editor may require an account/credits, and its tool must be able to return a usable file. The user can supply artwork instead.

## Geometry and preview

Android layers use 108×108 dp. Start with a 60 dp longest visible edge and review the conservative central 66×66 dp safe area. The builder also rejects visible alpha outside a central 72 dp circular mask, but passing that circular check alone does **not** guarantee safety with every OEM shape or launcher animation. Prefer the smaller safe area when portability matters. A user-directed larger Nothing-only glyph needs a real-phone check.

Preview the prepared mask in a light and a dark circle at roughly 48–64 screen pixels. These are design previews, not device evidence. Inspect thin ends, counters, circular clipping and visual weight next to native icons. For a 110% request, multiply both width and height by 1.10 relative to the recorded baseline; do not enlarge the adaptive background or repeatedly compound 10% changes.

Example edit prompt:

> Simplify this supplied app mark into a clean white monochrome silhouette. Preserve [recognizable features]. Remove [specific small details]. Keep open counters, smooth edges and consistent substantial stroke weight. Center it optically with generous empty margins. No baked-in circular background, shadow, gradient, texture, small text or watermark. It must remain recognizable at 48 px. Change only [requested revision]; preserve [approved invariants].

The constraints are a starting point, not a fixed visual style. Retain user-approved quirks when they are intentional.

Source: [Android adaptive icon design](https://developer.android.com/develop/ui/compose/system/icon_design_adaptive).
