# Compact GitHub Analytics Design

## Goal

Redesign the GitHub Analytics section to eliminate wasted space and preserve the cards' natural aspect ratios.

## Layout

- First row: the `700 x 200` profile-details contribution card at full width.
- Second row: the `340 x 200` stats and repositories-per-language cards side by side.
- Use centered HTML markup without fixed height scaling.
- Keep the `github_dark` theme.

## Validation

- Confirm all three cards are present.
- Confirm no analytics image has a fixed `height` attribute.
- Confirm the profile-details card appears before the two smaller cards.
- Confirm all card URLs return valid SVG responses.
