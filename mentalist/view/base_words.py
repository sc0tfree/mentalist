import tkinter as Tk
import tkinter.filedialog
import tkinter.messagebox

from functools import partial

from .base import BaseNode
from .main import center_window
from .. import model

class FileErrorFrame(Tk.Frame):
    '''This puts the error message along side a "Locate file..." button inside
    the file attribute.
    '''
    def __init__(self, controller, master, node, add_file_command):
        self.controller = controller
        self.master = master
        self.node = node
        
        button = Tk.Button(master, text='Fix...')
        button.pack(side='right')
        button.bind("<ButtonRelease-1>", partial(self.on_ok_locate_file, add_file_command))
    
        label = Tk.Label(master, text='Missing file', foreground="red")
        label.pack(side='right')
        
        self.string_popup = None

    def on_ok_locate_file(self, add_file_command, *args):
        # Add the new file attribute and remove the old one
        if add_file_command():
            self.controller.remove_attr(self.node, self.master)
            self.controller.update_counts()

class BaseWordsNode(BaseNode):
    '''A chain always begins with a BaseWordsNode. Derived class AdderNode
    re-uses the file reading code, but cannot begin a chain.
    '''

    def __init__(self, controller, master=None, main=None, title='Base Words', allow_remove=False, **kwargs):
        BaseNode.__init__(self, controller, master=master, main=main, title=title, allow_remove=allow_remove, **kwargs)
        self.file_error_frames = {} # key: attr, value: FileErrorFrame instance

    def add_file_menu(self, menu_button, menu):
        '''Adds items representing the built-in files to the given menu_button
        and menu
        '''
        for label, value in model.FileAttr.named_files:
            if isinstance(value, str):
                menu.add_command(label=label, command=partial(self.controller.add_attr, label=label, right_label_text='Calculating...', node_view=self, attr_class=model.FileAttr, path=value, controller=self.controller))
            else:
                submenu = Tk.Menu(menu_button, tearoff=0)
                menu.add_cascade(label=label, menu=submenu, underline=0)
                
                for sublabel, subvalue in value:
                    submenu.add_command(label=sublabel, command=partial(self.controller.add_attr, label='%s: %s' % (label, sublabel), right_label_text='Calculating...', node_view=self, attr_class=model.FileAttr, path=subvalue, controller=self.controller))

    def add_upper_button(self):
        mb = Tk.Menubutton(self.upper_frame, text=" + ", relief="raised", font=("Helvetica", "14"))
        mb.menu = Tk.Menu(mb, tearoff=0)
        mb["menu"] = mb.menu
        
        label = 'No Words'
        mb.menu.add_command(label=label, command=partial(self.controller.add_attr, label=label, node_view=self, attr_class=model.NothingAdderAttr))
        
        mb.menu.add_command(label="Custom File...", command=partial(self.open_file_dlg, partial(self.controller.add_attr, label='File:', right_label_text='Calculating...', node_view=self, attr_class=model.FileAttr, controller=self.controller)))
        
        mb.menu.add_command(label="Custom String...", command=partial(self.open_string_popup, 'String'))
        
        self.add_file_menu(mb, mb.menu)
        
        mb.pack(side="left", fill="x", padx=10, pady=5)

    def open_string_popup(self, type_):
        '''Custom string input popup window
        type_: the name to appear in labels ('Base Words')
        '''
        self.string_popup = Tk.Toplevel()
        self.string_popup.withdraw()
        self.string_popup.title('Input Custom String ({})'.format(type_))
        self.string_popup.resizable(width=False, height=False)
        frame = Tk.Frame(self.string_popup)
        lb = Tk.Label(frame, text='Input Custom String - {}'.format(self.title))
        lb.pack(fill='both', side='top')

        box = Tk.Frame(frame)
        lb1 = Tk.Label(box, text='String: ')
        lb1.pack(side='left', padx=5)
        self.entry_string = Tk.Entry(box, width=25)
        self.entry_string.pack(side='left')
        box.pack(fill='both', side='top', padx=30, pady=20)

        btn_box = Tk.Frame(frame)
        btn_cancel = Tk.Button(btn_box, text='Cancel', command=self.cancel_string_popup)
        btn_cancel.pack(side='right', padx=10, pady=20)
        btn_ok = Tk.Button(btn_box, text='Ok', command=partial(self.on_ok_string_popup, type_))
        btn_ok.pack(side='left', padx=10, pady=20)
        btn_box.pack()
        frame.pack(fill='both', padx=10, pady=10)
        
        center_window(self.string_popup, self.main.master)
        self.string_popup.focus_set()

    def cancel_string_popup(self, *args):
        if self.string_popup:
            self.string_popup.destroy()
            self.string_popup = None

    def on_ok_string_popup(self, type_, *args):
        '''OK in Custom String Window was selected, create the attribute
        type_: the name to appear in labels ('Base Words')
        '''
        val = self.entry_string.get()
        if val != '':
            label = "{}: '{}'".format(type_, val)
            self.controller.add_attr(label=label, node_view=self, attr_class=model.StringListAttr, strings=[val])
            self.cancel_string_popup()

    def remove_attr(self, attr, *args):
        BaseNode.remove_attr(self, attr, *args)
        if (not self.allow_remove) and len(self.attrs) == 0:
            self.main.process_mb.configure(state='disabled')
            self.main.base_file_box.config(highlightbackground="red", highlightcolor="red", highlightthickness=1)
        if attr in self.file_error_frames:
            del self.file_error_frames[attr]

    def add_attr(self, attr_name, *args):
        BaseNode.add_attr(self, attr_name, *args)
        self.main.process_mb.configure(state='normal')
        if self.main.base_file_box:
            self.main.base_file_box.config(highlightthickness=0)

    def set_word_count(self, word_count):
        if isinstance(word_count, int):
            word_count = locale.format("%d", word_count, grouping=True) # add commas
        self.word_count_label.configure(text=word_count)

    def open_file_dlg(self, callback, *args):
        '''Displays the Custom File dialog
        Returns a bool indicating whether a new file was obtained
        '''
        try:
            file_path = tkinter.filedialog.askopenfile(parent=self.main)
        except Exception as e:
            tkinter.messagebox.showerror('Could not open file', 'Could not open file: {}'.format(str(e)), parent=self.main)
            return False
        
        if file_path:
            callback(label='File: %s' % file_path.name, path=file_path.name, controller=self.controller)
            return True
        else:
            return False

    def set_file_error(self, attr, message):
        if not attr in self.file_error_frames:
            attr.config(highlightbackground="red", highlightcolor="red", highlightthickness=1)
        
            self.file_error_frames[attr] = FileErrorFrame(self.controller, attr, self, add_file_command=partial(self.open_file_dlg, partial(self.controller.add_attr, right_label_text='Calculating...', node_view=self, attr_class=model.FileAttr, controller=self.controller)))
        # else the attr was already missing, don't add another Locate button
