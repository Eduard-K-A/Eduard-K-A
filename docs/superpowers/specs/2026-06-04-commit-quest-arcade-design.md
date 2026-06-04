# Commit Quest Arcade Design

## Goal

Add a unique retro RPG card at the bottom of the GitHub profile README. The card turns Eduard's public GitHub activity into a daily-updated character sheet and quest map.

## User Experience

The README section is titled **Commit Quest Arcade** and displays `assets/commit-quest.svg`.

The card presents:

- Character: **Eduard, the Full-Stack Adventurer**
- Level and XP derived from the current year's public contribution count
- Four character stats: Code, Build, Data, and AI
- Four abilities: TypeScript Strike, React Shield, Python Insight, and Cloud Deploy
- Current quest derived from the most recently updated non-fork public repository
- Four world areas: Web Woods, Mobile Marsh, Desktop Citadel, and AI Peaks
- Official GitHub achievements: Pull Shark, YOLO, and Quickdraw
- Contribution streak and last-updated date

## Visual Design

- Retro terminal RPG aesthetic compatible with GitHub dark and light themes
- `900 x 430` responsive SVG
- Dark navy background, neon cyan and green highlights, gold XP accents
- Pixel-inspired character and world map built from SVG primitives
- Clear text hierarchy and accessible contrast
- No external fonts, scripts, or images inside the SVG

## Data Model

The generator requests GitHub GraphQL data using `GITHUB_TOKEN`:

- Current-year contribution total
- Current contribution streak calculated from the contribution calendar
- Public repositories and their primary languages
- Most recently updated non-fork public repository

Calculated values:

- Level: `floor(totalContributions / 100) + 1`
- XP progress: `totalContributions % 100`
- Code stat: contribution-based score capped at 99
- Build stat: public repository-based score capped at 99
- Data stat: bonus from Python, R, Jupyter Notebook, and SQL-related repositories
- AI stat: bonus from repository names, descriptions, and languages associated with AI/ML work

## Generator

Create `scripts/generate-commit-quest.mjs`.

Responsibilities:

- Fetch GitHub data when `GITHUB_TOKEN` is available
- Calculate the character state
- Escape all dynamic SVG text
- Render the complete SVG
- Write `assets/commit-quest.svg`
- Fall back to a valid "awaiting quest sync" state if API data is unavailable

The fallback keeps the last committed SVG usable and allows local generation without credentials.

## Workflow

Create `.github/workflows/commit-quest.yml`.

The workflow:

- Runs daily and through manual dispatch
- Uses Node.js 20
- Grants `contents: write`
- Runs the generator with the repository `GITHUB_TOKEN`
- Commits `assets/commit-quest.svg` only when its content changes

## README Integration

Append a bottom section:

```markdown
## Commit Quest Arcade

<div align="center">
  <img src="./assets/commit-quest.svg" alt="Commit Quest Arcade character sheet generated from Eduard's GitHub activity" />
</div>
```

Include one short sentence explaining that the card updates daily from public GitHub activity.

## Reliability

- The committed SVG remains visible if the scheduled workflow fails.
- The workflow does not depend on third-party package registries or image services.
- Dynamic text is escaped before SVG rendering.
- Git commits occur only when generated output changes.

## Testing

Create `scripts/generate-commit-quest.test.mjs` using Node's built-in test runner.

Tests cover:

- Level and XP calculation
- Contribution streak calculation
- Dynamic SVG text escaping
- Valid fallback rendering
- Expected card sections in rendered SVG

## Validation

- `node --test scripts/generate-commit-quest.test.mjs` passes.
- `node scripts/generate-commit-quest.mjs --fallback` creates a valid SVG.
- Generated SVG contains no unescaped dynamic markup.
- Workflow YAML contains the schedule, manual trigger, token, and write permission.
- README references the committed SVG at the bottom.
