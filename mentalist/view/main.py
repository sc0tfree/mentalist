import tkinter as Tk
import tkinter.ttk as ttk
import tkinter.filedialog
import tkinter.messagebox

from functools import partial
import os
import sys
import webbrowser
import locale

if sys.platform == 'win32':
    locale.setlocale(locale.LC_ALL, 'en-US')
else:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

from .scrollable_frame import VerticalScrolledFrame
from .. import version, icons

class MainWindow(Tk.Frame):
    '''The Mentalist main window view
    
    This maintains a list of Node views representing the chain. It displays an
    upper status bar with estimated statistics on the output words, and
    menubuttons for adding nodes, outputting wordlists and rules, and loading
    and saving the chain. Below the status bar is a scrollable frame for
    displaying the nodes and attributes.
    '''
    
    def __init__(self, controller, master=None, width=730, height=800):
        Tk.Frame.__init__(self, master)
        self.master.title('Mentalist')
        self.master.resizable(width=True, height=True)
        self.master.geometry('{}x{}'.format(width, height))
        
        # This is the icon in Windows and X Windows
        icon_image = Tk.PhotoImage(file=os.path.join(icons.icon_dir, 'mentalist.gif'))
        self.master.tk.call('wm', 'iconphoto', self.master._w, icon_image)
        
        self.controller = controller
        self.nodes = []

        # Build the top menubar
        menubar = Tk.Menu(self.master)
                                
        def do_about_dialog():
            help_url = 'https://github.com/sc0tfree/mentalist/wiki'
            tkinter.messagebox.showinfo(message='Mentalist\nv{}\n\nby sc0tfree\n\nFor more information, visit:\n{}\n'.format(version, help_url))
        
        if sys.platform == 'darwin':
            app_menu = Tk.Menu(menubar, name='apple')
            menubar.add_cascade(menu=app_menu)
            app_menu.add_command(label='About Mentalist', command=do_about_dialog)
            self.master.config(menu=menubar) # sets the window to use this menubar
        
        self.master.config(menu=menubar)
        
        if sys.platform == 'darwin':
            cmd_key = 'Command-'
        else:
            cmd_key = 'Control-'
        
        filemenu = Tk.Menu(menubar)
        menubar.add_cascade(menu=filemenu, label='File')
        filemenu.add_command(label='Load Chain', command=self.on_load,
                             accelerator=cmd_key+'o')
        self.master.bind_all('<'+cmd_key+'o>', lambda event: self.after(100, self.on_load)) # Tk bug workaround
        filemenu.add_command(label='Save Chain', command=self.on_save,
                             accelerator=cmd_key+'s')
        self.master.bind_all('<'+cmd_key+'s>', lambda event: self.after(100, self.on_save))
        if sys.platform == 'darwin':
            quit_label = 'Quit Mentalist'
        else:
            quit_label = 'Exit'
        filemenu.add_separator()
        filemenu.add_command(label=quit_label, command=self.controller.exit,
                             accelerator=cmd_key+'q')
        self.master.bind_all('<'+cmd_key+'q>', lambda event: self.after(100, self.controller.exit))
        
        processmenu = Tk.Menu(menubar)
        menubar.add_cascade(menu=processmenu, label='Process')
        def pcommand(): self.on_process(type_='full') # after() doesn't like partial()
        processmenu.add_command(label='Full Wordlist', command=pcommand,
                                accelerator=cmd_key+'p')
        self.master.bind_all('<'+cmd_key+'p>', lambda event: self.after(100, pcommand))
        
        def bcommand(): self.on_process(type_='basewords')
        processmenu.add_command(label='Base Words Only', command=bcommand,
                                accelerator=cmd_key+'b')
        self.master.bind_all('<'+cmd_key+'b>', lambda event: self.after(100, bcommand))
        
        def rcommand(): self.on_process(type_='hashcat')
        processmenu.add_command(label='Hashcat/John Rules', command=rcommand,
                                accelerator=cmd_key+'r')
        self.master.bind_all('<'+cmd_key+'r>', lambda event: self.after(100, rcommand))
        
        helpmenu = Tk.Menu(menubar)
        menubar.add_cascade(menu=helpmenu, label='Help')
        helpmenu.add_command(label='About Mentalist', command=do_about_dialog)
        
        self.pack(padx=0, pady=0, fill=Tk.BOTH, expand=1)
        
        self.base_file_box = None

        # Upper status bar
        self.upper_status_bar = Tk.Frame(self)
        self.lb_total_words_bytes = Tk.Label(self.upper_status_bar, text='Est. Total Words / Size: Calculating...')
        self.lb_total_words_bytes.pack(side="left", padx=10, pady=10)
        self.word_count_str = None
        self.byte_count_str = None
        
        # Add Node menubutton
        mb = Tk.Menubutton(self.upper_status_bar, text=" + ", relief=Tk.RAISED, font=("Helvetica", "14"))
        mb.menu = Tk.Menu(mb, tearoff=0)
        mb["menu"] = mb.menu
        mb.menu.add_command(label='Case', command=partial(self.controller.add_node, 'Case'))
        mb.menu.add_command(label='Substitution', command=partial(self.controller.add_node, 'Substitution'))
        mb.menu.add_command(label='Prepend', command=partial(self.controller.add_node, 'Prepend'))
        mb.menu.add_command(label='Append', command=partial(self.controller.add_node, 'Append'))
        mb.pack(side="right", fill="both", padx=10, pady=5)
        
        # Process menubutton
        self.process_mb = Tk.Menubutton(self.upper_status_bar, text='Process', relief='raised')
        self.process_mb.menu = Tk.Menu(self.process_mb, tearoff=0)
        self.process_mb["menu"] = self.process_mb.menu
        self.process_mb.menu.add_command(label='Full Wordlist', command=partial(self.on_process, type_='full'))
        self.process_mb.menu.add_command(label='Base Words Only', command=partial(self.on_process, type_='basewords'))
        self.process_mb.menu.add_command(label='Hashcat/John Rules', command=partial(self.on_process, type_='hashcat'))
        self.process_mb.pack(fill='both', side='right', padx=10, pady=5)
        
        # Load/Save menubutton
        self.save_mb = Tk.Menubutton(self.upper_status_bar, text='Load/Save', relief='raised')
        self.save_mb.menu = Tk.Menu(self.save_mb, tearoff=0)
        self.save_mb["menu"] = self.save_mb.menu
        self.save_mb.menu.add_command(label='Load Chain', command=self.on_load)
        self.save_mb.menu.add_command(label='Save Chain', command=self.on_save)
        self.save_mb.pack(fill='both', side='right', padx=10, pady=5)
        
        self.upper_status_bar.pack(side="top", fill="both") # The upper status bar is now complete

        # This is the scrollable area below the upper status bar where nodes
        # and attributes are displayed
        self.scr_box = VerticalScrolledFrame(self)
        self.scr_box.pack(fill='both', side='top', expand=True)
        
        # Center the main window on the screen
        self.master.update_idletasks()
        self.master.withdraw() # hide the main window until it is centered
        w = self.master.winfo_screenwidth()
        h = self.master.winfo_screenheight()
        size = tuple(int(_) for _ in self.master.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        
        margins = (h-height) / 2
        if margins < 100: # Don't waste any vertical space on smaller screens,
            y = 0    # push the window right up to the top.
        elif margins < 200:
            y = 50   # window is partial way down, but not into the bottom 100px on screen
        else:
            y = h/2 - size[0]/2 # big screen - center vertically
        
        if h < size[1]: # shrink the window vertically if it doesn't fit
            size[1] = h - 10
            y = 0
        
        self.master.geometry("%dx%d+%d+%d" % (size + (x, y)))
        self.master.deiconify() # show the main window
        self.master.protocol("WM_DELETE_WINDOW", self.controller.exit)
        
        # The Progress popup appears while a wordlist is being output
        self.progress_popup = None
        s = ttk.Style() # Create a style for use on the progressbar
        s.theme_use('classic')
        aqua_blue = '#4899f9'
        s.configure('plain.Horizontal.TProgressbar', foreground=aqua_blue, background=aqua_blue)

    def set_base_file_box(self, base_file_box):
        self.base_file_box = base_file_box
        self.pack(fill="both", padx=10, pady=10, expand=True)

    def on_process(self, type_):
        '''An item from the Process menubutton has been selected
        '''
        if self.process_mb['state'] == 'disabled':
            return
        
        if type_ == 'hashcat':
            if not self.controller.check_hashcat_compatible():
                if not tkinter.messagebox.askokcancel('Warning', 'Replace First and Replace Last are incompatible with Hashcat/John rules. Continue with all instances of First and Last changed to All?', parent=self.master):
                    return
            filetypes = [("Rule files", "*.rules")]
        else:
            filetypes=[("Text files", "*.txt")]
        
        opt_file_path = tkinter.filedialog.asksaveasfile(parent=self.master, filetypes=filetypes)
        if opt_file_path:
            print()
            print('---------------------\n' \
                  '| Output initiated: |\n' \
                  '---------------------')
            print()
            print('File:', opt_file_path.name)
            print('Mode:', {'full': 'Full Wordlist',
                            'basewords': 'Base Words Only',
                            'hashcat': 'Hashcat/John Rules'}[type_])
            print()
            print('Chain')
            print('---------------------')
            
            for i, node in enumerate(self.nodes):
                print('Node {}: {}'.format(i+1, node.title))
            
                for attr_label in node.get_values():
                    print('\t-', attr_label)
        
                print()
            
            if type_ == 'full':
                self.controller.process(opt_file_path.name, basewords_only=False)
            elif type_ == 'basewords':
                self.controller.process(opt_file_path.name, basewords_only=True)
            elif type_ == 'hashcat':
                # Build up a pretty printed string for the hashcat comments
                lines = ['# Rules Generated by', '# Mentalist', '#',
                         '# Rule chain', '# ---------------------']
                if len(self.nodes) > 1:
                    for i, node in enumerate(self.nodes[1:]):
                        lines.append('# Node {}: {}'.format(i+1, node.title))
                        for attr_label in node.get_values():
                            lines.append('# \t-' + attr_label)
                
                self.controller.to_hashcat(opt_file_path.name, comments='\n'.join(lines))
    
    def on_save(self):
        '''Save Chain was selected
        '''
        path = tkinter.filedialog.asksaveasfile(parent=self.master, filetypes=[("Mentalist chain files", "*.mentalist")])
        if path:
            self.controller.save(path.name)
    
    def on_load(self):
        '''Load Chain was selected
        '''
        answer = tkinter.messagebox.askyesno("Load chain", "Are you sure you want to discard the current chain and load one from a file?", icon='warning', parent=self.master)
        if answer:
            try:
                path = tkinter.filedialog.askopenfile(parent=self.master)
            except OSError as e:
                tkinter.messagebox.showerror('File error', 'Could not open chain file: {}'.format(e.strerror), parent=self.master)
                return
            if path:
                self.controller.load(path.name)

    def on_remove_node(self, node, *args):
        '''A node's delete button was pressed
        '''
        answer = tkinter.messagebox.askyesno("Remove Node", "Are you sure you want to delete this node?", icon='warning', parent=self.master)
        if answer:
            self.controller.remove_node(self.nodes.index(node))

    def remove_node(self, node_idx):
        '''Update the view to reflect the deleted node
        '''
        self.nodes[node_idx].destroy()
        del self.nodes[node_idx]
        self.sort_numbers()

    def move_node(self, node, direction, *args):
        '''One of a node's arrow buttons was pushed
        '''
        index = self.nodes.index(node)
        
        sub_list = self.controller.move_node(index, direction)
        
        if sub_list is None:
            return # Can't go any higher
        
        for s in sub_list:
            s.pack_forget()
        for s in sub_list:
            s.pack(fill='both', expand=True, side='top')
        self.sort_numbers()
        self.update()

    def sort_numbers(self):
        '''Update the numbering of nodes in the chain
        '''
        for i, node in enumerate(self.nodes):
            node.update_number(i + 1)

    def _update_counts(self):
        '''Update word and byte count labels
        '''
        text = 'Est. Total Words / Size:     {} / {}'.format(self.word_count_str,
                                                             self.byte_count_str)
        self.lb_total_words_bytes.configure(text=text)

    def update_total_words(self, words):
        '''Set the word count and update the display
        '''
        self.word_count_str = word_count_to_string(words)
        self._update_counts()

    def update_est_opt_size(self, byte_count):
        '''Set the byte count and update the display
        '''
        self.byte_count_str = get_size_str(byte_count)
        self._update_counts()

    def start_progress_bar(self, path):
        '''Pop up a progress bar starting at 0% while the wordlist is processing
        '''
        self.progress_path = path
        
        self.progress_popup = Tk.Toplevel()
        self.progress_popup.title('Processing')
        self.progress_popup.resizable(width=False, height=False)
        self.progress_popup.grab_set()
        self.progress_popup.overrideredirect(1)
        
        progress_frame = Tk.Frame(self.progress_popup, borderwidth=1, relief=Tk.RAISED)
        progress_frame.pack(side='top', fill='both', padx=10, pady=10)
        
        path_label = Tk.Label(progress_frame, text='', font=('Helvetica', '12'))
        path_label.pack(padx=10, pady=10)
        path_label.configure(text="Processing to '{}'...".format(path))
        
        self.progress_var = Tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
            length=300, maximum=100, style='plain.Horizontal.TProgressbar')
        self.progress_bar.pack(side='left', padx=10, pady=10)
        
        self.progress_percent_lb = Tk.Label(progress_frame, text='', font=('Helvetica', '12'))
        self.progress_percent_lb.pack(side='left', padx=10, pady=10)
        self.progress_percent_lb.configure(text='0%')
        
        def stop(): self.controller.stop_processing_flag = True
        self.progress_btn = Tk.Button(progress_frame, text='Cancel', command=stop)
        self.progress_btn.pack(side='left', padx=10, pady=20)
        
        center_window(self.progress_popup, self.master)
        self.progress_popup.update()

    def update_progress_bar(self, percent):
        '''Advance the progress bar
        '''
        self.progress_bar.update()
        self.progress_var.set(percent)
        self.progress_percent_lb.configure(text='{}%'.format(percent))
    
    def cancel_progress_bar(self):
        '''Processing was canceled for some reason, destroy the progress bar
        '''
        if self.progress_popup is not None:
            self.progress_popup.destroy()

    def progress_bar_done(self):
        '''Processing is done, switch the 'Cancel' button to 'Processing
        Complete' and hide the progress bar
        '''
        if self.progress_popup is not None:
            self.progress_percent_lb.destroy()
            self.progress_bar.destroy()
            self.process_mb.configure(state='normal') # It sometimes seems to stick in 'active' state
            
            def close(): self.progress_popup.destroy()
            self.progress_btn.configure(text='Processing complete!', default='active', command=close)
            self.progress_btn.focus()
            self.progress_popup.bind('<Return>', lambda e: close())
            self.progress_btn.pack(side='top')

    def showerror(self, title, message):
        '''This is used by the controller to show error message popups
        '''
        tkinter.messagebox.showerror(title, message, parent=self.master)


def get_size_str(byte_count_, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(byte_count_) < 1024.0:
            return '%3.1f%s%s' % (byte_count_, unit, suffix)
        byte_count_ /= 1024.0
    return '%.1f%s%s' % (byte_count_, 'Y', suffix)


def word_count_to_string(words):
    '''Get a string representation of the word count
    '''
    if isinstance(words, int):
        words = locale.format("%d", words, grouping=True) # add commas
    return words


def center_window(w, master):
    '''Horizontally and vertically center the window w's position within the
    master window
    '''
    w.update_idletasks()
    popup_w = w.winfo_reqwidth()
    popup_h = w.winfo_reqheight()
    master_w = master.winfo_width()
    master_h = master.winfo_height()
    w_margin = (master_w - popup_w) / 2
    h_margin = (master_h - popup_h) / 2
    geometry = (popup_w, popup_h, master.winfo_x()+w_margin, master.winfo_y()+h_margin)
    w.geometry('%dx%d+%d+%d' % geometry)
    w.deiconify()

