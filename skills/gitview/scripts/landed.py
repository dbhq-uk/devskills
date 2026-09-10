"""Decides whether a branch still contributes anything to the trunk.

A branch is finished when merging the trunk into it produces the trunk's tree
exactly. Then it adds nothing, whatever its commit count says.

Read references/safe-to-delete.md before changing any of this. Both of the
obvious cheaper tests are wrong, and the wrongness is silent: they do not
error, they quietly report live work forever.
"""
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

import gitrepo


@dataclass
class Verdict:
    state: str  # landed, unlanded, conflicts
    detail: str


def _tree(cwd, ref):
    return gitrepo.git(["rev-parse", f"{ref}^{{tree}}"], cwd, check=False)


def fast_is_landed(cwd, trunk_ref, branch):
    """Tier one: a trivial three-way merge into a temporary index, no checkout.

    Definitive only when it says yes. If every path resolved to the trunk's
    version then the branch either never touched it or agrees with it, which is
    exactly what contributing nothing means.

    A no answer proves nothing, because read-tree refuses any file both sides
    edited, even where a real merge would combine the two edits cleanly. That
    is why a no falls through to the real merge below.
    """
    base = gitrepo.git(["merge-base", trunk_ref, branch], cwd, check=False)
    if not base:
        return False

    handle, index = tempfile.mkstemp(prefix="gitview-index-")
    os.close(handle)
    os.unlink(index)
    env = dict(os.environ, GIT_INDEX_FILE=index)

    def run(args):
        return subprocess.run(
            ["git", "-C", cwd, *args], capture_output=True, text=True, env=env
        )

    try:
        if run(["read-tree", "-m", "--aggressive", base, branch, trunk_ref]).returncode != 0:
            return False
        if run(["ls-files", "-u"]).stdout.strip():
            return False
        written = run(["write-tree"])
        if written.returncode != 0:
            return False
        return written.stdout.strip() == _tree(cwd, trunk_ref)
    finally:
        if os.path.exists(index):
            os.unlink(index)


def _real_merge(cwd, trunk_ref, branch):
    """Tier two: a real merge in a throwaway detached worktree.

    Only reached where tier one could not prove the branch finished. This is
    the only thing that can tell a genuine conflict apart from genuine
    unlanded work.
    """
    tmp = tempfile.mkdtemp(prefix="gitview-merge-")
    path = os.path.join(tmp, "wt")
    try:
        try:
            gitrepo.git(["worktree", "add", "--detach", path, branch], cwd)
        except gitrepo.GitError as exc:
            return Verdict("unlanded", f"could not check out: {exc}")

        gitrepo.git(["merge", "--no-edit", trunk_ref], path, check=False)
        conflicted = gitrepo.git(["diff", "--name-only", "--diff-filter=U"], path, check=False)
        if conflicted:
            names = conflicted.split("\n")
            shown = ", ".join(names[:3]) + (", ..." if len(names) > 3 else "")
            gitrepo.git(["merge", "--abort"], path, check=False)
            return Verdict("conflicts", shown)

        if _tree(path, "HEAD") == _tree(cwd, trunk_ref):
            return Verdict("landed", "adds nothing to trunk")

        stat = gitrepo.git(["diff", trunk_ref, "HEAD", "--shortstat"], path, check=False)
        return Verdict("unlanded", stat.strip() or "differs from trunk")
    finally:
        gitrepo.git(["worktree", "remove", "--force", path], cwd, check=False)
        shutil.rmtree(tmp, ignore_errors=True)
        gitrepo.git(["worktree", "prune"], cwd, check=False)


def verdict(cwd, trunk_ref, branch):
    """Is this branch finished? Fast path first, real merge only where needed."""
    if fast_is_landed(cwd, trunk_ref, branch):
        return Verdict("landed", "adds nothing to trunk")
    return _real_merge(cwd, trunk_ref, branch)
