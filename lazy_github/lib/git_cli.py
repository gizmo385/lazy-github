import subprocess
import re

from dataclasses import dataclass

# Regex designed to match git@github.com:gizmo385/lazy-github.git:
# ".+:"         Match everything to the first colon
# "([^\/]+)"    Match everything until the forward slash, which should be owner
# "\/"          Match the forward slash
# "([^.]+)"     Match everything until the period, which should be the repo name
# ".git"        Match the .git suffix
_GIT_REMOTE_REGEX = re.compile(r".+:([^\/]+)\/([^.]+).git")


@dataclass
class LocalGitRepo:
    owner: str
    name: str


def current_directory_git_repo_remote_owner(remote: str = "origin") -> LocalGitRepo | None:
    """
    Returns the name and owner associated with the remote of the git repo in the current working directory.
    """
    try:
        output = subprocess.check_output(["git", "remote", "get-url", remote]).decode().strip()
    except subprocess.SubprocessError:
        return None

    if matches := re.match(_GIT_REMOTE_REGEX, output):
        owner, name = matches.groups()
        return LocalGitRepo(owner, name)
