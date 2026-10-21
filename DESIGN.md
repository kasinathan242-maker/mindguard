# Design System: MindGuard AI (Google Stitch Specification)

> Semantic Design System and Visual Architecture specification for Google Stitch screen generation and frontend engineering. Encodes an Awwwards-tier, restorative sanctuary aesthetic for mental wellbeing with zero AI generic clichés.

---

## 1. Visual Theme & Atmosphere
- **Atmosphere:** Restorative Serenity & Clinical Architecture. A tactile, private sanctuary for the mind that balances deep medical trust with warm, organic calm.
- **Density Dial:** `4 / 10` (Art Gallery Airy & Deliberate). Generous macro-whitespace (`py-28` to `py-36`) that allows sensitive mental health information to breathe without feeling sparse or clinical.
- **Variance Dial:** `8 / 10` (Asymmetrical Bento & Split-Screen Rhythm). Offset cards, dynamic bento grids, and layered hardware bezels that deliberately eliminate boring, repetitive corporate card rows.
- **Motion Dial:** `6 / 10` (Kinetic Weight & Somatic Spring Physics). Perpetual somatic micro-interactions (e.g. rhythmic box-breathing orb with 4-7-8 timing, magnetic pill buttons, smooth staggered entry waterfalls).

---

## 2. Color Palette & Roles

Strict, high-contrast, restorative botanical palette. The "AI Purple/Blue Neon" aesthetic is strictly BANNED. Pure black (`#000000`) is never used.

### Light Mode (Warm Sanctuary)
- **Canvas Oatmeal** (`#FBF9F5`) — Primary background surface. Warm, natural paper tone that minimizes eye strain and reduces cortisol.
- **Porcelain Surface** (`#FFFFFF`) — Card and container fill. Clean, pure elevated resting surface.
- **Surface Sunk** (`#F0EDE6`) — Recessed containers, input fields, and nested bezel trays.
- **Forest Ink** (`#141E18`) — Primary text. Ultra-deep botanical charcoal with high legibility (14.2:1 contrast ratio against canvas).
- **Muted Sage** (`#4E5F55`) — Secondary text, subtitles, and explanatory guidance.
- **Whisper Line** (`rgba(20, 30, 24, 0.08)`) — 1px hairline structural dividers and outer bezels.
- **Botanical Emerald Accent** (`#1D5A46`) — Primary interactive accent for CTAs, active states, and focus rings. High-agency, restorative green.
- **Accent Soft** (`#E2ECE6`) — Tonal pill badges, active selections, and highlight halos.
- **Crisis Crimson** (`#BA1A1A`) — Restricted exclusively to crisis emergency interventions and safety cards. Never used for standard UI buttons.

### Dark Mode (Deep Obsidian Forest)
- **Obsidian Canvas** (`#0B110E`) — Deepest OLED botanical charcoal background (not `#000000`).
- **Dark Surface** (`#131B17`) — Elevated card plates.
- **Dark Sunk** (`#080D0B`) — Recessed trays and nested double bezels.
- **Luminous Ink** (`#E8EFEA`) — Primary display text.
- **Luminous Muted** (`#98AAA0`) — Secondary text and labels.
- **Dark Line** (`rgba(232, 239, 234, 0.08)`) — Delicate glass hairlines.
- **Dark Accent Emerald** (`#4ADE80`) — Crisp, luminous mint accent for high visibility in dark mode.

---

## 3. Typographic Architecture

Typography pairs humanistic, editorial warmth with crisp, technical precision. Generic corporate fonts like `Inter`, `Roboto`, and `Arial` are strictly BANNED.

- **Display & Headlines:** `Bricolage Grotesque Variable` (Latin) paired seamlessly with `Noto Sans Tamil Variable`. Tight tracking (`tracking-tight`), strong weight contrast (SemiBold to Bold), controlled scale via `clamp()`. Headings deliver presence through typographic personality rather than pure visual loudness.
- **Body & Controls:** `Plus Jakarta Sans Variable`. Modern, open aperture, highly legible at both 14px and 18px. Generous leading (`leading-relaxed`), restricted line length (maximum 60–65 characters per line).
- **Numbers & Metrics:** Tabular Figures (`tabular-nums`) with `JetBrains Mono` or monospace styling for clinical assessment scores (PHQ-9 / GAD-7) and biometric timestamps.
- **Banned Typography:** No `Inter`, no `Helvetica`, no standard serif fonts (`Times New Roman`, `Georgia`, `Garamond`). No centered hero headlines on desktop.

---

## 4. Component Stylings & Micro-Aesthetics

### A. The "Double-Bezel" Hardware Architecture
Cards never float flatly against the canvas. Every container uses a physical, machined enclosure:
- **Outer Shell:** Tinted tray (`p-1.5`, `rounded-[2rem]`, `bg-ink/[0.03]` in light, `bg-white/[0.03]` in dark) with a hairline outer ring (`ring-1 ring-line`).
- **Inner Core:** Concentric inner plate (`rounded-[calc(2rem-0.375rem)]`, `bg-surface`) featuring an inner specular highlight (`shadow-[inset_0_1px_1px_rgba(255,255,255,0.4)]` in light mode, `rgba(255,255,255,0.08)` in dark mode).

### B. Nested Island Buttons & CTAs
- **Primary CTAs:** Fully rounded pill (`rounded-full`, `px-6 py-3.5`). Tactile spring feedback on active press (`active:scale-[0.97]`).
- **Trailing Icon Capsule:** Action arrows never sit naked beside text. They are nested inside an internal circular capsule (`size-8 rounded-full bg-accent-ink/15`) flush with the button's right inner padding that translates diagonally on hover (`group-hover:translate-x-1 group-hover:-translate-y-px`).

### C. Floating Island Navigation
- Floating glass pill detached from the top edge (`mt-4 sm:mt-6`, `mx-auto`, `w-max`, `max-w-5xl`, `rounded-full`).
- Layered with heavy frosted backdrop (`backdrop-blur-2xl bg-surface/80 ring-1 ring-line`).
- Live crisis button (`Need Help?`) integrated directly into the pill for immediate, friction-free emergency access.

### D. Somatic Breathing Engine
- Interactive, rhythmic breathing orb embedded directly in the hero for immediate physical grounding.
- Micro-haptic pulsation with subtle concentric atmospheric rings (`ring-accent/15`).
- Multi-phase rhythm support: Box Breathing (4s Inhale, 4s Hold, 4s Exhale, 4s Hold) and Relaxing (4s Inhale, 7s Hold, 8s Exhale).

### E. Clinical Assessment & Screening Tiles
- Radio option pills that highlight with tactile spring animations upon selection.
- Clear visual progress indicator with animated meter, eliminating test anxiety.

---

## 5. Layout Principles & Responsive Hierarchy

- **Asymmetrical Bento Grids:** Hero and feature sections break traditional 3-column Bootstrap templates. Uses a 12-column masonry grid with alternating aspect ratios (`col-span-7` narrative hero next to `col-span-5` somatic breathing module).
- **Mobile-First Collapse:** Below `768px`, all multi-column layouts strictly collapse to a single clean vertical flow (`grid-cols-1`, `gap-6`, `px-4`). No horizontal scroll under any circumstances.
- **Viewport Height Discipline:** Full-height views strictly use `min-h-[100dvh]` — never `h-screen`, preventing mobile Safari navigation bar jumps.
- **Whitespace Rhythm:** Double standard padding across major vertical sections (`py-24` to `py-36` on desktop, `py-16` on mobile).

---

## 6. Motion Philosophy & Spring Dynamics

All motion simulates physical weight and mass rather than artificial linear slides:
- **Physics Engine:** Spring physics curve `cubic-bezier(0.32, 0.72, 0, 1)` and ease-out soft `[0.16, 1, 0.3, 1]`.
- **Staggered Entry Waterfalls:** Elements enter through gentle, heavy fade-up transitions (`translate-y-6 opacity-0` resolving to `translate-y-0 opacity-100` with 80ms stagger delay).
- **GPU Safety:** Animations occur exclusively on `transform` and `opacity`. Layout properties (`top`, `left`, `width`, `height`) are never animated.
- **Accessibility:** Full respect for `prefers-reduced-motion: reduce`. Disables continuous motion and collapses transitions to instant opacity toggles.

---

## 7. Anti-Patterns (Explicitly Banned)

1. ❌ **No Emojis Anywhere** — Replace with ultra-crisp line icons (Phosphor Light / Bold).
2. ❌ **No Inter or Default System Fonts** — Force `Bricolage Grotesque` and `Plus Jakarta Sans`.
3. ❌ **No Generic Symmetrical 3-Card Grids** — Use asymmetric Bento or 2-column zig-zag.
4. ❌ **No Neon or AI-Purple Glows** — Retain natural botanical emerald and oatmeal neutrals.
5. ❌ **No Pure Black (`#000000`)** — Use deep botanical charcoal `#0B110E`.
6. ❌ **No AI Copywriting Clichés** — Ban words like "Seamless", "Elevate", "Next-Gen", "Revolutionize", "Unleash".
7. ❌ **No Placeholder Filler Text** — No "Scroll to explore", no bouncing chevrons.
8. ❌ **No Overlapping Text/Images** — Every element maintains its own clear spatial zone.
