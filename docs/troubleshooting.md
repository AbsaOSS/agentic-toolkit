# Troubleshooting

Fixes for known setup issues, plus setup guides for specific skills.

---

## Skill not activating

The `description` field is the **sole activation signal** — the agent never reads a skill's body until it decides
the description matches the current task.

Steps to diagnose:

1. Inside a Copilot CLI session, run `/skills list` to confirm the skill is loaded and inspect its description.
2. Outside the CLI, run `npx skills list` or open the skill's `SKILL.md` directly.
3. Rephrase your prompt to include keywords that appear in the description — both formal terms and casual phrasings.
4. If the skill still won't trigger, consider improving the description. See the
   [Contributing Guide](../CONTRIBUTING.md#3-writing-the-description) for guidance.

## SSL / certificate errors (corporate proxy)

If `npx skills` fails with SSL or certificate errors, you are likely behind a corporate proxy or TLS inspection
tool. Configure npm to trust your organisation's certificate bundle:

```bash
npm config set cafile /path/to/your/ca-bundle.pem
```

This writes the setting to `~/.npmrc`. Obtain the certificate bundle from your organisation's IT or security team.

## Skill removal doesn't update the lock file

`npx skills remove` removes the skill directory but does not always clean up internal state. If you see stale
references after removing a skill, delete the corresponding entry from the skills lock file (typically
`.skills-lock.json`) manually. See
[Managing AI Agent Skills with npx skills](https://dev.to/toyama0919/managing-ai-agent-skills-with-npx-skills-a-practical-guide-2an8)
for a detailed walkthrough.

## Skills directory location varies

The global skills directory depends on which location you chose when you first ran `npx skills add`. The default
is `~/.agents/skills/`, but `~/.copilot/skills/` and other paths are valid. We recommend `~/.agents/skills/` for
cross-tool compatibility.

## Skills not loading in a project session

Make sure project-scoped skills live in `.github/skills/` at the root of the repo *and* that you launched the
Copilot CLI from inside that repo's directory. Skills in subdirectories or in differently named folders are ignored.
