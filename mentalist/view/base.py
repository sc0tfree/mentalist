# coding=utf-8
from tkinter import Frame
import tkinter as Tk
from abc import abstractmethod
from functools import partial


class BaseNode(Frame):
    '''Node view base class
    
    Has a 'title' at the left-top corner, and then a '+' button for adding
    attributes, and optional label on the right side with a word count
    '''

    def __init__(self, controller, master=None, main=None, title='Title', right_label_text=None, allow_remove=True, number=1, **kwargs):
        '''
        controller: a mentalist.controller.Controller instance
        master: the tkinter master of this view
        main: a mentalist.view.Main instance
        title: the title string to be displayed for this node
        right_label_text: an optional string to be displayed on the right-hand
                          side (word count)
        allow_remove: False if attempting to remove this node gives an error message
        number: an integer starting with 1 identifying this node's position in the chain
        '''
        Frame.__init__(self, master=master, **kwargs)
        self.controller = controller
        self.title = title
        self.main = main
        self.attrs = []
        self.number = number
        self.allow_remove = allow_remove
        self.configure(borderwidth=1, relief=Tk.RAISED)
        self.upper_frame = Frame(self)
        self.upper_frame.configure(borderwidth=1, relief=Tk.RIDGE)
        self.lb_title = Tk.Label(self.upper_frame, text='{}. {}'.format(number, title))
        self.lb_title.pack(fill="both", side="left", padx=10, pady=10)
        
        if right_label_text is not None: # this is the right-justified word count label
            self.right_label = Tk.Label(self.upper_frame, text=right_label_text, font=('Helvetica', '10', 'italic'))
            self.right_label.pack(fill="both", side="right", padx=10, pady=10)
        else:
            self.right_label = None
        
        self.upper_frame.pack(side="top", fill="x", expand=1)
        self.lower_frame = Frame(self)
        self.lower_frame.pack(side="bottom", fill="both")
        self.add_upper_button()
        if self.allow_remove:
            self.add_remove_button()
        self.pack(side="top", fill="both", padx=2, pady=2)

    @abstractmethod
    def add_upper_button(self):
        '''Creates the menubutton for adding attributes
        '''
        pass

    def add_remove_button(self):
        '''Creates the button for removing the node
        '''
        btn_add_file = Tk.Button(self.upper_frame, text=' - ')
        btn_add_file.pack(fill="both", side="right", padx=10, pady=5)
        btn_add_file.bind("<ButtonRelease-1>", partial(self.main.on_remove_node, self))

        btn_add_file = Tk.Button(self.upper_frame, text=' ↑ ')
        btn_add_file.pack(fill="both", side="right", padx=10, pady=5)
        btn_add_file.bind("<ButtonRelease-1>", partial(self.main.move_node, self, 'up'))

        btn_add_file = Tk.Button(self.upper_frame, text=' ↓ ')
        btn_add_file.pack(fill="both", side="right", padx=10, pady=5)
        btn_add_file.bind("<ButtonRelease-1>", partial(self.main.move_node, self, 'down'))

    def update_number(self, num):
        '''Updates the node number displayed on the left-hand side
        '''
        self.number = num
        self.lb_title.configure(text='{}. {}'.format(self.number, self.title))

    def add_attr(self, attr_name, right_label_text=None, *args):
        '''Add attr to the lower frame with a '-' button & title
        
        attr_name: title to be shown on the left side
        right_label_text: label string to be shown on the right side, which is
                          a word count or 'Calculating...'
        '''
        if len(self.attrs) == 0:
            self.lower_frame = Frame(self)
            self.lower_frame.pack(side="bottom", fill="both")
        attr = LabeledFrame(self.lower_frame, title=attr_name)
        btn_add_file = Tk.Button(attr, text=' - ')
        btn_add_file.pack(fill="both", side="left", padx=10, pady=5)
        btn_add_file.bind("<ButtonRelease-1>", partial(self.on_remove_attr, attr))
        lb_base_files = Tk.Label(attr, text=attr_name)
        lb_base_files.pack(fill="both", side="left", padx=10, pady=10)
        
        if right_label_text is not None:
            attr.right_label = Tk.Label(attr, text=right_label_text, font=('Helvetica', '10', 'italic'))
            attr.right_label.pack(fill="both", side="right", padx=10, pady=10)
        else:
            attr.right_label = None
        
        attr.pack(side="top", fill="both")
        self.attrs.append(attr)

    def on_remove_attr(self, attr, *args):
        '''The '-' button was pressed
        '''
        self.controller.remove_attr(self, attr)
        
    def remove_attr(self, attr):
        '''Remove the attribute, updating the display
        '''
        attr.destroy()
        self.attrs.remove(attr)
        if len(self.attrs) == 0:
            self.lower_frame.destroy()

    def get_values(self):
        '''Gets the list of attribute label strings
        '''
        return [attr.get_value() for attr in self.attrs]


class LabeledFrame(Frame):
    '''Tkinter Frame which has 'title'
    '''

    def __init__(self, master=None, title='', **kwargs):
        Frame.__init__(self, master=master, **kwargs)
        self.title = title

    def get_value(self):
        return self.title
