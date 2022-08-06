#!/usr/bin/env python3

import os
import math
import random
import hashlib
import json

missing = ""

try:
    import yaml
except ImportError as e:
    missing += " pyyaml"

try:
    import numpy as np
except ImportError as e:
    missing += " numpy"

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    matplotlib.rcParams['savefig.dpi']=600
except ImportError as e:
    missing += " matplotlib"

try:
    import tkinter as tk
except ImportError as e:
    print()
    print("ERROR!")
    print("It looks like you don't have tkinter available.")
    print("Please, install it by running this command in the Terminal:")
    print("brew install python-tk")
    quit()

if missing:
    print()
    print("ERROR!")
    print("It looks like you don't have%s installed." % (missing))
    print("Please, install them by running this command in the Terminal:")
    print("pip3 install %s" % (missing))
    quit()


import spectropy as spp


class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        def config_interior(event):
            size = (scrollable_frame.winfo_reqwidth(), scrollable_frame.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            canvas.config(width=scrollable_frame.winfo_reqwidth())
        scrollable_frame.bind("<Configure>", config_interior)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.interior = scrollable_frame

def toFloat(val, default=0.0, amin=None, amax=None):
    try:
        flt = float(val)
    except ValueError:
        flt = default
    if amin and flt<amin: flt=amin
    if amax and flt>amax: flt=amax
    return flt

class Spectropy(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Spectropy %s" % (spp.version))
        container = tk.Frame(self)
        container.pack(side=tk.LEFT, fill="both", expand=True)
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=0)
        container.grid_columnconfigure(1, weight=1)
        top_bar = tk.Frame(container)
        top_bar.grid(row=0, column=0, columnspan=2)
        self.spectra = dict()
        self.graph = GraphFrame(container, self)
        self.scrollframe = ScrollableFrame(container)
        self.left = LeftPanel(self.scrollframe.interior, self)
        self.graph.grid(row=1, column=1, sticky="nsew")
        self.scrollframe.grid(row=1, column=0, sticky="nsew")
        self.left.pack()
        tk.Button(top_bar, text='Open new spectrum', command=self.left.LoadNewGraph).grid(row=0, column=0)
        tk.Button(top_bar, text='Update graph', command=self.update).grid(row=0, column=1)
        tk.Button(top_bar, text='Save config', command=self.save).grid(row=0, column=2)
        tk.Button(top_bar, text='Load config', command=self.load).grid(row=0, column=3)
        self.order_status = None

    def AddSpectrum(self, fname, label=None, color='black', xmin=200.0, xmax=3000.0, vshift=0.0, pfilter=5, alsl=3, alsp=3, alsm=0):
        sp = Spectrum(self.left, self, fname, label, color, xmin, xmax, vshift, pfilter, alsl, alsp, alsm)
        if sp.isvalid:
            self.spectra[sp.id] = sp
            self.update()

    def save(self):
        fname = tk.filedialog.asksaveasfilename(defaultextension='.yaml', filetypes=[("YAML", '*.yaml'), ("JSON", '*.json')])
        if not fname: return
        basepath = os.path.dirname(fname)
        save = dict()
        for idd, sp in self.spectra.items():
            save[idd] = sp.toJson()
            save[idd]['fname'] = os.path.relpath(save[idd]['fname'], basepath)
        with open(fname, 'w') as fp:
            if fname.endswith('.json'):
                json.dump(save, fp, indent=4)
            else:
                yaml.dump(save, fp)

    def load(self):
        fname = tk.filedialog.askopenfilename(defaultextension='.yaml', filetypes=[("YAML", '*.yaml'), ("JSON", '*.json')])
        if not fname: return
        with open(fname, 'r') as fp:
            if fname.endswith('.json'):
                save = json.load(fp)
            else:
                save = yaml.safe_load(fp)
        basepath = os.path.dirname(fname)
        for idd, sp in save.items():
            sp['fname'] = os.path.join(basepath, sp['fname'])
            self.AddSpectrum(**sp)

    def update(self, event=None):
        order_status = '-'.join([ '%s_%s' % (k, v.vshift_var.get()) for k,v in self.spectra.items() if v.isvalid ])
        if order_status!=self.order_status:
            self.left.update()
            self.order_status = order_status
        self.graph.update()


class LeftPanel(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
    def LoadNewGraph(self):
        fname = tk.filedialog.askopenfilename(title='Open a file')
        if not fname: return
        self.controller.AddSpectrum(fname)
    def update(self):
        for sp in self.grid_slaves():
            sp.grid_forget()
        self.controller.spectra = { key:sp for key, sp in self.controller.spectra.items() if sp.isvalid }
        for i, sp in enumerate(sorted(self.controller.spectra.values(), reverse=True, key=lambda tmp:toFloat(tmp.vshift_var.get(), 0))):
            sp.grid(row=i, column=0, columnspan=2)

class Spectrum(tk.LabelFrame):

    def __init__(self, parent, controller, fname, label=None, color='black', xmin=200.0, xmax=3000.0, vshift=0.0, pfilter=5, alsl=3, alsp=3, alsm=0):
        tk.LabelFrame.__init__(self, parent, text='')
        self.parent = parent
        self.controller = controller
        tmp = "%s%f" % (fname, random.random())
        self.id = hashlib.md5(tmp.encode('utf-8')).hexdigest()
        self.fname = fname
        self.isvalid = False
        if not os.path.isfile(fname):
            tk.messagebox.showerror('File not found!', 'Sorry, but I could not find this file :(')
            return
        self.x, self.y, self.peaks = spp.read_raman(fname)
        if not np.all(self.x):
            tk.messagebox.showerror('Error parsing file!', 'Sorry, but I could not understand this file :(')
            return
        tk.Label(self, text='Label').grid(row=0, column=0)
        tk.Label(self, text='Color').grid(row=0, column=2)
        tk.Label(self, text='Min').grid(row=1, column=0)
        tk.Label(self, text='Max').grid(row=1, column=2)
        tk.Label(self, text='Shift').grid(row=2, column=0)
        tk.Label(self, text='Filter').grid(row=2, column=2)
        tk.Label(self, text='Baseline L').grid(row=3, column=0)
        tk.Label(self, text='Baseline P').grid(row=3, column=2)
        tk.Label(self, text='Baseline').grid(row=4, column=0)
        self.label_var = tk.StringVar(value=label if label is not None else os.path.basename(fname))
        self.color_var = tk.StringVar(value=color)
        self.xmin_var = tk.StringVar(value=xmin)
        self.xmax_var = tk.StringVar(value=xmax)
        self.vshift_var = tk.StringVar(value=vshift)
        self.pfilter_var = tk.StringVar(value=pfilter)
        self.alsl_var = tk.StringVar(value=alsl)
        self.alsp_var = tk.StringVar(value=alsp)
        self.alsm_var = tk.IntVar(value=alsm)
        ee = list()
        ee.append(tk.Entry(self, textvariable=self.label_var, width=11))
        ee.append(tk.Entry(self, textvariable=self.color_var, width=11))
        ee.append(tk.Entry(self, textvariable=self.xmin_var, width=11))
        ee.append(tk.Entry(self, textvariable=self.xmax_var, width=11))
        ee.append(tk.Entry(self, textvariable=self.vshift_var, width=11))
        ee.append(tk.Entry(self, textvariable=self.pfilter_var, width=11))
        ee.append(tk.Entry(self, textvariable=self.alsl_var, width=11))
        ee.append(tk.Entry(self, textvariable=self.alsp_var, width=11))
        for i,e in enumerate(ee):
            r = i//2
            c = (i%2)*2+1
            e.grid(row=r, column=c)
            e.bind("<Tab>", controller.update)
            e.bind("<Return>", controller.update)
        tk.Radiobutton(self, text='Not compute', variable=self.alsm_var, value=0, command=controller.update).grid(row=4, column=1)
        tk.Radiobutton(self, text='Compute', variable=self.alsm_var, value=1, command=controller.update).grid(row=4, column=2)
        tk.Radiobutton(self, text='Remove', variable=self.alsm_var, value=2, command=controller.update).grid(row=4, column=3)
        tk.Label(self, text='Calibrate m,q').grid(row=5, column=0)
        self.rescale_slope_var = tk.StringVar(value=1.0093)
        rescale_slope_entry = tk.Entry(self, textvariable=self.rescale_slope_var, width=5)
        rescale_slope_entry.grid(row=5, column=1)
        rescale_slope_entry.bind("<Tab>", controller.update)
        rescale_slope_entry.bind("<Return>", controller.update)
        self.rescale_intercept_var = tk.StringVar(value=0.1226)
        rescale_intercept_entry = tk.Entry(self, textvariable=self.rescale_intercept_var, width=5)
        rescale_intercept_entry.grid(row=5, column=2)
        rescale_intercept_entry.bind("<Tab>", controller.update)
        rescale_intercept_entry.bind("<Return>", controller.update)
        self.rescale_apply_var = tk.IntVar(value=0)
        tk.Checkbutton(self, text='Apply', variable=self.rescale_apply_var, command=controller.update).grid(row=5, column=3)
        tk.Button(self, text='Save', command=self.save_raman).grid(row=6, column=2)
        tk.Button(self, text='Remove', command=self.remove).grid(row=6, column=3)
        self.isvalid = True

    def plot(self, ax):
        label = self.label_var.get()
        color = self.color_var.get()
        xmin = toFloat(self.xmin_var.get(), 200.0)
        self.xmin_var.set(xmin)
        xmax = toFloat(self.xmax_var.get(), 3000.0)
        self.xmax_var.set(xmax)
        vshift = toFloat(self.vshift_var.get(), 0)
        self.vshift_var.set(vshift)
        pfilter = toFloat(self.pfilter_var.get(), 0.0, 0.0, 100.0)
        self.pfilter_var.set(pfilter)
        alsp = toFloat(self.alsp_var.get(), 3, 1, 5)
        self.alsp_var.set(alsp)
        alsl = toFloat(self.alsl_var.get(), 3, 1, 10)
        self.alsl_var.set(alsl)
        alsm = self.alsm_var.get()
        if alsm==0:
            als = None
        elif alsm==1:
            als = (math.pow(10,alsl), math.pow(10,-alsp), "keep")
        else:
            als = (math.pow(10,alsl), math.pow(10,-alsp), "remove")
        rescale = self.rescale_apply_var.get()
        if rescale==1:
            rescale_slope = toFloat(self.rescale_slope_var.get(), 1.0)
            self.rescale_slope_var.set(rescale_slope)
            rescale_intercept = toFloat(self.rescale_intercept_var.get(), 0.0)
            self.rescale_intercept_var.set(rescale_intercept)
            xgraph = rescale_slope * self.x + rescale_intercept
        else:
            xgraph = self.x
        spp.plot(ax, xgraph, self.y, self.peaks, label=label, xmin=xmin, xmax=xmax, color=color, vshift=vshift, pfilter=pfilter, spl=als)

    def save_raman(self):
        label = self.label_var.get()
        xmin = toFloat(self.xmin_var.get(), 200.0)
        self.xmin_var.set(xmin)
        xmax = toFloat(self.xmax_var.get(), 3000.0)
        self.xmax_var.set(xmax)
        alsp = toFloat(self.alsp_var.get(), 3, 1, 5)
        self.alsp_var.set(alsp)
        alsl = toFloat(self.alsl_var.get(), 3, 1, 10)
        self.alsl_var.set(alsl)
        alsm = self.alsm_var.get()
        if alsm==0:
            als = None
        elif alsm==1:
            als = (math.pow(10,alsl), math.pow(10,-alsp), "keep")
        else:
            als = (math.pow(10,alsl), math.pow(10,-alsp), "remove")
        rescale = self.rescale_apply_var.get()
        if rescale==1:
            rescale_slope = toFloat(self.rescale_slope_var.get(), 1.0)
            self.rescale_slope_var.set(rescale_slope)
            rescale_intercept = toFloat(self.rescale_intercept_var.get(), 0.0)
            self.rescale_intercept_var.set(rescale_intercept)
            xgraph = rescale_slope * self.x + rescale_intercept
        else:
            xgraph = self.x
        nx, ny = spp.clean_raman(xgraph, self.y, xmin, xmax, als)
        fname = tk.filedialog.asksaveasfilename(defaultextension='.rruff', filetypes=[("RRUFF", '*.rruff')])
        if not fname: return
        spp.write_raman(fname, nx, ny, name=label, fmt='rruff')

    def remove(self):
        self.isvalid = False
        self.controller.update()

    def toJson(self):
        j = dict(
            fname = self.fname,
            label = self.label_var.get(),
            color = self.color_var.get(),
            xmin = self.xmin_var.get(), 
            xmax = self.xmax_var.get(), 
            vshift = self.vshift_var.get(), 
            pfilter = self.pfilter_var.get(), 
            alsl = self.alsl_var.get(), 
            alsp = self.alsp_var.get(), 
            alsm = self.alsm_var.get()
           )
        return j

class GraphFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.update()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    def update(self, event=None):
        self.ax.clear()
        for sp in sorted(self.controller.spectra.values(), reverse=True, key=lambda tmp:toFloat(tmp.vshift_var.get(), 0)):
            sp.plot(self.ax)
        if len(self.controller.spectra.values())>0:
            self.ax.legend()
        self.canvas.draw()

app = Spectropy()
app.mainloop()

