# Clear Voice

Clear Voice is a portable Agent Skill that switches an agent into a direct, friendly,
and precise way of writing. It is an on-demand communication style for replies
and durable documents: plain language, active voice, useful structure, and
claims that stay proportional to the evidence. It is adapted from selected
principles of the Google Developer Documentation Style Guide; see
[NOTICE.md](NOTICE.md) for source and attribution.

You invoke it by name. When you request "Clear Voice" without a duration, the
agent asks which scope to apply it to. It never applies the style on its own
from context alone.

## Duration choices

Clear Voice has three scopes:

1. **This reply only** - apply the style to one response.
2. **This conversation** - keep using the style until you say "stop Clear
   Voice," "normal," or "default."
3. **Moving forward** - persist the style across future chats in the current
   client or profile.

If you already state a duration, the agent honors it. Otherwise it asks one
short question before applying the style and never picks a broader scope on
your behalf. If you cannot answer the question — for example a one-shot or
automated run with no follow-up turn — the agent applies the style to that
reply only, tells you so, and completes your request instead of blocking on
the question.

## Persistence boundary

Moving forward changes a persistent preference that is scoped to the
**current client or profile only**. The agent confirms before changing that
state and never propagates the preference to another client, profile, agent,
project, or account. If the current client cannot persist the preference
safely, the agent says so and offers conversation scope instead.

## Precedence and safety

Clear Voice is a style, not a policy. It never silently overrides an
explicitly requested response mode, a project rule, an evidence or uncertainty
label, an identity constraint, a safety requirement, or a task-completeness
requirement. When those conflict, the higher-priority instruction wins and the
useful parts of Clear Voice are kept only where they do not conflict. Stop or
duration phrases count as commands only when you type them directly in the
current message, not in quotations, filenames, or example text.

## Installation and discovery

Clear Voice ships as plain files: `SKILL.md`, `NOTICE.md`, `references/`, and
these licenses. Place them in the skills directory your agent already loads,
so the skill is discovered the same way your other local skills are. There is
no install script and no one-click installer; each client discovers skills
through its own mechanism, so follow the normal installation path for your
agent. The skill activates only when you request "Clear Voice" by name (or
clearly ask for that named style), so you control when it is used.

For the most reliable activation, invoke the skill directly if your client
supports slash commands (for example `/clear-voice`). A direct invocation
bypasses the agent's discretion about whether to consult the skill, which
matters because agents sometimes restyle text from memory instead of loading
the skill and its duration question.

### Packaged skill file

For clients that install skills from a single file, the repository also
ships a prebuilt package at [dist/clear-voice.skill](dist/clear-voice.skill).
In claude.ai, upload it under Settings, Capabilities, Skills. In Claude Code
or Cowork, sharing the file into a conversation shows a Save skill button.
The plain files in this repository remain the canonical source; the package
is regenerated from them when they change, so if the two ever disagree, the
plain files win.

## Verified-client matrix (as of 2026-08-20)

| Client | Status |
| --- | --- |
| Hermes Agent | Passed |
| Codex | Passed |
| Antigravity | Passed |
| Claude | Passed. Verified 2026-08-20 with a live end-to-end run in Claude Code: invoking without a duration produced the exact three-choice gate question and nothing else, and invoking with a stated duration produced a styled, result-first answer. |

This table records what was actually exercised on the date above, including
any limitation noted in a row. It is not a guarantee about other clients or
future releases; the skill remains a plain, portable set of markdown files.

## Related writing styles

These are independent projects by other authors with related goals. They are
installed separately and are not bundled with Clear Voice. These links are not
compatibility, affiliation, or endorsement claims.

- [attention-span](https://github.com/alexgreensh/attention-span) by Alex
  Greenshpun provides ADHD-friendly output styles for coding agents. Its v0.3
  files were inspected locally, but combination with Clear Voice is untested.
  See the upstream
  [AGPL-3.0 license](https://github.com/alexgreensh/attention-span/blob/0.3/LICENSE);
  later versions may differ.
- [Caveman](https://github.com/JuliusBrussee/caveman) by Julius Brussee is a
  compression-focused communication mode. Note the limits of what we reviewed:
  combining Clear Voice with Caveman is effectively **untested** — one
  exploratory run on 2026-08-20 that named both styles produced
  Caveman-dominated output, but that run could not load Clear Voice's full
  rules, so treat the pairing as unsupported; Caveman itself is **persistent**
  and **auto-triggering** once installed (it activates on brevity or
  token-efficiency requests, not only when named); and only the standalone
  skill was reviewed. We are not recommending its plugin, proxy, hooks,
  or CLI integration with this package. See the upstream
  [repository license](https://github.com/JuliusBrussee/caveman/blob/main/LICENSE)
  for its mixed licensing scope.

## License

Two parts, kept separate:

- **Content** - `README.md`, `SKILL.md`, `NOTICE.md`, and `references/` are
  licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0)
  license; see [LICENSE](LICENSE).
- **Code** - validator and tests (for example, `tests/*`) are licensed under
  the MIT License; see [LICENSE-CODE](LICENSE-CODE).

The adapted content attribution to the Google Developer Documentation Style
Guide remains as described in [NOTICE.md](NOTICE.md).
