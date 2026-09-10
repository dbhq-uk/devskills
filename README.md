# devskills

Development skills for Claude Code and Codex.

## Skills

| Skill | What it does |
|---|---|
| [gitview](skills/gitview) | Surveys every branch and worktree in a repository, says which branches are finished, and offers to clear them away |

## gitview

One table: worktree, branch, open pull request, ahead, behind, unpushed, and whether the branch is safe to delete.

The last column is the one that is hard. A branch merged by squash stays ahead of the trunk forever while contributing nothing, so commit counts cannot answer it and `git branch --merged` never sees it. gitview merges the trunk into a throwaway copy of each branch and compares the resulting tree against the trunk's. If they match, the branch adds nothing and can go.

Design: [docs/superpowers/specs/2026-09-10-gitview-design.md](docs/superpowers/specs/2026-09-10-gitview-design.md)

## Licence

MIT. See [LICENSE](LICENSE).
