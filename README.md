# LazyGithub

This is a **WIP** terminal UI client for interacting with [GitHub](https://github.com). It draws heavy
inspiration from the [lazygit](https://github.com/jesseduffield/lazygit) project and uses
[Textual](https://textual.textualize.io/) to drive the terminal UI interactions.


![Example screenshot](https://raw.githubusercontent.com/gizmo385/lazy-github/main/images/lazy-github-conversation-ui.svg)


Currently, it supports the following:


- Listing the repositories associated with your account 
- Listing the issues and pull requests on those repositories
- Listing the details, diff, and reviews on any of those pull requests
- Detailed issue views, including conversation participation

Planned features:
- Local caching, improving reload times and making it easier to use within a terminal or editor
  environment.
- A more wholeistic summary view for the currently selected repository
- The ability to list, view, and trigger actions on a repository
- More fleshed out PR interactions, including commenting and eventually submitting full PR reviews
  from within your terminal.


## Running Locally

If you have [uv](https://github.com/astral-sh/uv) installed, then you can try LazyGithub by running
`uvx lazy-github`. Alternatively, you can pull the repo and run it locally by running the
`./start.sh` script in the root of the repo.
