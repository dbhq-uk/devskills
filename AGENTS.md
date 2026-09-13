# AGENTS.md

Guidance for AI agents (and people) working in this repository.

## What this is

**devskills** - a pack of development skills for AI coding agents. It follows the
[Agent Skills](https://agentskills.io) layout (`skills/<name>/SKILL.md`) and
ships as a [Claude Code plugin](https://code.claude.com/docs/en/plugins).

Two skills, and they have nothing in common beyond being things a developer
needs mid-task:

- **gitview** surveys every branch and worktree in a repository and says which
  branches are finished
- **jira** creates and reads Jira Cloud issues

## Layout

```
.claude-plugin/plugin.json        # plugin manifest for the whole pack
skills/gitview/SKILL.md           # the skill (agent-facing instructions)
skills/gitview/references/        # safe-to-delete: why the cheap checks are wrong
skills/gitview/scripts/           # Python, standard library only, shells out to git
skills/gitview/tests/             # pytest, with a fixture that builds real repositories
skills/jira/SKILL.md              # the skill
skills/jira/references/           # Simplified Technical English, for issue text
skills/jira/scripts/              # bash, curl and jq
install.sh / install-codex.sh     # local symlink installers (Claude / Codex)
docs/superpowers/                 # the dated design and plan records for gitview
```

## The constraints that must not be broken

Everything else here is a preference. These are not.

**1. `gitview.py` is read only.** It never deletes, pushes, merges or checks out
an existing branch. Its docstring says so and that is a promise to the reader,
not a description of the current state. The test merge happens in a temporary
index and a detached temporary worktree, both outside the repository, both
cleaned up. If you need a write operation, it belongs in the agent's hands in
the user's session, not in the script.

**2. A destructive suggestion must be gated, and the gate is re-verified.** The
skill's most useful output is also its most dangerous: a list of branches
somebody is about to delete. So `SKILL.md` requires the table first, then the
offer, then a fresh `gitview.py --verify BRANCH` on each branch immediately
before it goes, the commit SHA printed so a wrong call is recoverable, and a
flat refusal for any branch with a worktree or an open pull request. A table is
a snapshot and a repository worked by several sessions moves underneath it.
Do not weaken this into "the table already said it was safe".

**3. Safe to delete is computed, never inferred.** Read
[`skills/gitview/references/safe-to-delete.md`](skills/gitview/references/safe-to-delete.md)
before touching that logic. A branch merged by squash stays ahead of the trunk
forever while contributing nothing, so a commit count cannot answer the question
and `git branch --merged` never sees it. Both cheap checks fail silently, which
is the worst failure mode available: the answer looks right. Never tell somebody
a branch has unlanded work because its ahead number is large.

**4. jira creates and reads. It does not delete.** No delete, no bulk
transition, no project administration. `bulk` keeps `--dry-run`. A partial
failure leaves the successful issues in place, and that is stated rather than
hidden, because the skill has no way to roll back.

**5. No packages, no venv, no credential in the repo.** gitview is Python
standard library plus `git`; jira is bash plus `curl` and `jq`. jira's token
lives in `~/.jira/config.json` at mode 600 and never reaches a command line, so
it stays out of `ps` and out of shell history. Keep it that way.

## Conventions

- Any path a `SKILL.md` names goes through `${CLAUDE_SKILL_DIR}`, which Claude
  Code substitutes for personal, project and plugin installs alike. **Never
  hardcode `~/.claude/skills/<name>` or any absolute path** - it is wrong under
  a Codex install and wrong under a plugin install. `install-codex.sh` rewrites
  the variable at install time because Codex does not substitute it.
- `SKILL.md` is the short half on purpose. The workflow, the constraints and the
  checks live there; the reasoning and the reference material live in
  `references/` and are read on demand.
- Shell scripts use `set -e`; errors go to stderr, output to stdout.
- Every example is generic: `owner/repo`, `PAY-12`, `mycompany.atlassian.net`.
  CI greps for anything that looks like a real ticket id, hostname, IP address
  or organisation, and the ticket pattern it matches is `[A-Z]{3,}-[0-9]{3,}`.
- House style: British English, plain hyphens, **no em dashes** - CI fails on
  them. No trailing full stops on headings.

## Validating a change

```bash
bash -n install.sh install-codex.sh
jq empty .claude-plugin/plugin.json
python3 -m pytest skills/gitview/tests -q
```

CI runs those plus the two prose checks. The gitview tests are worth more than
they look: the fixture builds real git repositories, including the
squash-merged-then-trunk-moved case that defeats both naive checks, so a change
that breaks the finished-branch logic fails rather than quietly returning the
wrong verdict.
