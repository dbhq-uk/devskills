# Why "is this branch finished?" is harder than it looks

A branch is finished when merging the trunk into it produces the trunk's tree exactly. Then it contributes nothing, whatever its commit count says.

Two cheaper tests look right and are wrong. Both fail silently, which is what makes them dangerous. They do not error. They quietly report finished work as live, and a branch nobody dares delete sits there for weeks.

## `git branch --merged` misses every squash merge

Where a repository squashes on merge, the branch's commits never become ancestors of the trunk. A branch whose every line landed weeks ago still never appears as merged.

In a repository whose branch policy permits nothing but squash, and many do, this test is not merely unreliable. It is always wrong.

## Reverse-applying the branch's patch gives false negatives

Take the branch's diff against its merge base and try to apply it backwards to the trunk. If it applies cleanly the content must already be there.

The reasoning is sound and the test still fails, because applying a patch depends on context lines. The moment the trunk edits the same files after the branch landed, the surrounding lines no longer match and the patch will not reverse. The content is present. The check says it is missing.

This is not hypothetical. It is what sent one survey badly wrong: two branches were reported as thousands of insertions of live work when both had in fact landed days earlier. The error only surfaced because merging the trunk into one of them turned out to produce no change at all.

`tests/test_landed.py` asserts both failures against the fixture, so the suite proves the naive checks are wrong rather than assuming it.

## The test that works

Merge the trunk into a throwaway copy of the branch, and compare the resulting tree with the trunk's tree. Equal means the branch adds nothing.

gitview does this in two tiers, because the obvious implementation, a real merge per branch, needs a worktree per branch and is slow enough to be annoying.

### Tier one: a trivial merge into a temporary index

`git read-tree -m --aggressive <merge-base> <branch> <trunk>` against a temporary `GIT_INDEX_FILE`, then compare `git write-tree` with the trunk's tree. No checkout, no worktree, milliseconds.

**It is definitive only when it says yes.** If every path resolved to the trunk's version then for every path the branch either never touched it or agrees with it, which is exactly what contributing nothing means.

**A no answer proves nothing.** `read-tree` performs a trivial merge and refuses any file both sides edited, even where a real merge would combine two non-overlapping changes cleanly. Treating its no as an answer would report finished branches as conflicted.

### Tier two: a real merge in a throwaway worktree

Run only for branches tier one could not prove finished. It is the only thing that can tell a genuine conflict apart from genuine unlanded work, and it is where the `conflicts` and `no, N insertions` answers come from.

The worktree is created detached under a temporary directory and removed in a `finally` block, including when the merge raises.

## What the columns cannot tell you

**Ahead is a commit count against the trunk.** A branch merged by squash stays ahead forever. Reading a large ahead number as "unlanded work" is the same mistake in a different form, and the table deliberately puts the safe-to-delete column last so it reads as the conclusion rather than as one number among several.

**Behind says nothing about whether a branch is finished.** A branch can be behind by fifty commits and still contribute nothing.
