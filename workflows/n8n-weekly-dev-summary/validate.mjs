#!/usr/bin/env node
// Validates the n8n workflow JSON against acceptance criteria
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const wf = JSON.parse(readFileSync(resolve(__dir, 'workflow.json'), 'utf8'));

const results = [];
const pass = (msg) => results.push({ ok: true, msg });
const fail = (msg) => results.push({ ok: false, msg });

// 1. Valid JSON (already parsed)
pass('workflow.json is valid JSON');

// 2. Has name
wf.name ? pass(`name: "${wf.name}"`) : fail('missing name');

// 3. Schedule trigger with Friday 5pm cron
const schedule = wf.nodes.find(n => n.type === 'n8n-nodes-base.scheduleTrigger');
if (!schedule) { fail('missing scheduleTrigger node'); }
else {
  const expr = JSON.stringify(schedule.parameters);
  if (expr.includes('0 17 * * 5')) pass('cron trigger: 0 17 * * 5 (Friday 5pm)');
  else fail(`cron expression missing — got: ${expr.slice(0, 80)}`);
}

// 4. Fetches commits, issues, PRs
const httpNodes = wf.nodes.filter(n => n.type === 'n8n-nodes-base.httpRequest');
const urls = httpNodes.map(n => JSON.stringify(n.parameters)).join(' ');
urls.includes('commits') ? pass('fetches commits from GitHub API') : fail('no commits fetch');
urls.includes('issues')  ? pass('fetches issues from GitHub API')  : fail('no issues fetch');
urls.includes('pulls')   ? pass('fetches PRs from GitHub API')     : fail('no PRs fetch');

// 5. Calls Claude API with correct model
urls.includes('anthropic.com') ? pass('calls Anthropic API') : fail('no Anthropic API call');
const bodyStr = httpNodes.map(n => JSON.stringify(n.parameters.body || '')).join(' ');
bodyStr.includes('claude-sonnet-4-20250514') ? pass('model: claude-sonnet-4-20250514') : fail('wrong/missing model ID');

// 6. Discord delivery
JSON.stringify(wf).includes('discord')
  ? pass('Discord delivery node present') : fail('no Discord delivery');

// 7. Configurable variables
const cfgNode = wf.nodes.find(n => n.type === 'n8n-nodes-base.set');
const cfgStr = JSON.stringify(cfgNode?.parameters || '');
['GITHUB_OWNER', 'GITHUB_REPO', 'SUMMARY_LANGUAGE', 'ANTHROPIC_API_KEY', 'DISCORD_WEBHOOK_URL']
  .forEach(v => cfgStr.includes(v) ? pass(`config var: ${v}`) : fail(`missing config var: ${v}`));

// 8. EN/FR language support
JSON.stringify(wf).includes('FR') ? pass('FR language variant present') : fail('no FR language support');

// 9. Connections — enough sources wired
const connectedSrc = Object.keys(wf.connections);
connectedSrc.length >= wf.nodes.length - 1
  ? pass(`connections: ${connectedSrc.length} source(s) wired`)
  : fail('workflow has disconnected nodes');

// 10. Node count
wf.nodes.length >= 9
  ? pass(`${wf.nodes.length} nodes total`)
  : fail(`only ${wf.nodes.length} nodes — expected ≥9`);

// Summary
const passed = results.filter(r => r.ok).length;
const failed = results.filter(r => !r.ok).length;
results.forEach(r => console.log(`${r.ok ? '✅' : '❌'} ${r.msg}`));
console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
