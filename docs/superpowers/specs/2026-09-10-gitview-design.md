# gitview design

One table answering "where are we at with branches and worktrees", then an offer to clear away what is finished.

## The problem

A repository worked by several sessions at once accumulates branches faster than anyone retires them. Some are finished, some are parked in a worktree, some exist only on one machine. The questions that matter are always the same: what is in flight, what is at risk of being lost, and what can go.

Git answers none of them well on its own. `git branch -vv` shows ahead and behind against the upstream, which is the wrong reference point, and it says nothing about worktrees, pull requests, or whether a branch is finished.

## What it prints

| Worktree | Branch | PR | Ahead | Behind | Unpushed | Safe to delete |
|---|---|---|---|---|---|---|
| `app` | `feature/import` | 118 succeeded | 3 | 0 | 0 | no, 46 insertions |
| `app-fix` | `fix/parser` | – | 18 | 1 | 0 | no, 2,232 insertions |
| `spike` | `spike/cache` | 121 conflicts | 11 | 1 | 1 | no, conflicts |
| – | `main` | – | 0 | 0 | 0 | no, trunk |
| – | `docs/old-notes` | – | 15 | 1 | 0 | **YES** |

One row per local branch. Rows with a worktree sort first, then the rest under a dash. Worktree-less branches are kept deliberately: that is where finished branches hide.

### The columns

- **Worktree** is the basename of the checkout holding the branch, or a dash. The basename often disagrees with the branch name, and seeing that is the point.
- **PR** is the open pull request number and its merge status.
- **Ahead** and **Behind** are commit counts against the trunk, not the upstream.
- **Unpushed** is commits the upstream does not have. `no remote` where there is no upstream at all, which is a finding rather than an error.
- **Safe to delete** is the judgement, described below.

Ahead is a commit count, not a measure of unlanded content. A branch merged by squash stays ahead forever while contributing nothing. The safe-to-delete column is the one to read.

## Safe to delete

A branch is safe to delete when merging the trunk into it produces the trunk's tree exactly. Then the branch contributes nothing, whatever its commit count says.

Both obvious tests are wrong, and this is the reason the skill exists.

**`git branch --merged` misses every squash merge.** Where a repository squashes on merge, the branch's commits never become ancestors of the trunk, so a fully landed branch never appears as merged.

**Reverse-applying the branch's patch gives false negatives.** Take the branch's diff against its merge base and try to apply it backwards to the trunk: if it applies, the content is already there. It fails as soon as the trunk edits the same files afterwards, because the surrounding context no longer matches. The content is present, the check says it is missing, and the branch looks like live work forever.

### The two-tier test

**Tier one, fast, no checkout.** A three-way `git read-tree -m --aggressive` of merge base, branch and trunk into a temporary index. If the resulting tree equals the trunk's tree, the branch adds nothing and that answer is final: every path resolved either because the branch never touched it or because the branch and trunk agree.

This runs in milliseconds for a whole repository and needs no working tree.

**Tier two, only where tier one cannot prove it.** `read-tree` performs a trivial merge, so it reports a conflict wherever a real merge would have combined two non-overlapping edits to one file. Its "not landed" and "conflicts" answers are therefore not trustworthy on their own. Any branch tier one does not prove landed gets a real merge in a throwaway detached worktree, which settles whether the answer is `conflicts` or `unlanded, N insertions`.

Tier one is definitive only in the positive direction. Tier two exists because the negative direction is where the naive tests went wrong.

## Structure

```
skills/gitview/
  SKILL.md
  scripts/gitview.py
  references/safe-to-delete.md
```

`gitview.py` is one file, because it is one pass over one repository and splitting it would add indirection without adding a seam worth testing.

`references/safe-to-delete.md` records why the naive tests fail, so the check is not "simplified" back into a broken one later.

## Data flow

1. Find the trunk: `origin/HEAD`, else `main`, else `master`. Report which was used.
2. Read worktrees from `git worktree list --porcelain` and map branch to checkout basename.
3. Read local branches and their upstreams from `git for-each-ref`.
4. Count ahead, behind and unpushed per branch with `git rev-list --count`.
5. Run the two-tier landed test per branch.
6. Look up open pull requests once, and match them to branches by source ref.
7. Print the table.

## Pull request lookup

The forge comes from the `origin` URL. A host containing `dev.azure.com` or `visualstudio.com` means Azure DevOps and `az repos pr list`. A host containing `github.com` means GitHub and `gh pr list`. Anything else means no lookup.

One call lists every open pull request, and branches are matched against it in memory. Never one call per branch.

The column degrades rather than fails. A missing CLI, a failed login, or no network prints dashes and one line saying the lookup was skipped and why. A status table that refuses to render because a remote API was unreachable is useless exactly when it is most wanted.

## Actions

The table prints first, always. The actions are a second step and never automatic.

**Delete the safe-to-delete branches.** Offered only when there are any. Before each delete the branch is re-verified from scratch, because a table is a snapshot and a repository worked by several sessions moves underneath it. The commit SHA is printed before the branch goes, so it can be restored. A branch is refused if it has a worktree, has an open pull request, or fails re-verification, and the reason is said out loud.

Local and remote deletion are offered as one step, because a local-only delete leaves the remote branch to be rediscovered later.

**Push the unpushed.** Offered when any branch has unpushed commits or no upstream at all. No upstream is the more urgent of the two: that work exists on one machine.

Nothing else is offered. It does not merge, complete pull requests, rebase or resolve conflicts.

## Failure modes

| Situation | Behaviour |
|---|---|
| Not a git repository | Say so, exit non-zero |
| No trunk found | Say so, exit non-zero. Nothing else is meaningful without one |
| Detached HEAD in a worktree | Row shows the SHA, no branch |
| Branch with no upstream | Unpushed reads `no remote` |
| Forge CLI missing or not logged in | PR column dashes, one explanatory line |
| Bare repository | Run normally, no worktree column entries |

## Testing

A fixture repository built by script, so the landed test is proven against the cases that break the naive checks rather than against a happy path:

1. A branch squash-merged into the trunk, where the trunk then edits the same files. Must read as safe to delete. This is the case reverse-applying the patch gets wrong.
2. A branch with genuine unlanded work. Must not read as safe to delete.
3. A branch conflicting with the trunk. Must read as conflicts, not as safe to delete.
4. A branch with no upstream. Must read as `no remote`.
5. A worktree whose directory name differs from its branch name. Must show both correctly.
6. A detached worktree. Must not crash.

The pull request lookup is tested against recorded output rather than a live forge.

## Out of scope

Remote branches with no local counterpart, stash contents, submodules, and any repository other than the current one. Each is a real question and none is this table.
