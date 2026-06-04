import assert from 'node:assert/strict';
import test from 'node:test';

import {
  calculateLevel,
  calculateStreak,
  createFallbackState,
  escapeXml,
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
  assert.match(svg, /Web Woods/);
  assert.match(svg, /Pull Shark/);
  assert.match(svg, /class="small label">AI</);
  assert.match(svg, /Build &lt;Vault&gt;/);
  assert.match(svg, /Ship &amp; learn/);
  assert.doesNotMatch(svg, /Build <Vault>/);
  assert.doesNotMatch(svg, /H550 310/);
});
