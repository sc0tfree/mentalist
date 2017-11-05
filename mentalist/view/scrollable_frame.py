#!/usr/bin/python
# -*- coding: utf-8 -*-
from tkinter import *   # from x import * is bad practice
#from tkinter.ttk import *

# Adapted from https://github.com/JonathanTaquet/Oe2sSLE/blob/master/VerticalScrolledFrame.py

class VerticalScrolledFrame(Frame):
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)
        # create a canvas object and a vertical scrollbar for scrolling it

        vscrollbar = Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            # update the canvas's width and height to fit the inner frame
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.config(width=interior.winfo_reqwidth())
            if interior.winfo_reqheight() != canvas.winfo_height():
                canvas.config(height=interior.winfo_reqheight())
        interior.bind('<Configure>', _configure_interior)


        def _configure_canvas(event):
            # update the inner frame's width and height to fill the canvas
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)


if __name__ == "__main__":

    class SampleApp(Tk):
        def __init__(self, *args, **kwargs):
            root = Tk.__init__(self, *args, **kwargs)

            self.frame = VerticalScrolledFrame(root)
            self.frame.pack()
            self.label = Label(text="Shrink the window to activate the scrollbar.")
            self.label.pack()
            buttons = []
            for i in range(10):
                buttons.append(Button(self.frame.interior, text="Button " + str(i)))
                buttons[-1].pack()

    app = SampleApp()
    app.mainloop()
