<div align="center">

# devskills

**Two jobs a developer does mid-task, in the conversation they are already having**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://code.claude.com/docs/en/plugins)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20WSL-lightgrey)]()

A free, open-source tool by [DBHQ](https://dbhq.uk)

</div>

---

Development skills for Claude Code and Codex.

## Skills

| Skill | What it does |
|---|---|
| [gitview](skills/gitview) | Surveys every branch and worktree in a repository, says which branches are finished, and offers to clear them away |
| [jira](skills/jira) | Creates and reads Jira Cloud issues over the REST API, after checking the project key, the issue type and the required fields |

## Install

### Any agent (Claude Code, Codex, Cursor, Copilot, Windsurf, Gemini, Cline and more)

```bash
npx skills add dbhq-uk/devskills
```

The [skills.sh](https://skills.sh) CLI installs into whichever agent directories it finds.

### Local install (Claude Code or Codex)

```bash
git clone https://github.com/dbhq-uk/devskills.git
cd devskills
./install.sh          # Claude Code: symlinks into ~/.claude/skills (edits are live)
./install-codex.sh    # Codex: installs into ~/.codex/skills
```

[`install.sh`](install.sh) and [`install-codex.sh`](install-codex.sh) are the same install two ways: Claude Code substitutes `${CLAUDE_SKILL_DIR}`, so the whole skill directory is symlinked untouched, while Codex does not, so its `SKILL.md` is rewritten at install time. Re-run the Codex one after editing a `SKILL.md`.

Both install every skill in the pack, warn rather than fail on a missing dependency and name the skill that needs it, then print the setup command for any skill that needs credentials. Neither runs that setup for you: launching one member's interactive prompt on install of the whole pack is surprising.

### Requirements

- **`gitview`:** Python 3 and `git`. Optionally `gh` or the Azure CLI, for the pull request column
- **`jira`:** `jq`, `curl`, and a Jira Cloud account you can create an API token on

## gitview

One table: worktree, branch, open pull request, ahead, behind, unpushed, and whether the branch is safe to delete.

The last column is the one that is hard. A branch merged by squash stays ahead of the trunk forever while contributing nothing, so commit counts cannot answer it and `git branch --merged` never sees it. gitview merges the trunk into a throwaway copy of each branch and compares the resulting tree against the trunk's. If they match, the branch adds nothing and can go.

Design: [docs/superpowers/specs/2026-09-10-gitview-design.md](docs/superpowers/specs/2026-09-10-gitview-design.md)

## jira

Creates and reads Jira Cloud issues over the REST API v3, authenticated with an API token.

Ask Claude to raise a ticket and it does, after checking the project key, the issue type and the required fields against your Jira, so the create call is right the first time. It creates one issue or a batch, and reads issues back with JQL.

**It creates and reads only.** There is no delete, no bulk transition, and no project administration. Anything destructive stays a human job in the Jira UI.

### Setup

```bash
~/.claude/skills/jira/scripts/jira-setup.sh
```

It asks for three things: your site URL (`https://you.atlassian.net`), the email on your Atlassian account, and an API token from <https://id.atlassian.com/manage-profile/security/api-tokens>. The token input is hidden.

Setup verifies against `/rest/api/3/myself` **before** writing anything, so a wrong token costs you nothing. Credentials are saved to `~/.jira/config.json` at mode 600, outside any repository.

The token never reaches a command line. `curl` reads it from a 0600 config file, so it does not appear in `ps` output or in shell history.

### Use

Talk to Claude: "raise a bug in PAY about the timeout", "what's assigned to me", "create these five tickets". The scripts are also usable directly:

```bash
cd ~/.claude/skills/jira/scripts

./jira-meta.sh projects              # project keys you can see
./jira-meta.sh types PAY             # issue type names in that project
./jira-meta.sh fields PAY Task       # what a create accepts, required marked

./jira-issues.sh create PAY Task "Summary" "Description" --label infra --priority High
./jira-issues.sh bulk PAY tickets.json --dry-run
./jira-issues.sh get PAY-12
./jira-issues.sh search "assignee = currentUser() AND statusCategory != Done"
./jira-issues.sh mine
```

Issue type names are per-project. `Task` in one project may be `Story` or `Work Item` in another, so read `types` rather than assuming.

### Bulk creation

`bulk` takes a JSON array. Only `summary` is required; `type` defaults to `Task`.

```json
[
  {"summary": "Enable the storage provider on the subscription", "type": "Task",
   "description": "Blocks the deployment.\n\nOnly the pipeline identity can do this.",
   "labels": ["infra"], "priority": "High"},
  {"summary": "Add retry handling to the upload step"}
]
```

Blank lines in a description become separate paragraphs. REST v3 needs Atlassian Document Format rather than a plain string, and the script builds it, so you pass plain text.

**Run it with `--dry-run` first.** That prints the exact payload for every issue and sends nothing.

A batch paces itself at five requests a second to stay inside Jira's limit of roughly 60 a minute, and reports `Created:` and `Failed:` counts at the end. A partial failure leaves the successful issues in place, because there is no rollback: the skill cannot delete.

### Files

| Path | What it is |
|---|---|
| `skills/jira/SKILL.md` | What Claude reads |
| `skills/jira/scripts/jira-setup.sh` | Credential capture and verification |
| `skills/jira/scripts/jira-meta.sh` | Projects, issue types, fields, priorities, read-only |
| `skills/jira/scripts/jira-issues.sh` | Create, bulk create, get, search |
| `skills/jira/scripts/_common.sh` | Shared request, error and ADF helpers |

## Licence

MIT. See [LICENSE](LICENSE).
