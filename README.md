<div align="center">

<img src="./ascii.svg" width="460" alt="Eduard King Anterola"/>

<img src="./stats.svg" width="620" alt="Contributions in the last year"/>

[portfolio](https://eduard-king.vercel.app) &nbsp;·&nbsp;
[linkedin](https://www.linkedin.com/in/eduard-king-anterola/) &nbsp;·&nbsp;
[email](mailto:eduardkinganterola@gmail.com)

</div>

<img src="./hd-about.svg" width="620" alt="about"/>

> CS student at De La Salle Lipa, in Lipa City, Philippines.<br>
> Ship it, watch someone use it, then decide what it should have been.

Back-end lead at the AWS Learning Club, DevOps head at AnimoDev before that. Most<br>
of what I build is full-stack — web, mobile, desktop — and lately I have been<br>
pulling that toward AI engineering: Python, statistics, Hugging Face, LLMOps.<br>
Open to internships, freelance work, and entry-level roles.

<img src="./hd-stack.svg" width="620" alt="stack"/>

<samp>typescript &nbsp; python &nbsp; react &nbsp; next.js &nbsp; react native &nbsp; node &nbsp; supabase &nbsp; postgres &nbsp; postgis &nbsp; sqlite &nbsp; electron &nbsp; tailwind &nbsp; git</samp>

<img src="./hd-projects.svg" width="620" alt="projects"/>

**[studdybuddy](https://github.com/Eduard-K-A/studdybuddy)** &nbsp;·&nbsp; <samp>typescript</samp><br>
Upload your course material and an agent quizzes you on it. Reading is easy to<br>
fake; being asked is not.

**[agora](https://github.com/Eduard-K-A/agora)** &nbsp;·&nbsp; <samp>typescript, electron, groq</samp><br>
Real-time voice sales assistant that listens to a live call and feeds the rep<br>
what they need. Top 10 finalist at an Agora-sponsored hackathon.

**[cleanOps](https://github.com/Eduard-K-A/cleanOps)** &nbsp;·&nbsp; <samp>next.js, supabase, postgis</samp><br>
Marketplace for home-service work, matched by real geolocation rather than a<br>
postcode field. Realtime subscriptions, multi-role auth, mock escrow.<br>
[Mobile client](https://github.com/Eduard-K-A/cleanOps-mobile) in React Native.

**[TaskOverflow](https://github.com/Eduard-K-A/TaskOverflow)** &nbsp;·&nbsp; <samp>electron, sqlite</samp><br>
Local-first desktop task manager. Groups, subtasks, deadlines, no account.

<img src="./hd-stats.svg" width="620" alt="stats"/>

<div align="center">

<img src="./streak.svg" width="620" alt="Current and longest streak"/>

<img src="./langs.svg" width="620" alt="Top languages by bytes and by repository"/>

<img src="./year.svg" width="620" alt="The last year, one character per day"/>

</div>

<img src="./hd-about-this-page.svg" width="620" alt="about this page"/>

Every graphic here is generated, not embedded from anyone else's server.<br>
`ascii.svg` is a photo pushed through a character ramp by<br>
[`scripts/make_portrait.py`](scripts/make_portrait.py); the stat graphics and<br>
these section headings are drawn by [a scheduled action](.github/workflows/stats.yml)<br>
straight from the GitHub GraphQL API, once a day, committing only what changed.

They animate with SMIL inside the SVG, because GitHub strips scripts from<br>
READMEs — and since nothing loads from a third party, nothing here can<br>
rate-limit or go dark. The headings are SVGs for the same reason: GitHub also<br>
strips CSS, so an image is the only way to put this page's own typeface on them.

The typeface is [JetBrains Mono](scripts/fonts), subset to just the characters<br>
each graphic draws and inlined as base64. That isn't only for looks: the<br>
portrait's grid assumes an advance width of exactly 0.600 em, and a viewer whose<br>
default monospace is narrower would otherwise see it squeezed.

Colours come from CSS custom properties behind a `prefers-color-scheme` query, so<br>
one file suits both GitHub themes. Density in the portrait has to mean *the<br>
subject*, not *the bright half of the frame*, so which end of the ramp gets the<br>
ink is measured off the photo — centre against edges — rather than assumed. Ink<br>
colour then flips with the theme on its own, and I stay drawn either way.

Language totals cover public, non-fork repositories only. `year.svg` uses the<br>
portrait's character ramp: `:` `+` `#` `@`, quiet to loud, with the cut-offs set<br>
at quartiles of my own active days rather than fixed counts.
