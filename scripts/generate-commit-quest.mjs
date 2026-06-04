import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const USERNAME = process.env.GITHUB_REPOSITORY_OWNER || 'Eduard-K-A';
const OUTPUT_PATH = path.resolve('assets', 'commit-quest.svg');

export function calculateLevel(totalContributions) {
  const total = Math.max(0, Number(totalContributions) || 0);
  return {
    level: Math.floor(total / 100) + 1,
    xp: total % 100,
    xpToNextLevel: 100,
  };
}

export function calculateStreak(weeks, now = new Date()) {
  const days = weeks
    .flatMap((week) => week.contributionDays || [])
    .sort((a, b) => a.date.localeCompare(b.date));

  const byDate = new Map(days.map((day) => [day.date, day.contributionCount]));
  const cursor = new Date(Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate(),
  ));
  const today = cursor.toISOString().slice(0, 10);

  if (!byDate.get(today)) {
    cursor.setUTCDate(cursor.getUTCDate() - 1);
  }

  let streak = 0;
  while ((byDate.get(cursor.toISOString().slice(0, 10)) || 0) > 0) {
    streak += 1;
    cursor.setUTCDate(cursor.getUTCDate() - 1);
  }

  return streak;
}

export function escapeXml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

export function createFallbackState(now = new Date()) {
  return {
    username: USERNAME,
    level: 1,
    xp: 0,
    xpToNextLevel: 100,
    totalContributions: 0,
    streak: 0,
    stats: {
      code: 20,
      build: 20,
      data: 20,
      ai: 20,
    },
    currentQuest: {
      name: 'Awaiting quest sync',
      description: 'The next adventure appears after the daily GitHub sync.',
      url: `https://github.com/${USERNAME}`,
    },
    world: [
      { name: 'Web Woods', unlocked: true },
      { name: 'Mobile Marsh', unlocked: true },
      { name: 'Desktop Citadel', unlocked: true },
      { name: 'AI Peaks', unlocked: true },
    ],
    updatedAt: now.toISOString().slice(0, 10),
    synced: false,
  };
}

function clamp(value, minimum = 0, maximum = 99) {
  return Math.max(minimum, Math.min(maximum, Math.round(value)));
}

function countMatches(repositories, matcher) {
  return repositories.filter((repository) => matcher(repository)).length;
}

export function createActivityState(data, now = new Date()) {
  const user = data.user;
  const calendar = user.contributionsCollection.contributionCalendar;
  const repositories = user.repositories.nodes.filter(Boolean);
  const level = calculateLevel(calendar.totalContributions);
  const languages = repositories.map((repository) => repository.primaryLanguage?.name || '');
  const text = repositories
    .map((repository) => `${repository.name} ${repository.description || ''}`.toLowerCase())
    .join(' ');

  const dataRepos = countMatches(repositories, (repository) =>
    ['Python', 'R', 'Jupyter Notebook'].includes(repository.primaryLanguage?.name)
    || /data|analytics|database|sql|postgres/.test(`${repository.name} ${repository.description || ''}`.toLowerCase()));
  const aiRepos = countMatches(repositories, (repository) =>
    /ai|ml|machine learning|llm|agent|hugging face|groq|openai/.test(
      `${repository.name} ${repository.description || ''}`.toLowerCase(),
    ));

  const latest = repositories
    .filter((repository) => !repository.isFork)
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))[0];

  return {
    username: user.login,
    ...level,
    totalContributions: calendar.totalContributions,
    streak: calculateStreak(calendar.weeks, now),
    stats: {
      code: clamp(25 + calendar.totalContributions / 8 + languages.filter(Boolean).length),
      build: clamp(25 + repositories.length * 4),
      data: clamp(20 + dataRepos * 14),
      ai: clamp(20 + aiRepos * 16 + (/typescript|python/.test(text) ? 4 : 0)),
    },
    currentQuest: latest
      ? {
          name: latest.name,
          description: latest.description || `Continue building ${latest.name}.`,
          url: latest.url,
        }
      : {
          name: 'Explore a new repository',
          description: 'The quest board is ready for a new public project.',
          url: `https://github.com/${user.login}`,
        },
    world: [
      { name: 'Web Woods', unlocked: true },
      { name: 'Mobile Marsh', unlocked: repositories.some((repo) => /mobile|expo|native/i.test(`${repo.name} ${repo.description || ''}`)) },
      { name: 'Desktop Citadel', unlocked: repositories.some((repo) => /desktop|electron/i.test(`${repo.name} ${repo.description || ''}`)) },
      { name: 'AI Peaks', unlocked: aiRepos > 0 },
    ],
    updatedAt: now.toISOString().slice(0, 10),
    synced: true,
  };
}

function truncate(value, length) {
  const text = String(value ?? '');
  return text.length > length ? `${text.slice(0, length - 1)}…` : text;
}

function safeHttpsUrl(value, fallback) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' ? url.href : fallback;
  } catch {
    return fallback;
  }
}

function statBar(label, value, y, color) {
  const width = Math.round((value / 99) * 176);
  return `
    <text x="58" y="${y}" class="small label">${escapeXml(label)}</text>
    <rect x="118" y="${y - 10}" width="176" height="8" rx="4" fill="#17263b"/>
    <rect x="118" y="${y - 10}" width="${width}" height="8" rx="4" fill="${color}"/>
    <text x="304" y="${y}" class="tiny value">${value}</text>`;
}

function mapNode(x, y, label, unlocked, color) {
  const fill = unlocked ? color : '#26354a';
  const status = unlocked ? 'UNLOCKED' : 'LOCKED';
  return `
    <g>
      <rect x="${x}" y="${y}" width="118" height="52" rx="7" fill="#111d2e" stroke="${fill}" stroke-width="2"/>
      <circle cx="${x + 18}" cy="${y + 18}" r="7" fill="${fill}"/>
      <text x="${x + 32}" y="${y + 21}" class="tiny map-title">${escapeXml(label)}</text>
      <text x="${x + 14}" y="${y + 40}" class="micro ${unlocked ? 'open' : 'locked'}">${status}</text>
    </g>`;
}

export function renderSvg(state) {
  const safeQuestName = escapeXml(truncate(state.currentQuest.name, 34));
  const safeQuestDescription = escapeXml(truncate(state.currentQuest.description, 66));
  const xpWidth = Math.round((state.xp / state.xpToNextLevel) * 230);
  const syncLabel = state.synced ? 'ONLINE' : 'FALLBACK';
  const world = state.world;
  const username = encodeURIComponent(state.username);
  const profileUrl = `https://github.com/${username}`;
  const questUrl = safeHttpsUrl(state.currentQuest.url, profileUrl);
  const portfolioUrl = 'https://eduard-king.vercel.app';
  const mobileUrl = `https://github.com/search?q=mobile%20OR%20expo%20OR%20react-native%20user%3A${username}&type=repositories`;
  const desktopUrl = `https://github.com/search?q=electron%20OR%20desktop%20user%3A${username}&type=repositories`;
  const aiUrl = `https://github.com/search?q=ai%20OR%20ml%20OR%20data%20user%3A${username}&type=repositories`;
  const achievementsUrl = `${profileUrl}?tab=achievements`;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="430" viewBox="0 0 900 430" role="img" aria-labelledby="title description">
  <title id="title">Commit Quest Arcade</title>
  <desc id="description">A retro RPG character sheet generated from ${escapeXml(state.username)}'s public GitHub activity.</desc>
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d1726"/>
      <stop offset="1" stop-color="#101d31"/>
    </linearGradient>
    <linearGradient id="xp" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#f4c95d"/>
      <stop offset="1" stop-color="#ff7b72"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      text { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
      .title { fill: #7ee787; font-size: 24px; font-weight: 700; letter-spacing: 1px; }
      .subtitle { fill: #8b949e; font-size: 11px; }
      .panel-title { fill: #58a6ff; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
      .hero { fill: #f0f6fc; font-size: 16px; font-weight: 700; }
      .label { fill: #b1bac4; }
      .value { fill: #f0f6fc; text-anchor: end; }
      .small { font-size: 11px; }
      .tiny { font-size: 10px; }
      .micro { font-size: 8px; letter-spacing: .7px; }
      .map-title { fill: #f0f6fc; font-weight: 700; }
      .open { fill: #7ee787; }
      .locked { fill: #6e7681; }
      .ability { fill: #d2a8ff; font-size: 10px; }
      .quest { fill: #f4c95d; font-size: 12px; font-weight: 700; }
      .quest-note { fill: #b1bac4; font-size: 10px; }
      .click-target { fill: transparent; stroke: transparent; stroke-width: 2; cursor: pointer; pointer-events: all; }
      a:hover .click-target, a:focus .click-target { fill: #7ee78710; stroke: #7ee787; }
    </style>
  </defs>

  <rect width="900" height="430" rx="14" fill="#080f1c"/>
  <rect x="8" y="8" width="884" height="414" rx="10" fill="url(#panel)" stroke="#303d52" stroke-width="2"/>
  <path d="M8 54H892" stroke="#26354a"/>
  <text x="30" y="37" class="title" filter="url(#glow)">COMMIT QUEST ARCADE</text>
  <text x="870" y="34" class="micro ${state.synced ? 'open' : 'locked'}" text-anchor="end">● ${syncLabel} · ${escapeXml(state.updatedAt)}</text>
  <text x="870" y="49" class="micro label" text-anchor="end">OPEN CARD TO EXPLORE</text>

  <rect x="25" y="72" width="300" height="232" rx="10" fill="#0b1422" stroke="#26354a"/>
  <text x="43" y="96" class="panel-title">ADVENTURER</text>

  <g transform="translate(48 113)" shape-rendering="crispEdges">
    <rect x="16" y="0" width="28" height="8" fill="#58a6ff"/>
    <rect x="8" y="8" width="44" height="8" fill="#58a6ff"/>
    <rect x="16" y="16" width="28" height="28" fill="#e6b98a"/>
    <rect x="8" y="24" width="8" height="20" fill="#e6b98a"/>
    <rect x="44" y="24" width="8" height="20" fill="#e6b98a"/>
    <rect x="20" y="24" width="6" height="6" fill="#08111e"/>
    <rect x="34" y="24" width="6" height="6" fill="#08111e"/>
    <rect x="12" y="44" width="36" height="36" fill="#238636"/>
    <rect x="4" y="48" width="8" height="28" fill="#238636"/>
    <rect x="48" y="48" width="8" height="28" fill="#238636"/>
    <rect x="16" y="80" width="12" height="22" fill="#303d52"/>
    <rect x="32" y="80" width="12" height="22" fill="#303d52"/>
    <rect x="56" y="40" width="6" height="44" fill="#f4c95d"/>
    <rect x="52" y="36" width="14" height="6" fill="#f4c95d"/>
  </g>

  <text x="132" y="132" class="hero">Eduard</text>
  <text x="132" y="150" class="subtitle">THE FULL-STACK ADVENTURER</text>
  <text x="132" y="178" class="panel-title">LEVEL ${state.level}</text>
  <rect x="132" y="190" width="160" height="9" rx="4.5" fill="#17263b"/>
  <rect x="132" y="190" width="${Math.round((state.xp / state.xpToNextLevel) * 160)}" height="9" rx="4.5" fill="url(#xp)"/>
  <text x="132" y="216" class="tiny label">XP ${state.xp}/${state.xpToNextLevel}</text>
  <text x="292" y="216" class="tiny value">${state.totalContributions} contributions</text>
  ${statBar('CODE', state.stats.code, 238, '#58a6ff')}
  ${statBar('BUILD', state.stats.build, 256, '#7ee787')}
  ${statBar('DATA', state.stats.data, 274, '#d2a8ff')}
  ${statBar('AI', state.stats.ai, 292, '#ff7b72')}

  <rect x="25" y="318" width="300" height="86" rx="10" fill="#0b1422" stroke="#26354a"/>
  <text x="43" y="341" class="panel-title">ABILITY LOADOUT</text>
  <text x="43" y="363" class="ability">◆ TypeScript Strike</text>
  <text x="175" y="363" class="ability">◆ React Shield</text>
  <text x="43" y="385" class="ability">◆ Python Insight</text>
  <text x="175" y="385" class="ability">◆ Cloud Deploy</text>

  <rect x="342" y="72" width="533" height="118" rx="10" fill="#0b1422" stroke="#26354a"/>
  <text x="362" y="96" class="panel-title">CURRENT QUEST</text>
  <text x="362" y="124" class="quest">⚔ ${safeQuestName}</text>
  <text x="362" y="146" class="quest-note">${safeQuestDescription}</text>
  <rect x="362" y="162" width="230" height="8" rx="4" fill="#17263b"/>
  <rect x="362" y="162" width="${xpWidth}" height="8" rx="4" fill="url(#xp)"/>
  <text x="852" y="168" class="tiny value">${state.streak} day streak</text>

  <rect x="342" y="204" width="533" height="130" rx="10" fill="#0b1422" stroke="#26354a"/>
  <text x="362" y="228" class="panel-title">WORLD MAP</text>
  <path d="M474 270H480M598 270H604M722 270H728" stroke="#303d52" stroke-width="2" stroke-dasharray="3 3"/>
  ${mapNode(356, 244, world[0].name, world[0].unlocked, '#58a6ff')}
  ${mapNode(480, 244, world[1].name, world[1].unlocked, '#7ee787')}
  ${mapNode(604, 244, world[2].name, world[2].unlocked, '#f4c95d')}
  ${mapNode(728, 244, world[3].name, world[3].unlocked, '#d2a8ff')}

  <rect x="342" y="348" width="533" height="56" rx="10" fill="#0b1422" stroke="#26354a"/>
  <text x="362" y="371" class="panel-title">BADGES</text>
  <text x="362" y="391" class="tiny label">🦈 Pull Shark</text>
  <text x="482" y="391" class="tiny label">🎯 YOLO</text>
  <text x="570" y="391" class="tiny label">⚡ Quickdraw</text>
  <text x="852" y="391" class="tiny value">4 realms mapped</text>

  <a href="${escapeXml(profileUrl)}" target="_blank">
    <title>Open Eduard's GitHub profile</title>
    <rect class="click-target" x="25" y="72" width="300" height="232" rx="10"/>
  </a>
  <a href="${escapeXml(questUrl)}" target="_blank">
    <title>Open the current quest repository</title>
    <rect class="click-target" x="342" y="72" width="533" height="118" rx="10"/>
  </a>
  <a href="${escapeXml(portfolioUrl)}" target="_blank">
    <title>Explore Web Woods</title>
    <rect class="click-target" x="356" y="244" width="118" height="52" rx="7"/>
  </a>
  <a href="${escapeXml(mobileUrl)}" target="_blank">
    <title>Explore Mobile Marsh</title>
    <rect class="click-target" x="480" y="244" width="118" height="52" rx="7"/>
  </a>
  <a href="${escapeXml(desktopUrl)}" target="_blank">
    <title>Explore Desktop Citadel</title>
    <rect class="click-target" x="604" y="244" width="118" height="52" rx="7"/>
  </a>
  <a href="${escapeXml(aiUrl)}" target="_blank">
    <title>Explore AI Peaks</title>
    <rect class="click-target" x="728" y="244" width="118" height="52" rx="7"/>
  </a>
  <a href="${escapeXml(achievementsUrl)}" target="_blank">
    <title>Open GitHub achievements</title>
    <rect class="click-target" x="342" y="348" width="533" height="56" rx="10"/>
  </a>
</svg>`;
}

async function fetchGitHubData(token, username) {
  const from = `${new Date().getUTCFullYear()}-01-01T00:00:00Z`;
  const to = new Date().toISOString();
  const query = `
    query CommitQuest($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        login
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
        repositories(first: 100, privacy: PUBLIC, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            name
            description
            url
            updatedAt
            isFork
            primaryLanguage { name }
          }
        }
      }
    }`;

  const response = await fetch('https://api.github.com/graphql', {
    method: 'POST',
    headers: {
      Authorization: `bearer ${token}`,
      'Content-Type': 'application/json',
      'User-Agent': 'commit-quest-arcade',
    },
    body: JSON.stringify({
      query,
      variables: { login: username, from, to },
    }),
  });

  if (!response.ok) {
    throw new Error(`GitHub API returned ${response.status}`);
  }

  const payload = await response.json();
  if (payload.errors?.length || !payload.data?.user) {
    throw new Error(payload.errors?.[0]?.message || `GitHub user ${username} was not found`);
  }

  return payload.data;
}

export async function generateCommitQuest({
  fallback = false,
  token = process.env.GITHUB_TOKEN,
  username = USERNAME,
  outputPath = OUTPUT_PATH,
  now = new Date(),
} = {}) {
  let state;

  if (fallback || !token) {
    state = createFallbackState(now);
  } else {
    try {
      const data = await fetchGitHubData(token, username);
      state = createActivityState(data, now);
    } catch (error) {
      console.warn(`Commit Quest sync failed: ${error.message}. Rendering fallback card.`);
      state = createFallbackState(now);
    }
  }

  const svg = renderSvg(state);
  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${svg}\n`, 'utf8');
  return { state, svg, outputPath };
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const fallback = process.argv.includes('--fallback');
  const result = await generateCommitQuest({ fallback });
  console.log(`Commit Quest Arcade generated at ${result.outputPath}`);
}
