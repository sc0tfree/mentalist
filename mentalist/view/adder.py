import tkinter as Tk
from functools import partial
import datetime
import tkinter.messagebox
import locale

from .base_words import BaseWordsNode, center_window
from .const import NUMBER_LIST, DATE_FORMATS, SPECIAL_CHARACTERS
from .. import model


class AdderNode(BaseWordsNode):
    '''Append and Prepend nodes. Inherits the file menu from BaseWordsNode.
    '''

    def __init__(self, controller, master=None, main=None, type_='Append', allow_remove=True, **kwargs):
        BaseWordsNode.__init__(self, controller, master=master, main=main, title=type_, allow_remove=allow_remove, **kwargs)
        self.sp_from = None
        self.sp_to = None
        self.custom_num_window = None
        self.entry_string = None
        self.date_format = Tk.StringVar()
        self.special_dlg = None
        self.chk_special = []

    def add_upper_button(self):
        mb = Tk.Menubutton(self.upper_frame, text=" + ", relief="raised", font=("Helvetica", "14"))
        mb.menu = Tk.Menu(mb, tearoff=0)
        mb["menu"] = mb.menu
        label = 'No %s' % self.title
        mb.menu.add_command(label=label, command=partial(self.controller.add_attr, label=label, node_view=self, attr_class=model.NothingAdderAttr))

        # The first few attributes are the same as BaseFile
        m_words = Tk.Menu(mb, tearoff=0)
        mb.menu.add_cascade(label='Words', menu=m_words, underline=0)
        m_words.add_command(label='Custom File...', command=partial(self.open_file_dlg, partial(self.controller.add_attr, label='File:', right_label_text='Calculating...', node_view=self, attr_class=model.FileAttr, controller=self.controller)))
        m_words.add_command(label='Custom String...', command=partial(self.open_string_popup, 'String'))
        
        self.add_file_menu(m_words, m_words)
        
        # In addition to BaseFile's attributes, we have numbers, dates,
        # and special characters
        m_numbers = Tk.Menu(mb, tearoff=0)
        mb.menu.add_cascade(label='Numbers', menu=m_numbers, underline=0)
        m_numbers.add_command(label='User Defined...', command=self.open_custom_number_dlg)
        for type_, range_str in NUMBER_LIST:
            range_ = list(map(int, range_str.split('-')))
            if type_ != 'years':
                range_str = '-'.join(['0', locale.format('%d', range_[1], grouping=True)])
            range_[1] += 1
            m_numbers.add_command(label='{}: {}'.format(type_.capitalize(), range_str),
                                  command=partial(
                                      self.controller.add_attr, label='Numbers: {} {}'.format(type_.capitalize(), range_str), node_view=self, attr_class=model.RangeAttr, start=range_[0], end=range_[1]))
        m_numbers.add_command(label='Dates...', command=self.open_date_dlg)

        mb.menu.add_command(label="Special Characters...", command=self.open_special_dlg)

        # Area and zip codes from lookup tables
        for code_type in ['Area', 'Zip']:
            m_area_zip = Tk.Menu(mb, tearoff=0)
            mb.menu.add_cascade(label='{} Codes (US)'.format(code_type), menu=m_area_zip, underline=0)
            for location_type in ['State', 'City']:
                m_sub = Tk.Menu(m_area_zip, tearoff=0)
                m_area_zip.add_cascade(label='By {}'.format(location_type), menu=m_sub, underline=0)
                target_list = sorted(model.location_codes[location_type][code_type].keys())
                for st in target_list:
                    label = '{} Codes: {} {}'.format(code_type, st, location_type if location_type == 'State' else '')
                    m_sub.add_command(label=st, command=partial(
                        self.controller.add_attr, label=label, node_view=self, attr_class=model.LocationCodeAttr, code_type=code_type, location=st, location_type=location_type))

        mb.pack(side="left", fill="x", padx=10, pady=5)

    def open_custom_number_dlg(self):
        '''Opens a popup for defining a custom number range
        '''
        self.custom_num_window = Tk.Toplevel()
        self.custom_num_window.withdraw()
        self.custom_num_window.title('{}: Number Selection'.format(self.title))
        self.custom_num_window.resizable(width=False, height=False)
        
        frame = Tk.Frame(self.custom_num_window)
        lb = Tk.Label(frame, text='Select Numbers to {}'.format(self.title))
        lb.pack(fill='both', side='top')

        # Boxes for inputting the start and endpoints
        sp_box = Tk.Frame(frame)
        lb1 = Tk.Label(sp_box, text='From')
        lb1.grid(column=0, row=0, padx=5, sticky='E')
        self.sp_from = Tk.Spinbox(sp_box, width=12, from_=0, to=10000)
        self.sp_from.grid(column=1, row=0)
        lb2 = Tk.Label(sp_box, text='To')
        lb2.grid(column=0, row=1, padx=5, sticky='E')
        self.sp_to = Tk.Spinbox(sp_box, width=12, from_=0, to=10000)
        self.sp_to.grid(column=1, row=1)
        
        # Optional zero padding
        lb_zeros = Tk.Label(sp_box, text='Pad with zeros to width:')
        lb_zeros.grid(column=0, row=2, sticky='E')
        self.sp_zfill = Tk.Spinbox(sp_box, width=12, from_=0, to=10)
        self.sp_zfill.grid(column=1, row=2)
        sp_box.pack(fill='both', side='top', padx=30, pady=20)

        # Cancel and Ok buttons
        btn_box = Tk.Frame(frame)
        btn_cancel = Tk.Button(btn_box, text='Cancel', command=self.cancel_custom_num_window)
        btn_cancel.pack(side='right', padx=10, pady=20)
        btn_ok = Tk.Button(btn_box, text='Ok', command=self.on_ok_custom_num_window)
        btn_ok.pack(side='left', padx=10, pady=20)
        btn_box.pack()
        frame.pack(fill='both', padx=10, pady=10)
        
        center_window(self.custom_num_window, self.main.master)
        
        self.custom_num_window.focus_set()

    def cancel_custom_num_window(self, *args):
        '''Cancel was pressed
        '''
        if self.custom_num_window:
            self.custom_num_window.destroy()
            self.custom_num_window = None

    def on_ok_custom_num_window(self, *args):
        '''Ok was pressed, create the attribute
        '''
        try:
            val_from = int(self.sp_from.get())
            val_to = int(self.sp_to.get())
            zfill = int(self.sp_zfill.get())
        except ValueError:
            tkinter.messagebox.showerror('Invalid Number', '"From", "To", and "Pad with zeros to width" must all be integers', parent=self.main)
            return
        if val_from > val_to:
            tkinter.messagebox.showerror('Invalid Range', '"From" value must be less than or equal to "To"', parent=self.main)
        elif val_to - val_from > 3000000:
            tkinter.messagebox.showerror('Invalid Range', 'The range must be smaller than 3 million', parent=self.main)
        else:
            if zfill == 0:
                label = 'Numbers: {} - {}'.format(val_from, val_to)
            else:
                label = 'Numbers: {} - {}, zero padding width: {}'.format(val_from, val_to, zfill)
            self.controller.add_attr(label=label,
                                     node_view=self,
                                     attr_class=model.RangeAttr,
                                     start=val_from, end=val_to+1,
                                     zfill=zfill)
            self.cancel_custom_num_window()

    def open_date_dlg(self):
        '''Open a popup for defining a range of dates
        '''
        self.custom_num_window = Tk.Toplevel()
        self.custom_num_window.withdraw()
        self.custom_num_window.title('{}: Date Selection'.format(self.title))
        self.custom_num_window.resizable(width=False, height=False)
        frame = Tk.Frame(self.custom_num_window)
        lb = Tk.Label(frame, text='Select Dates to {}'.format(self.title))
        lb.pack(fill='both', side='top')

        # Boxes for inputting the start and endpoints
        sp_box = Tk.Frame(frame)
        lb1 = Tk.Label(sp_box, text='From')
        lb1.pack(side='left', padx=5)
        cur_year = datetime.date.today().year
        self.sp_from = Tk.Spinbox(sp_box, width=12, from_=1950, to=cur_year)
        self.sp_from.pack(side='left')
        lb2 = Tk.Label(sp_box, text='To')
        lb2.pack(side='left', padx=(50, 5))
        var = Tk.IntVar()
        var.set(str(cur_year))
        self.sp_to = Tk.Spinbox(sp_box, width=12, from_=1950, to=cur_year, textvariable=var)
        self.sp_to.pack(side='right')
        sp_box.pack(fill='both', side='top', padx=30, pady=20)

        # Choose how the dates are formatted (mmddyyyy etc.)
        drop_down = Tk.OptionMenu(frame, self.date_format, *DATE_FORMATS)
        drop_down.configure(width=max(map(len, DATE_FORMATS)) + 4)
        self.date_format.set('mmddyy')
        drop_down.pack(side='top')
        
        self.date_zero_padding = Tk.IntVar()
        checkbutton = Tk.Checkbutton(frame, text='Leading zero on single-digit d or m', relief=Tk.FLAT, variable=self.date_zero_padding)
        checkbutton.pack()
        
        # Ok and cancel buttons
        btn_box = Tk.Frame(frame)
        btn_cancel = Tk.Button(btn_box, text='Cancel', command=self.cancel_custom_num_window)
        btn_cancel.pack(side='right', padx=10, pady=20)
        btn_ok = Tk.Button(btn_box, text='Ok', command=self.on_ok_date_window)
        btn_ok.pack(side='left', padx=10, pady=20)
        btn_box.pack()
        
        frame.pack(fill='both', padx=10, pady=10)
        
        center_window(self.custom_num_window, self.main.master)
        self.custom_num_window.focus_set()

    def on_ok_date_window(self):
        '''Ok was pressed, add the date range attribute
        '''
        year_limits = [1, 3000]
        try:
            val_from = int(self.sp_from.get())
            val_to = int(self.sp_to.get())
        except ValueError:
            tkinter.messagebox.showerror('Invalid Value', '"From" year and "To" year must both be integers', parent=self.main)
            return
        if val_from > val_to:
            tkinter.messagebox.showerror('Invalid Value', '"From" year must be less than or equal to "To" year', parent=self.main)
        elif val_to - val_from > 200:
            tkinter.messagebox.showerror('Invalid Value', 'Distance between "From" year and "To" year must be 200 or less', parent=self.main)
        elif val_from < year_limits[0] or val_to > year_limits[1]:
            tkinter.messagebox.showerror('Invalid Range', 'The year must be between {} and {}'.format(*year_limits), parent=self.main)
        else:
            label = 'Date: {} - {}, format: {}, {}'.format(val_from, val_to, self.date_format.get(), ['no leading zero', 'with leading zero'][self.date_zero_padding.get()==1])
            self.controller.add_attr(label=label, node_view=self, attr_class=model.DateRangeAttr, start_year=val_from, end_year=val_to+1, format=self.date_format.get(), zero_padding=self.date_zero_padding.get()==1, controller=self.controller)
            self.cancel_custom_num_window()

    def open_special_dlg(self):
        '''Open a popup for selecting special characters
        '''
        self.special_dlg = Tk.Toplevel()
        self.special_dlg.withdraw()
        self.special_dlg.title('Select Special Characters')
        self.special_dlg.resizable(width=False, height=False)
        frame = Tk.Frame(self.special_dlg)
        lb = Tk.Label(frame, text='Select Special Characters'.format(self.title))
        lb.pack(fill='both', side='top')

        box = Tk.Frame(frame)
        self.chk_special = []
        max_column_checks = 15
        for v, val in enumerate(SPECIAL_CHARACTERS):
            var = Tk.IntVar()
            tmp = Tk.Checkbutton(box, text=val, relief=Tk.FLAT, variable=var)
            self.chk_special.append(var)
            tmp.grid(row=v % max_column_checks, column=v // max_column_checks,
                     sticky='W', padx=10)
        box.pack(fill='both', side='top', padx=30, pady=20)

        # Ok and Cancel buttons
        btn_box = Tk.Frame(frame)
        btn_cancel = Tk.Button(btn_box, text='Cancel', command=self.cancel_special)
        btn_cancel.pack(side='right', padx=10, pady=20)
        btn_ok = Tk.Button(btn_box, text='Ok', command=self.on_ok_special_dlg)
        btn_ok.pack(side='left', padx=10, pady=20)
        btn_box.pack()
        frame.pack(fill='both', padx=60, pady=10)
        
        center_window(self.special_dlg, self.main.master)
        self.special_dlg.focus_set()

    def cancel_special(self, *args):
        if self.special_dlg:
            self.special_dlg.destroy()
            self.special_dlg = None

    def on_ok_special_dlg(self, *args):
        '''Ok was pressed, add the special character attribute
        '''
        checked_vals = [SPECIAL_CHARACTERS[i] for i in range(len(SPECIAL_CHARACTERS)) if self.chk_special[i].get() == 1]
        if len(checked_vals) > 0:
            label = 'Special Characters: {}'.format(' '.join(checked_vals))
            self.controller.add_attr(label=label, node_view=self, attr_class=model.StringListAttr, strings=checked_vals)
        self.cancel_special()
