from enum import StrEnum

from pydantic import BaseModel


class User(BaseModel):
    login: str
    id: int
    name: str | None = None
    followers: int | None = None
    following: int | None = None


class RepositoryPermission(BaseModel):
    admin: bool
    maintain: bool
    push: bool
    triage: bool
    pull: bool


class Repository(BaseModel):
    name: str
    full_name: str
    default_branch: str
    private: bool
    archived: bool
    owner: User
    description: str | None = None
    permissions: RepositoryPermission | None = None


class IssueState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class Issue(BaseModel):
    id: int
    number: int
    comments: int
    locked: bool
    state: IssueState
    title: str
    body: str | None = None
    user: User
    closed_by: User | None = None
    assignee: User | None = None
    assignees: list[User] | None


class PullRequest(Issue):
    draft: bool
