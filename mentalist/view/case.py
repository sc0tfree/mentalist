import tkinter as Tk
import tkinter.messagebox

from functools import partial

from .base import BaseNode
from .main import center_window
from .. import model

class CaseNode(BaseNode):
    '''Change the case of letters in a word
    '''

    def __init__(self, controller, master=None, **kwargs):
        BaseNode.__init__(self, controller, master=master, title='Case', **kwargs)
        self.sub_popup = None
        self.chk_subs = []
        self.sub_type = None

    def add_upper_button(self):
        mb = Tk.Menubutton(self.upper_frame, text=' + ', relief='raised', font=('Helvetica', '14'))
        mb.menu = Tk.Menu(mb, tearoff=0)
        mb['menu'] = mb.menu
        label = 'No Case Change'
        mb.menu.add_command(label=label, command=partial(self.controller.add_attr, label=label, node_view=self, attr_class=model.NothingMutatorAttr))

        m_cases = [None, None]
        for i, case in enumerate(['Lowercase', 'Uppercase']):
            m_cases[i] = Tk.Menu(mb, tearoff=0)
            mb.menu.add_cascade(label='{}'.format(case), menu=m_cases[i], underline=0)
            for type_ in ['All', 'First']:
                if type_ == 'First':
                    if case == 'Lowercase':
                        suffix = ', Upper Rest'
                    else:
                        suffix = ', Lower Rest'
                else:
                    suffix = ''
                label = '{} {}{}'.format(case, type_, suffix)
                m_cases[i].add_command(label=label, command=partial(self.controller.add_attr, label=label, node_view=self, attr_class=model.CaseAttr, type_=type_, case=case))
        mb.menu.add_command(label='Toggle Nth...', command=partial(self.open_case_popup, 'Toggle'))

        mb.pack(side='left', fill='x', padx=10, pady=5)

    def open_case_popup(self, case):
        '''Open popup for defining the Nth character to toggle
        '''
        self.case_popup = Tk.Toplevel()
        self.case_popup.withdraw()
        self.case_popup.title('{}: Nth Character'.format(case))
        self.case_popup.resizable(width=False, height=False)
        frame = Tk.Frame(self.case_popup)
        lb = Tk.Label(frame, text='Select Number of Nth Character'.format(self.title))
        lb.pack(fill='both', side='top')

        sp_box = Tk.Frame(frame)
        lb1 = Tk.Label(sp_box, text='Number: ')
        lb1.pack(side='left', padx=5)
        self.sp_case = Tk.Spinbox(sp_box, width=12, from_=1, to=10000)
        self.sp_case.pack(side='left')
        sp_box.pack(fill='both', side='top', padx=30, pady=20)

        # Ok and Cancel buttons
        btn_box = Tk.Frame(frame)
        btn_cancel = Tk.Button(btn_box, text='Cancel', command=self.cancel_case_popup)
        btn_cancel.pack(side='right', padx=10, pady=20)
        btn_ok = Tk.Button(btn_box, text='Ok', command=partial(self.on_ok_case_popup, case))
        btn_ok.pack(side='left', padx=10, pady=20)
        btn_box.pack()
        frame.pack(fill='both', padx=10, pady=10)
        
        center_window(self.case_popup, self.main.master)
        self.case_popup.focus_set()

    def cancel_case_popup(self, *args):
        if self.case_popup:
            self.case_popup.destroy()
            self.case_popup = None

    def on_ok_case_popup(self, case, *args):
        '''OK in Custom Number Window was selected, create the attribute.
        case: 'Uppercase' or 'Lowercase'
        '''
        try:
            val_case = int(self.sp_case.get())
        except ValueError:
            tkinter.messagebox.showerror('Invalid Value', 'Invalid Value: N must be an integer', parent=self.main)
            return

        if val_case < 1:
            tkinter.messagebox.showerror('Invalid Value', 'Invalid Value: N must be greater than 0', parent=self.main)
            return
        
        ordinal = '%d%s' % (val_case, 'tsnrhtdd'[(val_case / 10 % 10 != 1) * (val_case % 10 < 4) * val_case % 10::4])
        label = '{}: {}'.format(case, ordinal)
        self.controller.add_attr(label=label, node_view=self, attr_class=model.CaseAttr, type_='Toggle', case=case, idx=val_case-1)
        self.cancel_case_popup()
