# Design philosophy for Downstream's views

Source: `docs/DESIGN_PHILOSOPHY.md` in https://github.com/nikokoren/on_the_move, commit
03f8c7f1344883bd285e8cd1161c35a69ccd74a9 (branch `claude/vigilant-lamport-p6d600`, not yet on its
main), fetched 2026-09-30. Copied verbatim below as part A; re-fetch before relying on it. Part B
maps it onto Downstream: nothing in part B is approved by the author yet.

## Part A: On the Move's text (verbatim)

### Design philosophy (On the Move, single view), for other recipes

Written 2026-09-30 for the agent building "Downstream" (a stream map recipe). This is what we settled on in On the Move after two rounds of device feedback and a design review. Read the actual files before copying anything; the file names below point at the code.

### 1. Framework native, nothing else

- Only TRMNL Framework classes: no inline styles, no custom CSS (the owner calls extras "Extrawürstl").
- Before using a class, check that it exists in the framework's `plugins.css`. We guessed `outline--strong` and `overflow--hidden`, and neither exists.
- What we found useful:
  - Arbitrary sizes are pre-generated: `w--[Ncqw]` and `h--[Ncqh]` for N from 0 to 100, including the `portrait:` and `lg:` variants. `.layout` is the size container, so `cqw`/`cqh` are relative to the view.
  - `aspect--1/1`, `image image--cover`, `bg--canvas outline`, `rounded--full`, `stretch`, `no-shrink`, `flex--col flex--bottom` (bottom-anchored columns).
  - Text sizes, including their `lg:` variants: `label`, `title`, `description`.
- There is no title bar in any view: all the space goes to content.

### 2. Design for shapes, not for view names

- Four views times OG and X times two orientations gives 16 frames, which reduce to three shapes:
  - a wide strip: the half horizontal views in landscape;
  - a tall strip: half vertical in portrait;
  - a box: everything else.
- One template per view handles all its shapes:
  - `portrait:` classes switch the arrangement for portrait;
  - `lg:` classes give the X more (larger type, extra elements).
- Breakpoints come from the device model, not from a width. The OG is `md` and the X is `lg`, in both orientations. The renderer adds these classes; TRMNL's preview adds them after load, so anything hidden at load must be able to appear later.
- Everything the layouts share goes in the Shared tab: `{% template %}` components and one script. TRMNL prepends Shared to every layout.
- The script must allow two instances on one screen, because a mashup can hold our plugin twice. So it looks elements up relative to their scope and assigns ids at run time; it never relies on fixed ids.

### 3. The single view, per size (what the owner approved)

- **Full.** The map fills the screen.
  - A text box sits bottom left: canvas background plus outline, with the photo on its left.
  - An edge pill ("Destination: X · 2,012 km away") points at the destination only when the destination is not visible. "Not visible" means off the map, or under the text box, with a 16 px margin. The pill is placed afresh on every map draw.
  - If the pill's spot would land on the text box, the pill stacks above the box instead.
- **Half horizontal.** Photo and text on the left, map on the right. In portrait: the map on top, then photo and text below.
- **Half vertical.** Map on top, then the text, then the photo filling the rest. With the photo setting off, the map takes that space.
- **Quadrant.** The map, plus one strip of text: place and date. The photo appears only on the X in landscape, where the strip has room.
- **Text order**, everywhere:
  1. name (small, bold);
  2. place and state as the headline;
  3. destination;
  4. one fact;
  5. the date of the data.
  The date is always shown, so the recipe never claims to be live.
- Larger type on the X (`lg:label--large`, `lg:title--large`, `lg:description--large`), where there is room.
- Optional parts degrade cleanly: the photo off, no destination or no name must leave a layout with no gaps.

### 4. Maps

- Use `TRMNLMaps` with the `outline` preset: the leanest preset that still has water. The owner found roads distracting.
- Integer zoom only. The framework dithers fills only at an integer zoom; without that, a 2-bit screen shows the sea white. This was confirmed on the owner's device.
- Draw lines and dots with `TRMNLMaps.route` / `TRMNLMaps.dot`, never HTML markers: markers vanished under the dither layer.
  - A dashed or grey second line disappears at 1 bit. The line ahead is the same ink, only thinner.
- Keep a text fallback in place, so a map that fails to draw still shows the words.
- Check the data itself, not only the drawing. Our "double line" came from a usual-route table stitched across two years; the dot and the lines disagreed.

### 5. Words and settings

- The Worker sends every word, in English and German; the templates contain none.
- Settings get friendly, marketing-style names and clear descriptions. A switch is a boolean, on by default where that is the better experience. An empty value, sent before the settings are first saved, counts as the default.

### 6. How we worked with the owner

The sequence was:
1. brainstorm ideas;
2. rough wireframes on a canvas, which the owner comments on;
3. rendered mock-ups (variant templates through the real framework with real data), from which the owner picks;
4. build;
5. render sweep;
6. device feedback.

- Small, dated commits, with before and after numbers.
- A mock-up is a real render, never a drawing, once the direction is set.

### 7. Verification

- A render check (`template/render-check.mjs`) renders in real Chromium:
  - against TRMNL's own `plugins.css`/`plugins.js` and MapLibre;
  - with payloads the Worker builds from real data;
  - with the smaller views placed inside a real mashup;
  - with the breakpoint class the renderer would add.
- It sweeps every view on every screen and case, and fails when:
  - a map on screen is not drawn;
  - any text is cut off;
  - a list overflows;
  - the pill is shown without being needed, or needed without being shown;
  - the wrong number of maps is on screen.
- It can also add the size class late, to mimic TRMNL's preview.
- A Liquid pitfall: `divided_by` floors integers in Ruby Liquid (TRMNL) but not in liquidjs (the render check). Use `modulo`.
- Say "not confirmed on a device" until the owner has seen it on one.

### For Downstream

- The stream is the "animal":
  - its current state (level, flow, trend) is the headline;
  - upstream and downstream take the place of "where it came from" and "where it is heading";
  - an off-screen gauge or confluence gets the edge pill.
- Start from the four single layouts above and swap the photo slot for whatever image Downstream has, if any.
- Keep the map lean (the `outline` preset, integer zoom).
- Always show the time of the last reading.

## Part B: What this means for Downstream (approved 2026-09-30)

On the Move's own "For Downstream" section assumes a live stream recipe (levels, flow, gauges,
"time of the last reading"). Downstream has no live data: it shows the fixed path a raindrop takes
from a town (D8). So the parts carry over like this:

- **The "animal" is the raindrop's path.** The town is where it starts; the endpoint (sea, lake or
  sink) is the destination; the chain of streams and rivers is the route.
- **Text order**: superseded by D20 (2026-09-30): town (largest), path, "Ends in <endpoint>", distance; credits in the settings, not on screen. Earlier proposal, adapted from part A §3:
  1. town (small, bold);
  2. the endpoint as the headline ("Black Sea");
  3. the chain of rivers in order (the part most likely to overflow: up to ~15 steps; it needs a
     shortening rule, checked by the render sweep's "list overflows" case);
  4. one fact: the total distance (`total_km`);
  5. instead of "the date of the data": nothing live is claimed, so no timestamp. What must always be
     shown is the source credit (R16) and, where it applies, the estimate label (R10).
- **No edge pill** (author, 2026-09-30, D19): the raindrop isn't being tracked, so every view frames
  the whole path, town to endpoint, with `TRMNLMaps.fit()` on an integer zoom. The zoom is chosen so
  the whole path fits the part of the map not covered by the text box (fit padding on the box's
  side, as in the framework's Strava example); the render sweep fails any case where part of the
  path is off screen or under the box.
- **Text box over the map in every view** (author, 2026-09-30, wireframe comment): the half views and the quadrant also use a full-bleed map with the text box overlaid, like the full view, instead of On the Move's side-by-side or stacked layouts (less white space). The path is framed in the part of the map the box leaves free (D19).
- **Photo slot**: Downstream has no photo. The layouts from part A §3 without their photo slot
  ("photo off" case) are the starting point.
- **Map** (part A §4): `outline` preset, integer zoom, path drawn with `TRMNLMaps.route` from the
  payload's `polyline` (`decodePolyline`), start and end with `TRMNLMaps.dot`, one ink only, text
  fallback if the map fails. Very short paths (Limhamn: one 1.7 km stream) need a sensible minimum
  frame.
- **Words**: every word comes from the payload/LOCALES in English and German (R13); none in
  templates.
- **Liquid**: the Polling URL uses `divided_by` on whole numbers (`recipe/polling_url.liquid`). That
  is safe in TRMNL's Ruby Liquid (confirmed on TRMNL 2026-09-29) but would not floor in liquidjs;
  keep it out of any liquidjs render check, or rewrite it with `modulo` if one ever needs it.
- **Process** (part A §6) applies as is: brainstorm, wireframes, real-render mock-ups with real town
  files, build, render sweep, device feedback.
