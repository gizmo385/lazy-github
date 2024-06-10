from lazy_github.ui import app

# TODO:
# 2: Wrap the menus in a scrollpanel incase they get too big
# 3: Start pulling in Github information (how do we auth?)
# 3.a: Let's do pull requests first since they're straightforward

if __name__ == "__main__":
    app.LazyGithub().run()
