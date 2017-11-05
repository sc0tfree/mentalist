import tkinter as Tk
from functools import partial

from .base import BaseNode
from .main import center_window
from .const import SUBSTITUTION_CHECKS, SPECIAL_TYPES
from .. import model

class SubstitutionNode(BaseNode):
    '''Substitute one character for another
    '''
    def __init__(self, controller, master=None, **kwargs):
        BaseNode.__init__(self, controller, master=master, title='Substitution', **kwargs)
        self.case_popup = None
        self.sp_case = None

    def add_upper_button(self):
        mb = Tk.Menubutton(self.upper_frame, text=' + ', relief='raised', font=('Helvetica', '14'))
        mb.menu = Tk.Menu(mb, tearoff=0)
        mb['menu'] = mb.menu
        label = 'No Substitution'
        mb.menu.add_command(label=label, command=partial(self.controller.add_attr, label=label, node_view=self, attr_class=model.NothingMutatorAttr))
        mb.menu.add_command(label='Replace All Instances...', command=partial(self.open_sub_popup, 'All'))
        mb.menu.add_command(label='Replace First Instance...', command=partial(self.open_sub_popup, 'First'))
        mb.menu.add_command(label='Replace Last Instance...', command=partial(self.open_sub_popup, 'Last'))

        mb.pack(side='left', fill='x', padx=10, pady=5)
    
    def open_sub_popup(self, type_):
        '''Opens popup for defining the characters to substitute
        type_: 'All', 'First', or 'Last'
        '''
        self.sub_popup = Tk.Toplevel()
        self.sub_popup.withdraw()
        self.sub_popup.title('Replace {}'.format(type_))
        self.sub_popup.resizable(width=False, height=False)
        frame = Tk.Frame(self.sub_popup)
        lb = Tk.Label(frame, text='Select Substitution Checks'.format(self.title))
        lb.pack(fill='both', side='top')

        # Create a checkbox for each possible character substitution
        box = Tk.Frame(frame)
        self.chk_subs = []
        max_column_checks = 15
        for v in range(len(SUBSTITUTION_CHECKS)):
            val = SUBSTITUTION_CHECKS[v]
            var = Tk.IntVar()
            tmp = Tk.Checkbutton(box, text=val, relief=Tk.FLAT, variable=var,
                                 font=('Courier', '14'))
            self.chk_subs.append(var)
            
            # Split the checks into columns so the window isn't too tall
            tmp.grid(row=v % max_column_checks, column=v // max_column_checks,
                     sticky='W', padx=10)
        box.pack(fill='both', side='top', padx=30, pady=20)

        box_type = Tk.Frame(frame)
        self.sub_type = Tk.IntVar()
        for i, val in enumerate(SPECIAL_TYPES):
            tmp = Tk.Radiobutton(box_type, text=val, relief=Tk.FLAT, variable=self.sub_type, value=i)
            tmp.pack(fill='both', side='left')
        box_type.pack(fill='both', side='top', padx=30, pady=20)

        btn_box = Tk.Frame(frame)
        btn_cancel = Tk.Button(btn_box, text='Cancel', command=self.cancel_sub_popup)
        btn_cancel.pack(side='right', padx=10, pady=20)
        btn_ok = Tk.Button(btn_box, text='Ok', command=partial(self.on_ok_sub_popup, type_))
        btn_ok.pack(side='left', padx=10, pady=20)
        btn_box.pack()
        frame.pack(fill='both', padx=40, pady=10)
        
        center_window(self.sub_popup, self.main.master)
        self.sub_popup.focus_set()

    def cancel_sub_popup(self, *args):
        if self.sub_popup:
            self.sub_popup.destroy()
            self.sub_popup = None

    def on_ok_sub_popup(self, type_, *args):
        '''OK in substitution popup was selected, create the attribute
        type_: 'All', 'First', or 'Last'
        '''
        checked_vals = [SUBSTITUTION_CHECKS[i] for i in range(len(SUBSTITUTION_CHECKS)) if self.chk_subs[i].get() == 1]
        if len(checked_vals) > 0:
            special_type = SPECIAL_TYPES[self.sub_type.get()]
            label = 'Replace {}: {} ({})'.format(type_, ', '.join(checked_vals),
                                                 special_type)
            self.controller.add_attr(label=label, node_view=self, attr_class=model.SubstitutionAttr, type_=type_, checked_vals=checked_vals, all_together=special_type=='All together')
        self.cancel_sub_popup()
