# LazyGithub

This is a **WIP** terminal UI client for interacting with [GitHub](https://github.com). It draws heavy
inspiration from the [lazygit](https://github.com/jesseduffield/lazygit) project and uses
[Textual](https://textual.textualize.io/) to drive the terminal UI interactions. Currently, it
supports the following:

- Listing the repositories associated with your account 
- Listing the issues and pull requests on those repositories
- Listing the details, diff, and reviews on any of those pull requests

Planned features:
- Local caching, improving reload times and making it easier to use within a terminal or editor
  environment.
- A more wholeistic summary view for the currently selected repository
- The ability to list, view, and trigger actions on a repository
- More fleshed out PR interactions, including commenting and eventually submitting full PR reviews
  from within your terminal.
- Detailed issue views, including conversation participation


## Running Locally

I'm not currently automatically pushing LazyGithub up to [PyPi](https://pypi.org/) (although I plan
to in the future), so for the time being you can run this locally via the `./start.sh` script.
