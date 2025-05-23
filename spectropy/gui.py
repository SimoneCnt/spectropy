#!/usr/bin/env python3

import os
import math
import random
import hashlib
import json
import traceback
import yaml
import numpy as np
import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
matplotlib.rcParams['savefig.dpi']=600
import threading

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

        self.mode_is_raman = True
        self.spectra = dict()
        self.order_status = None
        self.matchlib = None
        self.matchlib_maxsimilar = None
        self.matchlib_laser = None
        self.matchlib_infrared = None

        container = tk.Frame(self)
        container.pack(side=tk.LEFT, fill="both", expand=True)
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=0)
        container.grid_columnconfigure(1, weight=1)

        top_bar = tk.Frame(container)
        top_bar.grid(row=0, column=0, columnspan=2)

        self.graph = GraphFrame(container, self)
        self.scrollframe = ScrollableFrame(container)
        self.left = LeftPanel(self.scrollframe.interior, self)
        self.graph.grid(row=1, column=1, sticky="nsew")
        self.scrollframe.grid(row=1, column=0, sticky="nsew")
        self.left.pack()

        self.mode_is_raman_button = tk.Button(top_bar, text='Raman', command=self.ChangeMode)
        self.mode_is_raman_button.grid(row=0, column=0)
        tk.Button(top_bar, text='Open new spectrum', command=self.left.LoadNewGraph).grid(row=0, column=1)
        tk.Button(top_bar, text='Update graph', command=self.update).grid(row=0, column=2)
        tk.Button(top_bar, text='Save config', command=self.save).grid(row=0, column=3)
        tk.Button(top_bar, text='Load config', command=self.load).grid(row=0, column=4)
        tk.Button(top_bar, text='RefLib Setup', command=self.reference_library_setup).grid(row=0, column=5)
        tk.Button(top_bar, text='RefLib Raman View', command=self.reference_raman_library_view).grid(row=0, column=6)
        tk.Button(top_bar, text='RefLib IR View', command=self.reference_infrared_library_view).grid(row=0, column=7)

    def ChangeMode(self):
        self.mode_is_raman = not self.mode_is_raman
        if self.mode_is_raman:
            self.mode_is_raman_button.configure(text="Raman")
        else:
            self.mode_is_raman_button.configure(text="Infrared")

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

    def reference_library_setup(self, event=None):
        LoadRefLibWindow(self, self)

    def reference_raman_library_view(self, event=None):
        if not self.matchlib:
            print('Loading rruff Raman database...')
            self.matchlib, self.matchlib_maxsimilar, self.matchlib_laser = spp.load_raman_reference_database(justload=True)
            if not self.matchlib:
                LoadRefLibWindow(self, self)
                if not self.matchlib:
                    print('You need to load a reference library!')
                    return
        ReferenceRamanLibraryWindow(self, self)

    def reference_infrared_library_view(self, event=None):
        if not self.matchlib_infrared:
            print('Loading rruff database...')
            self.matchlib_infrared = spp.load_infrared_reference_database(justload=True)
            if not self.matchlib_infrared:
                LoadRefLibWindow(self, self)
                if not self.matchlib:
                    print('You need to load a reference library!')
                    return
        ReferenceInfraredLibraryWindow(self, self)



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


class MatchWindow(tk.Toplevel):

    def __init__(self, matches=list(), master=None, controller=None):
        super().__init__(master=master)
        self.title('Matches')
        self.controller = controller
        self.yScroll = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.yScroll.grid(row=0, column=1, sticky=tk.N+tk.S)
        self.xScroll = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.xScroll.grid(row=1, column=0, sticky=tk.E+tk.W)
        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE, xscrollcommand=self.xScroll.set, yscrollcommand=self.yScroll.set)
        self.listbox.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.xScroll['command'] = self.listbox.xview
        self.yScroll['command'] = self.listbox.yview
        self.listbox.bind('<<ListboxSelect>>', self.plot_rruff)
        for m in matches:
            self.listbox.insert(tk.END, m)

    def plot_rruff(self, event=None):
        rruff_ids = self.listbox.curselection()
        if len(rruff_ids)==1:
            lab = self.listbox.get(rruff_ids[0])
            self.controller.AddSpectrum('rruff:'+lab)


class Spectrum(tk.LabelFrame):

    def __init__(self, parent, controller, fname, label=None, color='black', xmin=200.0, xmax=3000.0, vshift=0.0, pfilter=5, alsl=3, alsp=3, alsm=0):
        tk.LabelFrame.__init__(self, parent, text='')
        self.parent = parent
        self.controller = controller
        tmp = "%s%f" % (fname, random.random())
        self.id = hashlib.md5(tmp.encode('utf-8')).hexdigest()
        self.fname = fname
        self.isvalid = False
        if fname.startswith('rruff:'):
            if self.controller.mode_is_raman:
                self.x, self.y = self.controller.matchlib[fname[6:]]
            else:
                self.x, self.y = self.controller.matchlib_infrared[fname[6:]]
            print('Opening library file', fname[6:])
            self.peaks = None
        elif not os.path.isfile(fname):
            tk.messagebox.showerror('File not found!', 'Sorry, but I could not find this file :(')
            return
        else:
            print('Opening file', fname)
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
        tk.Radiobutton(self, text='Subtract', variable=self.alsm_var, value=2, command=controller.update).grid(row=4, column=3)
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
        tk.Button(self, text='Match', command=lambda: ProgressBar(self, command=self.match_rruff,
                    message='Matching with the reference spectra database...')).grid(row=6, column=1)
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

    def get_clean_raman(self):
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
        return nx, ny

    def save_raman(self):
        fname = tk.filedialog.asksaveasfilename(defaultextension='.rruff', filetypes=[("RRUFF", '*.rruff')])
        if not fname: return
        label = self.label_var.get()
        nx, ny = self.get_clean_raman()
        spp.write_raman(fname, nx, ny, name=label, fmt='rruff')

    def remove(self):
        self.isvalid = False
        self.controller.update()

    def match_rruff(self):
        if not self.controller.matchlib:
            print('Loading rruff database...')
            try:
                self.controller.matchlib, self.controller.matchlib_maxsimilar, self.controller.matchlib_laser = spp.load_raman_reference_database(justload=True)
                self.controller.matchlib_infrared = spp.load_infrared_reference_database(justload=True)
                if not self.controller.matchlib or not self.controller.matchlib_infrared:
                    LoadRefLibWindow(self.controller, self.controller)
                    if not self.controller.matchlib or not self.controller.matchlib_infrared:
                        print('You need to load a reference library to run the matching!')
                        return
            except:
                print('Loading failed!')
                error_message = traceback.format_exc()
                print(error_message)
                return
        print('Running matching algorithms...')
        nx, ny = self.get_clean_raman()
        if self.controller.mode_is_raman:
            matches = spp.score_all(nx, ny, self.controller.matchlib)
        else:
            matches = spp.score_all(nx, ny, self.controller.matchlib_infrared)
        mw = MatchWindow(controller=self.controller, matches=matches)

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


class LoadRefLibWindow(tk.Toplevel):

    def __init__(self, master=None, controller=None):
        super().__init__(master=master)
        self.title('Load Reference Library')
        self.controller = controller
        container = tk.Frame(self)
        container.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=10)
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=0)
        container.grid_columnconfigure(1, weight=1)
        self.controller.matchlib, self.controller.matchlib_maxsimilar, self.controller.matchlib_laser = spp.load_raman_reference_database(justload=True)
        self.controller.matchlib_infrared = spp.load_infrared_reference_database(justload=True)
        font_family = tkfont.nametofont('TkDefaultFont').config()['family']
        font_size = tkfont.nametofont('TkDefaultFont').config()['size']
        pad = 3
        row = 0
        tk.Label(container, text='RRUFF Reference Library', font=(font_family, font_size, 'bold')).grid(row=row, column=0, columnspan=2, padx=pad, pady=pad)
        row += 1
        self.rruff_download_text_label = tk.Label(container, text='Last download: '+spp.get_rruff_date())
        self.rruff_download_text_label.grid(row=row, column=0, padx=pad, pady=pad)
        tk.Button(container, text='Get new version', command=lambda: ProgressBar(self, command=self.download_rruff,
                    message='Downloading the RRUFF spectra database...')).grid(row=row, column=1, padx=pad, pady=pad)
        row += 1
        tk.Label(container, text='Matching Library', font=(font_family, font_size, 'bold')).grid(row=row, column=0, columnspan=2, padx=pad, pady=pad)
        row += 1
        self.matchlib_text_label = tk.Label(container, text='')
        self.matchlib_text_label.grid(row=row, column=0, columnspan=2, padx=pad, pady=pad)
        row += 1
        tk.Label(container, text='Max similar spectra:').grid(row=row, column=0, padx=pad, pady=pad)
        self.max_similar_var = tk.StringVar(value=2)
        tk.Entry(container, textvariable=self.max_similar_var, width=11).grid(row=row, column=1, padx=pad, pady=pad)
        row += 1
        tk.Label(container, text='Preferred laser [nm]:').grid(row=row, column=0, padx=pad, pady=pad)
        self.preferred_laser_var = tk.StringVar(value=780)
        tk.Entry(container, textvariable=self.preferred_laser_var, width=11).grid(row=row, column=1, padx=pad, pady=pad)
        row += 1
        tk.Button(container, text='Generate new matching library', command=lambda: ProgressBar(self, command=self.generate_match_lib,
                    message='Generating a new matching library...')).grid(row=row, column=0, padx=pad, pady=pad)
        tk.Button(container, text='Close', command=lambda: self.destroy()).grid(row=row, column=1, padx=pad, pady=pad)
        row += 1
        self.set_labels_text()
        self.transient(master)
        self.grab_set()
        master.wait_window(self)

    def set_labels_text(self):
        if self.controller.matchlib:
            txt = 'Library available with max_similar=%d and preferred_laser=%g' % \
                    (self.controller.matchlib_maxsimilar, self.controller.matchlib_laser)
        else:
            txt = 'No library currently available. Generate one below!'
        self.matchlib_text_label.config(text=txt)
        self.rruff_download_text_label.config(text='Last download: '+spp.get_rruff_date())

    def download_rruff(self, event=None):
        spp.download_rruff(overwrite=True)
        self.controller.matchlib = None
        self.set_labels_text()

    def generate_match_lib(self, event=None):
        max_similar = int(toFloat(self.max_similar_var.get(), 2.0))
        preferred_laser = toFloat(self.preferred_laser_var.get(), 780.0)
        self.controller.matchlib, self.controller.matchlib_maxsimilar, self.controller.matchlib_laser = \
                spp.load_raman_reference_database(max_similar=max_similar, preferred_laser=preferred_laser, overwrite=True)
        self.controller.matchlib_infrared = spp.load_infrared_reference_database(overwrite=True)
        self.set_labels_text()



class ReferenceRamanLibraryWindow(tk.Toplevel):

    def __init__(self, master=None, controller=None):
        super().__init__(master=master)
        self.title('Reference Raman Library')
        self.controller = controller
        container = tk.Frame(self)
        container.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)
        self.tree = ttk.Treeview(container)
        ysb = ttk.Scrollbar(container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=ysb.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        ysb.grid(row=0, column=1, sticky='ns')
        #self.tree.heading('#0', anchor='w')
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        alldata = spp.read_raman_reference_library()
        root_node = self.tree.insert('', 'end', text='Minerals', iid='root', open=True)
        for mineral in sorted(alldata.keys()):
            mineral_node = self.tree.insert(root_node, 'end', text=mineral, iid=mineral, open=False)
            lasers = set([ laser for fname, rruffid, laser, quality in alldata[mineral]])
            for ref_laser in sorted(lasers):
                laser_node = self.tree.insert(mineral_node, 'end', text='%gnm'%(ref_laser), iid=mineral+'%g'%(ref_laser), open=False)
                for full_path, rruffid, laser, quality in alldata[mineral]:
                    if laser==ref_laser:
                        name_fmt = '%s [%d]' % (rruffid, quality)
                        tmp_node = self.tree.insert(laser_node, 'end', text=name_fmt, iid=full_path, open=False)

    def on_tree_select(self, event=None):
        focus = self.tree.focus()
        if os.path.isfile(focus):
            mineral, rruffid, _, laser, _, _, _, _ = os.path.basename(focus).split('__')
            self.controller.AddSpectrum(focus, label='%s %s (%snm)' % (mineral, rruffid, laser))


class ReferenceInfraredLibraryWindow(tk.Toplevel):

    def __init__(self, master=None, controller=None):
        super().__init__(master=master)
        self.title('Reference Infrared Library')
        self.controller = controller
        container = tk.Frame(self)
        container.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)
        self.tree = ttk.Treeview(container)
        ysb = ttk.Scrollbar(container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=ysb.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        ysb.grid(row=0, column=1, sticky='ns')
        #self.tree.heading('#0', anchor='w')
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        alldata = spp.read_infrared_reference_library()
        root_node = self.tree.insert('', 'end', text='Minerals', iid='root', open=True)
        for mineral in sorted(alldata.keys()):
            mineral_node = self.tree.insert(root_node, 'end', text=mineral, iid=mineral, open=False)
            for full_path, rruffid in alldata[mineral]:
                name_fmt = rruffid
                tmp_node = self.tree.insert(mineral_node, 'end', text=name_fmt, iid=full_path, open=False)

    def on_tree_select(self, event=None):
        focus = self.tree.focus()
        if os.path.isfile(focus):
            mineral, rruffid, _, _, _ = os.path.basename(focus).split('__')
            self.controller.AddSpectrum(focus, label='%s %s' % (mineral, rruffid))



class ProgressBar(tk.Toplevel):
    def __init__(self, master=None, controller=None, command=None, message='Please wait...'):
        super().__init__(master=None)
        self.title('Please wait...')
        self.controller = None
        tk.Label(self, text=message).pack(padx=10, pady=30)
        pb = ttk.Progressbar(self, orient='horizontal', length=200, mode='indeterminate')
        pb.pack(padx=10, pady=30)
        pb.start()
        tk.Label(self, text='').pack(padx=10, pady=10)
        self.t = threading.Thread(target=command)
        self.t.start()
        self.monitor()
        self.transient(master)
        self.grab_set()
        master.wait_window(self)
    def monitor(self):
        if self.t.is_alive():
            self.after(100, lambda: self.monitor())
        else:
            self.destroy()


def run_spectropy_gui():
    app = Spectropy()
    app.mainloop()

