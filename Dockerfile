FROM registry.fedoraproject.org/fedora:28

# FIXME: get rid of docker binary, use just API
RUN dnf install -y neovim python3-docker python3-pyxattr python3-six git python3-neovim docker origin-clients podman

RUN dnf install -y sudo

# RUN pip3 install git+https://github.com/fedora-modularity/conu.git@master
RUN pip3 install git+https://github.com/TomasTomecek/conu.git@list-dkr-images-fix

COPY . /src
WORKDIR /src

# FIXME: we can't run as unpriv user since some backends need root

# This will fail b/c the process is not attached to PTY, we don't care
# nvim creates manifest file anyway
RUN nvim -u ./vimrc -c ':UpdateRemotePlugins' || :

CMD ["nvim", "-u", "./vimrc", "-c", "call LucidRun()"]
