# Aura Motion workspace

## Direction

A calm capture workspace, rather than a promotional landing page. The primary job is starting a camera-guided recording; the second is finding the saved data.

Taste's app draw selected **Framed sheet**, seed **107086022**: a pale frame surrounding a white workspace. The signature element is the existing body-landmark illustration, explicitly labelled as illustrative rather than live tracking.

The user's white, black, and sky-blue palette takes precedence over suggested library palettes. Manrope is self-hosted for its geometric character and readable numeric forms; this deliberately replaces the drawn IBM Plex face. Its OFL license is in `public/fonts/OFL-Manrope.txt`.

## Reference review

- [Awwwards minimal collection](https://www.awwwards.com/websites/minimal/): useful research categories include typography, content architecture, responsive design, and interaction design. Adaptation: restrained hierarchy and deliberate spacing, not marketing-site effects that interrupt capture.
- [Jahangir Hussain's healthcare dashboard on Dribbble](https://dribbble.com/shots/26383625-Health-Dashboard-UI-UX-Design): the designer describes a blue-and-white palette, modular cards, readable type, and clear actions. Adaptation: a quiet white workspace, a sky-blue capture study, compact recording summaries, and high-contrast controls.
- The uploaded Awwwards skill informs typography, spacing, motion preferences, and accessibility. Its separately referenced reference files were not supplied.

These are design directions, not copied layouts or downloaded artwork. Research used the pages and their descriptions; browser screenshot comparison was unavailable.

## System

- `src/workspace.css`: active foundation, font, palette, navigation, controls, focus, and responsive shell.
- `src/experience.css`: screen composition and component variants.
- The legacy `app.css` and `liquid-glass.css` are no longer imported.
- Ink: `#171b20`; frame: `#f3f7fa`; surface: `#fdfefe`; sky: `#82d4fb`; accessible blue: `#0877aa`.
- Glass is limited to floating capture controls and illustration annotations, retaining the user's request as an explicit exception to Taste's no-glass preference.
- Mobile navigation keeps visible labels. Keyboard focus and reduced-motion/transparency fallbacks remain available.

## Data and behavior

Recording counts come from the local API, not demonstration data. Sixty seconds describes the configured capture window, not a completed session. Saved status does not imply clinical validity. Unavailable joint-angle and symmetry calculations remain explicitly unavailable.

The backend and camera commands are unchanged. No camera was activated for the redesign.

## Verification

Run `npm run check` and `npm run build` from `frontend`. Review overview, studio, report tabs, recording search/filter, and guidance at desktop, tablet, and mobile widths when a browser is available. Browser-based screenshot and interaction checks are not yet completed.

Implementation checks: Svelte check completed with zero errors/warnings, production build completed, and `git diff --check` passed. The running UI and local font return HTTP 200; the session endpoint returns four recordings. The status endpoint currently reports no readable external USB camera; camera capture was not tested.

Taste's source lint in app mode reports zero failures and 21 warnings. Context labels and ordered preparation steps are retained for orientation; floating glass/shadows are retained for the requested treatment. This is source lint only, not a visual accessibility certification.
