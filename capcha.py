
import gi
import os
import sys
import sqlite3

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gio
from gi.repository import Gdk

finished_capcha = set()
with open("capcha_vals") as f:
    for line in f:
        finished_capcha.add(line.split(" ")[0].strip())

class LabelWindow(Gtk.Window):
    def on_open_clicked (self, button):
        dialog = Gtk.FileChooserDialog ("Open Folder", button.get_toplevel(), Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_button (Gtk.STOCK_CANCEL, 0)
        dialog.add_button (Gtk.STOCK_OK, 1)

        if dialog.run() == 1:
            self.folder_path = dialog.get_filename()
            self.update_folder(self.folder_path)

        dialog.destroy()

        curr_image = self.image_list[self.current_idx]
        img_ind = curr_image.split("/")[-1].split('.')[0]
        
        while img_ind in finished_capcha:
            self.go_right(None)
            curr_image = self.image_list[self.current_idx]
            img_ind = curr_image.split("/")[-1].split('.')[0]

    def update_image(self):
        n = len(self.image_list)

        if n > 0:
            img_file = "/".join((self.folder_path, self.image_list[self.current_idx]))
            w = self.default_imgsize[0]
            h = self.default_imgsize[1]

            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename=img_file, width=w, height=h, preserve_aspect_ratio=True)
            self.image.set_from_pixbuf(pixbuf)

    def go_left(self, button):
        n = len(self.image_list)

        if n > 0:
            self.current_idx = self.current_idx - 1
            self.current_idx = self.current_idx % n

            self.update_image()

    def go_right(self, button):
        n = len(self.image_list)

        if n > 0:
            self.current_idx = self.current_idx + 1
            self.current_idx = self.current_idx % n

            self.update_image()
            
    def on_key_press_event(self, widget, event):
        # check the event modifiers (can also use SHIFTMASK, etc)
        print(event.keyval)
        enter = (event.keyval == 65293)
        # see if we recognise a keypress
        if enter:
            self.on_submit(None)

    def update_folder(self, folder_path):
        self.folder_path = folder_path
        self.image_list = [f for f in os.listdir(self.folder_path) if f.split('.')[-1] in ".jpeg.jpg.png.bmp"]
        self.current_idx = 0
        self.update_image()

    def on_submit(self, button):
        text = self.entry.get_text()
        curr_image = self.image_list[self.current_idx]
        img_ind = curr_image.split("/")[-1].split('.')[0]
        print(text, curr_image, img_ind)
        open("capcha_vals", "a").write("{} {}\n".format(img_ind, text))
        self.go_right(None)
        self.entry.set_text("")

    def __init__(self):
        Gtk.Window.__init__(self, title="Image scoring")

        self.conn = sqlite3.connect("forbidden.db")
        
        self.default_imgsize = (400,300)
        self.set_default_size(450, 350)
        self.set_border_width(10)
        self.image = Gtk.Image() 

        self.folder_path = "./"
        self.current_idx = 0
        self.update_folder(self.folder_path)

        # -------------------------------------------------------------
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Navigation"
        self.set_titlebar(hb)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="mail-send-receive-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.connect_after('clicked', self.on_open_clicked)
        button.add(image)

        hb.pack_end(button)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(box.get_style_context(), "linked")

        button = Gtk.Button()
        button.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))
        button.connect_after('clicked', self.go_left)
        box.add(button)

        button = Gtk.Button()
        button.add(Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE))
        button.connect_after('clicked', self.go_right)
        box.add(button)


        hb.pack_start(box)
        #--------------------------------------------------------------

        hbox = Gtk.Box(spacing=10, orientation=Gtk.Orientation.VERTICAL)
        hbox.set_homogeneous(False)

        hbox.pack_start(self.image, False, False, 0)
        #hbox.pack_end(self.scale, False, False, 0)

        vbox = Gtk.Box(spacing=10)

        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry , False, False, 0)

        self.submit = Gtk.Button("Submit")
        self.submit.connect("clicked", self.on_submit)

        vbox.pack_start(self.submit, True, True, 0)
        hbox.pack_start(vbox, False, False, 0)

        self.add(hbox)
        self.connect("key-press-event",self.on_key_press_event)

        

window = LabelWindow()        
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()
