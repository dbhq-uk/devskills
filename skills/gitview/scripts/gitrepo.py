"""Every git subprocess call gitview makes. Nothing here writes to the repository."""
import os
import subprocess
from dataclasses import dataclass


class GitError(RuntimeError):
    pass


def git(args, cwd, check=True):
    """Run git and return stdout stripped. Raises GitError when check and it fails."""
    result = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    if result.returncode != 0:
        if check:
            raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return ""
    return result.stdout.strip()


def is_repo(cwd):
    return git(["rev-parse", "--is-inside-work-tree"], cwd, check=False) == "true"


def trunk(cwd):
    """The repository's main line, discovered rather than assumed.

    origin/HEAD is the honest answer where it exists. Falling back to main then
    master covers a repository with no remote. None says plainly that nothing
    else in this table would mean anything.
    """
    head = git(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd, check=False)
    if head:
        return head.split("refs/remotes/origin/", 1)[-1]
    for name in ("main", "master"):
        if git(["rev-parse", "--verify", "--quiet", name], cwd, check=False):
            return name
    return None


def trunk_ref(cwd, name):
    """Prefer the remote-tracking trunk, because a local one can be stale."""
    remote = f"origin/{name}"
    if git(["rev-parse", "--verify", "--quiet", remote], cwd, check=False):
        return remote
    return name


def worktrees(cwd):
    """Map branch name to the basename of the directory holding it.

    The basename often disagrees with the branch name, and seeing that is the
    point: a directory called after a branch deleted weeks ago misleads people.
    """
    out = git(["worktree", "list", "--porcelain"], cwd, check=False)
    found, path = {}, None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line.split(" ", 1)[1]
        elif line.startswith("branch ") and path:
            found[line.split("refs/heads/", 1)[-1]] = os.path.basename(path)
    return found


@dataclass
class Branch:
    name: str
    upstream: object  # str or None


def branches(cwd):
    out = git(["for-each-ref", "--format=%(refname:short)%09%(upstream:short)", "refs/heads/"], cwd)
    result = []
    for line in out.splitlines():
        name, _, upstream = line.partition("\t")
        if name:
            result.append(Branch(name=name, upstream=upstream or None))
    return result


def count(cwd, spec):
    out = git(["rev-list", "--count", spec], cwd, check=False)
    return int(out) if out.isdigit() else 0


def remote_url(cwd):
    return git(["remote", "get-url", "origin"], cwd, check=False) or None
