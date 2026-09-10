#!/usr/bin/env python3
"""Survey every branch and worktree in a repository.

Read only. It never deletes, pushes, merges or checks an existing branch out.
The actions live in SKILL.md so that nothing destructive sits in a script that
could be run unattended.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import forge  # noqa: E402
import gitrepo  # noqa: E402
import landed  # noqa: E402
import table  # noqa: E402


def survey(cwd, want_prs=True):
    """Return (rows, notes). Notes are things the reader needs to know."""
    notes = []
    trunk_name = gitrepo.trunk(cwd)
    if trunk_name is None:
        raise gitrepo.GitError("no trunk found: looked for origin/HEAD, then main, then master")
    trunk_ref = gitrepo.trunk_ref(cwd, trunk_name)
    notes.append(f"Trunk is `{trunk_ref}`.")

    prs = {}
    if want_prs:
        prs, reason = forge.list_prs(forge.detect(gitrepo.remote_url(cwd)), cwd)
        if reason:
            notes.append(f"Pull request column skipped: {reason}.")

    checkouts = gitrepo.worktrees(cwd)
    rows = []
    for branch in gitrepo.branches(cwd):
        name = branch.name
        if branch.upstream:
            unpushed = str(gitrepo.count(cwd, f"{branch.upstream}..{name}"))
        else:
            unpushed = "no remote"

        if name == trunk_name:
            safe = "no, trunk"
        else:
            result = landed.verdict(cwd, trunk_ref, name)
            safe = "YES" if result.state == "landed" else f"no, {result.detail}"

        rows.append(
            table.Row(
                worktree=checkouts.get(name, "-"),
                branch=name,
                pr=prs.get(name, "-"),
                ahead=gitrepo.count(cwd, f"{trunk_ref}..{name}"),
                behind=gitrepo.count(cwd, f"{name}..{trunk_ref}"),
                unpushed=unpushed,
                safe=safe,
            )
        )
    return rows, notes


def _verify(cwd, branch):
    """Exit 0 only when the branch is finished. Used before deleting one."""
    trunk_name = gitrepo.trunk(cwd)
    if trunk_name is None:
        print("no trunk found", file=sys.stderr)
        return 2
    if branch == trunk_name:
        print(f"{branch} is the trunk, refusing")
        return 1
    if not gitrepo.git(["rev-parse", "--verify", "--quiet", branch], cwd, check=False):
        print(f"no such branch: {branch}", file=sys.stderr)
        return 2
    result = landed.verdict(cwd, gitrepo.trunk_ref(cwd, trunk_name), branch)
    print(f"{branch}: {result.state} ({result.detail})")
    return 0 if result.state == "landed" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Survey branches and worktrees.")
    parser.add_argument("path", nargs="?", default=".", help="repository path")
    parser.add_argument(
        "--verify",
        metavar="BRANCH",
        help="exit 0 only if BRANCH is finished. Run this before deleting it",
    )
    parser.add_argument("--no-pr", action="store_true", help="skip the pull request lookup")
    args = parser.parse_args(argv)

    cwd = os.path.abspath(args.path)
    if not gitrepo.is_repo(cwd):
        print(f"{cwd} is not a git repository", file=sys.stderr)
        return 2

    try:
        if args.verify:
            return _verify(cwd, args.verify)
        rows, notes = survey(cwd, want_prs=not args.no_pr)
    except gitrepo.GitError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(table.render(rows))
    if notes:
        print()
        for note in notes:
            print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
