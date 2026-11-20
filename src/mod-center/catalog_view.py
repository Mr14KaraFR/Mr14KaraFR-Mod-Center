"""Scrollable, responsive cards for the mods and applications catalogue."""
import tkinter as tk
from tkinter import ttk


class CatalogView(tk.Frame):
    def __init__(self, parent, background):
        super().__init__(parent, bg=background)
        self.frames = []
        self.columns = 2
        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0,
                                height=1, takefocus=True)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                       style="Catalog.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y", padx=(10, 0))
        self.canvas.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(self.canvas, bg=background)
        self.window = self.canvas.create_window(0, 0, window=self.content, anchor="nw")
        self.content.bind("<Configure>", self.update_region)
        self.canvas.bind("<Configure>", self.resize)
        self.winfo_toplevel().bind("<MouseWheel>", self.scroll_wheel, add="+")
        for key, amount in (("<Down>", 1), ("<Up>", -1)):
            self.canvas.bind(key, lambda event, n=amount: self.scroll(n, "units"))
        for key, amount in (("<Next>", 1), ("<Prior>", -1)):
            self.canvas.bind(key, lambda event, n=amount: self.scroll(n, "pages"))
        self.canvas.bind("<Home>", lambda event: self.scroll_to(0))
        self.canvas.bind("<End>", lambda event: self.scroll_to(1))

    def add(self, frame):
        self.frames.append(frame)
        self.arrange()

    def clear(self):
        for child in self.content.winfo_children():
            child.destroy()
        self.frames.clear()

    def resize(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)
        columns = 2 if event.width >= 940 else 1
        if columns != self.columns:
            self.columns = columns
            self.arrange()

    def arrange(self):
        for column in range(2):
            self.content.columnconfigure(column, weight=1 if column < self.columns else 0,
                                          uniform="catalog" if column < self.columns else "")
        for index, frame in enumerate(self.frames):
            frame.grid(row=index // self.columns, column=index % self.columns,
                       sticky="nsew", padx=(0, 12) if self.columns == 2 and index % 2 == 0 else 0,
                       pady=(0, 14))

    def update_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def scroll_wheel(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        while widget is not None and widget is not self:
            widget = widget.master
        if widget is self and event.delta:
            units = -int(event.delta / 120) or (-1 if event.delta > 0 else 1)
            return self.scroll(units, "units")

    def scroll(self, amount, kind):
        if self.content.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(amount, kind)
        return "break"

    def scroll_to(self, fraction):
        self.canvas.yview_moveto(fraction)
        return "break"
