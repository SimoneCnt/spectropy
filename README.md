
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

This command should install all needed dependences, and you can run Spectropy from the Terminal via:

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


First Use
---------

Upon opening Spectropy for the first time, you probably want to load a Raman spectra you measured or received. For this, just click on the "Open New Spectrum" button and navigate to the file you want to open. Spectropy currently support Raman spectra in a few formats: spc, LRD 1.1, the format used by [the RRUFF project](https://rruff.info/) and a plain txt format. Spectropy tries to automatically detect the format, but it may fail. If that happens, or if your spectra is in a not supported format, please sent it to me, and I'll see what I can do.

Once loaded you can change a few settings: 
 - Label will change the text in the legend
 - Color will change the color!
 - Min and Max will limit the range of raman shifts in the plot
 - Shift will shift vertically the whole graph
 - Filter will increase/reduce the number of peaks detected
 - Baseline will compute and eventually remove a baseline correction; try to play with the L and P parameters to see what it "looks best"
 - Calibrate m,q are two parametes to shift horizontally and scale the graph; this is useful in case your Raman spectrometer is not calibrated and a simple linear regression may fix the issue (m is the slope, q the intercept of such linear regression). Click apply to see its effect.
 - Match will match the spectra with a database of reference spectra (see below)
 - Save will save a text file with the new spectra, useful when removing the baseline and calibrating it.
 - Remove will just delete it.
 
 You can load multiple spectra at the same time, for comparisons. If you are loading a lot of spectra you can save the current setup with the "Save config" button. The "Load config" will reopen it as it was left. The "Update graph" should be useless, as the graph should be updated every time your change any parameter. The buttons "RefLib Setup" and "RefLib View" allow you to load and view the reference library, see description below.


Reference Library
-----------------

Raman spectroscopy is close to useless without a reliable database of reference spectra. The [RRUFF project](https://rruff.info/) provides, free for everyone such reference database for minerals.

With the "RefLib Setup" button you can download and setup a copy of the RRUFF database for use in Spectropy. First, you need to download it, so click on the "Get new version" button. It will take a while, and, once done, if should show the text "Last downloded:" with the current date. The RRUFF project regularly update their database, so you may want to download a new fresh copy from time to time (no idea how often, maybe every few months?).

With a copy of the RRUFF database you can now create a matching library to be used to match your spectra with. You can select how many different spectra of the same mineral you want (a couple should be enough, increase if you want), and the preferred waivelength of the laser to use. Raman spectra can differ with the laser used, so using as reference spectra obtained with the same laser should help. If no spectra with your preferred laser are found, the closest ones are used instead. The click the "Generate new matching library" button. It will take again a little while, and, after that, it should show a text saying: "Library available with max_spectra=x and preferred_laser=xxx".

With this you are ready to go! Close to window and click the "RefLib View" button. This will open a new window where you can select a mineral, then a laser waivelength, and then a RRUFF ID. By clicking the RRUFF ID, that spectra will be loaded in the main window. The number in square brackets is the "quality" of the spectra as listed by RRUFF: 3 is high quality, 0 is low quality. This library view will show all spectra available, not only the ones selected in the generation of the matching library.


Matching a spectra
------------------

Once you have loaded a reference matching library you can click on the "Match" button of your spectra and this will run 3 different matching algorithms. The best matching spectra will be listed in a new window, and you can open any of them by just clicking on them. 

This overall interface need to be improved... todo!
