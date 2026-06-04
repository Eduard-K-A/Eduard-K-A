# GitHub Profile README Design

## Goal

Refactor the GitHub profile README into a balanced, recruiter-first developer profile that presents Eduard King Anterola's strongest work and professional direction before visual GitHub analytics.

## Audience

- Recruiters and hiring managers reviewing internship and entry-level candidates
- Engineering teams evaluating full-stack, mobile, desktop, and AI-focused work
- Developers interested in projects, collaboration, or professional networking

## Content Source

Use `context.md` as the source of truth for professional details, project descriptions, leadership roles, technical skills, contact links, and opportunity interests. Keep dynamic GitHub widgets tied to the `Eduard-K-A` username.

## Information Architecture

The README will use this section order:

1. Centered hero
2. About me
3. Featured projects
4. Tech stack
5. Leadership and current focus
6. GitHub analytics
7. Contact

This order prioritizes professional context and demonstrated work before statistics and decorative elements.

## Section Design

### Centered Hero

Display:

- Eduard King Anterola
- "Computer Science Student · Full-Stack Developer · Aspiring ML Engineer"
- A concise statement covering full-stack, mobile, desktop, and AI-oriented development
- Compact badges linking to portfolio, LinkedIn, email, and GitHub
- Profile-view counter

The hero should be centered and compatible with both light and dark GitHub themes.

### About Me

Use short bullets that communicate:

- Computer Science studies at De La Salle Lipa
- Current Back-End Developer Head role at AWS Learning Club
- Former DevOps Head role at DLSL AnimoDev
- Current AI, machine learning, data engineering, and LLMOps learning focus
- Openness to internships, freelance work, entry-level roles, and remote opportunities

### Featured Projects

Feature these four projects:

| Project | Primary Value | Core Technologies |
| --- | --- | --- |
| Ely Sales Agent | Top 10 Agora-sponsored hackathon finalist; real-time AI voice sales assistant | TypeScript, Electron, Agora, Groq API, SQLite |
| The Vault | Offline-first mobile POS for retail and multi-branch teams | TypeScript, React Native, Expo, Supabase, PowerSync, SQLite |
| TaskOverflow | Minimal local-first desktop task manager | TypeScript, Electron, React, SQLite |
| CleanOps | Full-stack service marketplace with geolocation and real-time features | Next.js, TypeScript, Supabase, PostGIS, Tailwind CSS |

Each project entry should use an impact-focused description and a compact technology line. Include a live demo link only when `context.md` provides one. Do not invent repository links.

### Tech Stack

Group badges into readable categories:

- Languages
- Frontend and mobile
- Backend and databases
- AI and data
- Tools and deployment

Use shields.io badges with a consistent flat style. Include technologies supported by `context.md`, while avoiding an excessively long or repetitive badge wall.

### Leadership and Current Focus

Summarize:

- Back-End Developer Head, AWS Learning Club
- Former DevOps Head, DLSL AnimoDev
- Current learning in AI engineering, machine learning, data engineering, Hugging Face, MLOps, and LLMOps

Keep this section concise and outcome-oriented.

### GitHub Analytics

Include:

- GitHub stats
- Contribution streak
- Top languages
- GitHub trophies
- Top contributed repositories

Use a consistent transparent or dark-compatible theme. Keep analytics below professional content. Remove the random developer quote because it does not support the recruiter-first narrative.

### Contact

Close with direct links to:

- Portfolio
- LinkedIn
- Email
- GitHub

## Visual Style

- Balanced and professional rather than highly decorative
- Clear heading hierarchy and generous spacing
- Centered hero, left-aligned content sections
- Consistent badge style and analytics theme
- Limited use of emoji as section markers
- No animated typing banner or unrelated decorative widgets

## Constraints

- Modify only `README.md` for the implementation.
- Preserve accurate facts from `context.md`.
- Do not add unsupported claims, repository URLs, or social links.
- Keep all external widget URLs valid Markdown image or link syntax.
- Ensure the README remains useful if a third-party stats widget is temporarily unavailable.

## Validation

- Confirm every requested content category is present: stats, badges, socials, tech stack, and trophies.
- Confirm all featured projects and professional claims match `context.md`.
- Confirm Markdown links and image syntax are structurally valid.
- Confirm the GitHub username is consistently `Eduard-K-A`.
- Confirm the random quote widget is removed.
- Review the rendered hierarchy for scanning: hero, professional context, projects, stack, leadership, analytics, contact.
