from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.constants import DIFF_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.issues import list_all_issues
from lazy_github.models.github import (
    FullPullRequest,
    Issue,
    PartialPullRequest,
    Repository,
    Review,
    ReviewComment,
)


async def list_for_repo(client: GithubClient, repo: Repository) -> list[PartialPullRequest]:
    """Lists the pull requests associated with the specified repo"""
    issues = await list_all_issues(client, repo)
    return [i for i in issues if isinstance(i, PartialPullRequest)]


async def get_full_pull_request(client: GithubClient, partial_pr: PartialPullRequest) -> FullPullRequest:
    """Converts a partial pull request into a full pull request"""
    user = await client.user()
    url = f"/repos/{user.login}/{partial_pr.repo.name}/pulls/{partial_pr.number}"
    response = await client.get(url, headers=client.headers_with_auth_accept())
    response.raise_for_status()
    return FullPullRequest(**response.json(), repo=partial_pr.repo)


async def get_diff(client: GithubClient, pr: FullPullRequest) -> str:
    """Fetches the raw diff for an individual pull request"""
    headers = client.headers_with_auth_accept(DIFF_CONTENT_ACCEPT_TYPE)
    response = await client.get(pr.diff_url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    return response.text


async def get_review_comments(client: GithubClient, pr: FullPullRequest, review: Review) -> list[ReviewComment]:
    user = await client.user()
    url = f"/repos/{user.login}/{pr.repo.name}/pulls/{pr.number}/reviews/{review.id}/comments"
    response = await client.get(url, headers=client.headers_with_auth_accept())
    response.raise_for_status()
    return [ReviewComment(**c) for c in response.json()]


async def get_reviews(client: GithubClient, pr: FullPullRequest, with_comments: bool = True) -> list[Review]:
    user = await client.user()
    url = url = f"/repos/{user.login}/{pr.repo.name}/pulls/{pr.number}/reviews"
    response = await client.get(url, headers=client.headers_with_auth_accept())
    response.raise_for_status()
    reviews: list[Review] = []
    for raw_review in response.json():
        review = Review(**raw_review)
        if with_comments:
            review.comments = await get_review_comments(client, pr, review)
        reviews.append(review)
    return reviews


async def reply_to_review_comment(
    client: GithubClient, repo: Repository, issue: Issue, comment: ReviewComment, comment_body: str
) -> ReviewComment:
    url = f"/repos/{repo.owner.login}/{repo.name}/pulls/{issue.number}/comments/{comment.id}/replies"
    response = await client.post(url, headers=client.headers_with_auth_accept(), json={"body": comment_body})
    response.raise_for_status()
    return ReviewComment(**response.json())


class ReviewCommentNode:
    def __init__(self, comment: ReviewComment) -> None:
        self.children: list["ReviewCommentNode"] = []
        self.comment = comment


def reconstruct_review_conversation_hierarchy(reviews: list[Review]) -> dict[int, ReviewCommentNode]:
    """
    Given a list of PR reviews, this rebuilds a the comment hierarchy as a tree of connected comment nodes. The return
    value of this function is a mapping between the comment IDs and the associated ReviewCommentNode for the top level
    comments ONLY. Any subsequent comments will be included as children in one of the review comment nodes.

    An important disclaimer is that this function does NOT take into account the body associated with the review itself,
    which is present in some reviews. When generating UI from this function, the body of review itself should be
    included prior to printing the review comments themselves.

    Given a variable `hierarchy` generated from a list `reviews` of PR reviews, the output of this can be properly
    unpacked like so:
    ```python
    for review in reviews:
        if review.body:
            # Output the root review body
            print(review.body)

            # Output the review comments that are top level (i.e. their ids are in the hierarchy map)
            for comment in review.comments:
                if comment.id in hierarchy:
                    # Call
                    comment_review_node_handler(hierarchy[comment.id])
    ```
    """
    comment_nodes_by_review_id: dict[int, ReviewCommentNode] = {}
    # Create review nodes for all of the comments in each of the reviews
    for review in reviews:
        for comment in review.comments:
            comment_nodes_by_review_id[comment.id] = ReviewCommentNode(comment)

    # Build a tree that represents the conversational flow between individual comments in the threads
    for review_node in comment_nodes_by_review_id.values():
        in_reply_to_id = review_node.comment.in_reply_to_id
        if in_reply_to_id is not None and in_reply_to_id in comment_nodes_by_review_id:
            comment_nodes_by_review_id[in_reply_to_id].children.append(review_node)

    return {r.comment.id: r for r in comment_nodes_by_review_id.values() if r.comment.in_reply_to_id is None}
