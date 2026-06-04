import assert from 'node:assert/strict';
import test from 'node:test';

import {
  calculateLevel,
  calculateStreak,
  createFallbackState,
  escapeXml,
  rankTopRepositories,
  renderSvg,
} from './generate-commit-quest.mjs';

test('calculateLevel converts contributions into levels and XP', () => {
  assert.deepEqual(calculateLevel(245), {
    level: 3,
    xp: 45,
    xpToNextLevel: 100,
  });
});

test('calculateStreak counts consecutive days ending today', () => {
  const weeks = [
    {
      contributionDays: [
        { date: '2026-06-01', contributionCount: 2 },
        { date: '2026-06-02', contributionCount: 1 },
        { date: '2026-06-03', contributionCount: 4 },
        { date: '2026-06-04', contributionCount: 3 },
      ],
    },
  ];

  assert.equal(calculateStreak(weeks, new Date('2026-06-04T12:00:00Z')), 4);
});

test('calculateStreak allows the latest contribution to be yesterday', () => {
  const weeks = [
    {
      contributionDays: [
        { date: '2026-06-01', contributionCount: 0 },
        { date: '2026-06-02', contributionCount: 1 },
        { date: '2026-06-03', contributionCount: 1 },
        { date: '2026-06-04', contributionCount: 0 },
      ],
    },
  ];

  assert.equal(calculateStreak(weeks, new Date('2026-06-04T12:00:00Z')), 2);
});

test('escapeXml protects dynamic SVG text', () => {
  assert.equal(
    escapeXml('Quest <script> & "ship"'),
    'Quest &lt;script&gt; &amp; &quot;ship&quot;',
  );
});

test('createFallbackState creates an awaiting-sync quest', () => {
  const state = createFallbackState(new Date('2026-06-04T12:00:00Z'));

  assert.equal(state.currentQuest.name, 'Awaiting quest sync');
  assert.equal(state.level, 1);
  assert.equal(state.updatedAt, '2026-06-04');
});

test('renderSvg contains required arcade sections and escaped quest data', () => {
  const state = {
    ...createFallbackState(new Date('2026-06-04T12:00:00Z')),
    currentQuest: {
      name: 'Build <Vault>',
      description: 'Ship & learn',
      url: 'https://github.com/Eduard-K-A',
    },
  };

  const svg = renderSvg(state);

  assert.match(svg, /Commit Quest Arcade/);
  assert.match(svg, /TypeScript Strike/);
  assert.match(svg, /TOP REPOSITORIES/);
  assert.match(svg, /Ely Sales Agent/);
  assert.match(svg, /Pull Shark/);
  assert.match(svg, /class="small label">AI</);
  assert.match(svg, /Build &lt;Vault&gt;/);
  assert.match(svg, /Ship &amp; learn/);
  assert.doesNotMatch(svg, /Build <Vault>/);
  assert.doesNotMatch(svg, /H550 310/);
});

test('renderSvg includes clickable profile, quest, repository, and achievement destinations', () => {
  const state = {
    ...createFallbackState(new Date('2026-06-04T12:00:00Z')),
    currentQuest: {
      name: 'The Vault',
      description: 'Ship the next release',
      url: 'https://github.com/Eduard-K-A/the-vault',
    },
    world: [
      { name: 'Repo One', language: 'TypeScript', url: 'https://github.com/Eduard-K-A/repo-one' },
      { name: 'Repo Two', language: 'Python', url: 'https://github.com/Eduard-K-A/repo-two' },
      { name: 'Repo Three', language: 'C++', url: 'https://github.com/Eduard-K-A/repo-three' },
      { name: 'Repo Four', language: 'R', url: 'https://github.com/Eduard-K-A/repo-four' },
    ],
  };

  const svg = renderSvg(state);

  assert.match(svg, /href="https:\/\/github\.com\/Eduard-K-A\/the-vault"/);
  assert.match(svg, /href="https:\/\/github\.com\/Eduard-K-A\/repo-one"/);
  assert.match(svg, /href="https:\/\/github\.com\/Eduard-K-A\/repo-two"/);
  assert.match(svg, /href="https:\/\/github\.com\/Eduard-K-A\/repo-three"/);
  assert.match(svg, /href="https:\/\/github\.com\/Eduard-K-A\/repo-four"/);
  assert.match(svg, /tab=achievements/);
  assert.match(svg, /OPEN CARD TO EXPLORE/);
});

test('renderSvg falls back to the GitHub profile for unsafe quest URLs', () => {
  const state = {
    ...createFallbackState(new Date('2026-06-04T12:00:00Z')),
    currentQuest: {
      name: 'Unsafe quest',
      description: 'Must not become a script link',
      url: 'javascript:alert(1)',
    },
  };

  const svg = renderSvg(state);

  assert.doesNotMatch(svg, /javascript:/);
  assert.match(svg, /href="https:\/\/github\.com\/Eduard-K-A"/);
});

test('rankTopRepositories uses balanced popularity and recency scoring', () => {
  const repositories = [
    {
      name: 'popular',
      url: 'https://github.com/Eduard-K-A/popular',
      isFork: false,
      stargazerCount: 3,
      forkCount: 1,
      updatedAt: '2026-01-01T00:00:00Z',
      primaryLanguage: { name: 'TypeScript' },
    },
    {
      name: 'fresh',
      url: 'https://github.com/Eduard-K-A/fresh',
      isFork: false,
      stargazerCount: 1,
      forkCount: 0,
      updatedAt: '2026-05-25T00:00:00Z',
      primaryLanguage: { name: 'Python' },
    },
    {
      name: 'Eduard-K-A',
      url: 'https://github.com/Eduard-K-A/Eduard-K-A',
      isFork: false,
      stargazerCount: 100,
      forkCount: 100,
      updatedAt: '2026-06-04T00:00:00Z',
      primaryLanguage: { name: 'Markdown' },
    },
    {
      name: 'forked',
      url: 'https://github.com/Eduard-K-A/forked',
      isFork: true,
      stargazerCount: 100,
      forkCount: 100,
      updatedAt: '2026-06-04T00:00:00Z',
      primaryLanguage: { name: 'Rust' },
    },
  ];

  const ranked = rankTopRepositories(
    repositories,
    'Eduard-K-A',
    new Date('2026-06-04T12:00:00Z'),
  );

  assert.deepEqual(ranked.map((repository) => repository.name), ['popular', 'fresh']);
  assert.equal(ranked[0].score, 48);
  assert.equal(ranked[1].score, 33);
});

test('fallback state provides four named repository nodes', () => {
  const state = createFallbackState(new Date('2026-06-04T12:00:00Z'));

  assert.deepEqual(
    state.world.map((repository) => repository.name),
    ['Ely Sales Agent', 'The Vault', 'TaskOverflow', 'CleanOps'],
  );
});

test('renderSvg links repository map nodes directly to repositories', () => {
  const state = {
    ...createFallbackState(new Date('2026-06-04T12:00:00Z')),
    world: [
      { name: 'Repo One', language: 'TypeScript', url: 'https://github.com/Eduard-K-A/repo-one' },
      { name: 'Repo Two', language: 'Python', url: 'https://github.com/Eduard-K-A/repo-two' },
      { name: 'Repo Three', language: 'C++', url: 'https://github.com/Eduard-K-A/repo-three' },
      { name: 'Repo Four', language: 'R', url: 'https://github.com/Eduard-K-A/repo-four' },
    ],
  };

  const svg = renderSvg(state);

  assert.match(svg, /Repo One/);
  assert.match(svg, /TypeScript/);
  assert.match(svg, /href="https:\/\/github\.com\/Eduard-K-A\/repo-one"/);
  assert.doesNotMatch(svg, /Web Woods/);
});
