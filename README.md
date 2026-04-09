# RokuRemoteECP
A script created to control a roku device over IP using External Control Protocol API calls with vim-like keybinds.

## Controls 
The controls on this script are "vim-like" so they are not 1:1 with an actual vim instance.
Notably, non-character keys like arrow keys and enter do not work because I am a bad programmer.

### List of keybinds
q : poweroff

w : poweron

h : left

j : down

k : up

l : right

space : select

b : back

u : volumedown

i : volumeup

m : volumemute

e : home

t : typetext  (if you want to exit the script press t and ctrl+c)

## Dependencies
pycurl readchar

## Installation 
you are free to install the libraries with your OS package manager or with pip using python virtial environments.

Debian based distros:
`# apt install <xyz>`

Arch based distros:
`# pacman -S python-pycurl python-readchar`

Pip, my beloathed:
`python -m venv /path/to/venvdir`
`/path/to/venvdir/bin/pip install pycurl readchar`
and then run with:
`/path/to/venvdir/bin/python rokuremote.py`



