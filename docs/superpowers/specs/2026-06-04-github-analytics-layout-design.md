# GitHub Analytics Layout Design

## Goal

Improve the GitHub Analytics section by placing the wide contribution details card on the left and stacking the stats and language cards on the right.

## Layout

- Use a centered, borderless HTML table because GitHub strips unsupported flexbox styling.
- Left cell: profile details card, vertically aligned to the top.
- Right cell: stats card followed by repositories-per-language card.
- Keep the `github_dark` theme on all cards.
- Use responsive image widths so the layout remains readable within GitHub's profile README container.

## Validation

- Confirm the table tags are balanced.
- Confirm the left column contains only the profile details card.
- Confirm the right column contains the stats card above the language card.
- Confirm all analytics endpoints return valid SVG responses.
