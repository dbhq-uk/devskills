import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import gitrepo
from fixture import build


def test_trunk_is_discovered_not_assumed():
    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp)
        assert gitrepo.trunk(repo) == "trunk"


def test_branches_lists_every_local_branch_with_its_upstream():
    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp)
        found = {b.name: b.upstream for b in gitrepo.branches(repo)}
        assert "live-work" in found
        assert found["no-upstream"] is None


def test_worktrees_maps_branch_to_directory_basename():
    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp)
        assert gitrepo.worktrees(repo)["live-work"] == "checkout-alpha"


def test_count_counts_commits_in_a_range():
    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp)
        assert gitrepo.count(repo, "trunk..live-work") >= 1
        assert gitrepo.count(repo, "trunk..trunk") == 0


def test_a_directory_that_is_not_a_repository_is_reported_not_raised():
    with tempfile.TemporaryDirectory() as tmp:
        assert gitrepo.is_repo(tmp) is False
