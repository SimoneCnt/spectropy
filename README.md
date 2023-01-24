
Spectropy
=========

Spectropy is a simple tool to view, compare and match Raman spectra of minerals.

Install
-------

### Install Python & tkinter

Spectropy is a python application using tkinter for the graphical user interface. You need first to install these on your computer first.
The details depend on your operating system; see below. To verify that tkinter is available run this command in the Terminal:

    python3 -m tkinter

You should see a little window opening with the tkinter version. If instead you get any error, it means something went wrong somewhere...

#### MacOS

On MacOS, first you need Homebrew. Please install it as [described on their website](https://brew.sh/)
Usually, you should just open the Terminal App and paste the following:

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Once done, install python with tkinter using this command:

    brew install python-tk

#### Linux

The specifics on how to install python and tkinter depend on your Linux distribution.
You should be able to do that from your package manager (apt, pacman, ...)

#### Windows

No idea, I never tested this. 

### Install Spectropy

At this point you should have python and tkinter installed. Python also comes with an utility called pip. To install Spectropy just run in the Terminal:

    pip3 install --user --upgrade https://github.com/SimoneCnt/spectropy/archive/refs/heads/main.zip

This command should install all needed dependences, and you can run Spectropy form the Terminal via:

    python3 -m spectropy

Again, no error should be printed and the main Spectropy window should open.
This should be work perfectly fine in MacOS and Linux. I haven't tested it on Windows, but it should work also there.

As a final touch on MacOS, if you prefer to use a graphical application, you can 
[download the Spectropy dmg file](https://github.com/SimoneCnt/spectropy/raw/main/make_macos_app/Spectropy.dmg).
Still, this is just a wrapper, and you need a working version of Spectropy to use it.
No wrapper is available for Linux or Windows.

### Update Spectropy to the latest version

To update Spectropy, you can just run again the command:

    pip3 install --user --upgrade https://github.com/SimoneCnt/spectropy/archive/refs/heads/main.zip

And you should get the latest version.


