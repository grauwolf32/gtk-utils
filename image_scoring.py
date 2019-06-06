import gi
import os
import sys
import sqlite3

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gio

def get_score(conn, imghash):
    sql = "SELECT score FROM images WHERE hash = '{}';"
    res = conn.execute(sql.format(imghash)).fetchone()
    if res:
        res = res[0]
        return res

    return -1

class LabelWindow(Gtk.Window):
    def on_open_clicked (self, button):
        dialog = Gtk.FileChooserDialog ("Open Folder", button.get_toplevel(), Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_button (Gtk.STOCK_CANCEL, 0)
        dialog.add_button (Gtk.STOCK_OK, 1)

        if dialog.run() == 1:
            self.folder_path = dialog.get_filename()
            self.update_folder(self.folder_path)

        dialog.destroy()

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
            self.update_score()
            self.current_idx = self.current_idx - 1
            self.current_idx = self.current_idx % n

            self.update_image()
            self.reset_scale()

    def go_right(self, button):
        n = len(self.image_list)

        if n > 0:
            self.update_score()
            self.current_idx = self.current_idx + 1
            self.current_idx = self.current_idx % n

            self.update_image()
            self.reset_scale()

    def skip_scored(self, button):
        n = len(self.image_list)

        if n > 0:
            while self.current_idx < n-1:
                imghash = self.image_list[self.current_idx].split('.')[0]
                s = get_score(self.conn, imghash)
                if s < 0:
                    break

                self.current_idx += 1
            
            self.update_image()
            self.reset_scale()

    def scale_change(self, s, _):
        self.score = self.scale.get_value()

    def reset_scale(self):
        n = len(self.image_list)
        score = 5

        if n > 0:
            imghash = self.image_list[self.current_idx].split('.')[0]
            s = get_score(self.conn, imghash)

            print ("current id {} score: {} hash: {}".format(self.current_idx, s, imghash))

            if int(s) != -1:
                score = s

        self.score = score
        self.scale.set_value(score)
            
    def update_folder(self, folder_path):
        self.folder_path = folder_path
        self.image_list = [f for f in os.listdir(self.folder_path) if f.split('.')[-1] in ".jpeg.jpg.png.bmp"]
        self.current_idx = 0
        self.update_image()
        self.reset_scale()

    def update_score(self):
        n = len(self.image_list)

        if n > 0:
            img_file = self.image_list[self.current_idx]
            imghash = img_file.split('.')[0]
            score = self.score

            print ("update id {} score: {}".format(self.current_idx, score))

            try:
                sql = "UPDATE images SET score = '{}' WHERE hash = '{}';"
                self.conn.execute(sql.format(score, imghash))
                self.conn.commit()
            except:
                print ("{}".format(sys.exc_info()))



    def __init__(self):
        Gtk.Window.__init__(self, title="Image scoring")

        self.conn = sqlite3.connect("forbidden.db")
        
        self.default_imgsize = (960,540)
        self.set_default_size(980, 540)
        self.set_border_width(10)
        self.image = Gtk.Image() 

        self.folder_path = "./"
        self.current_idx = 0

        ad1 = Gtk.Adjustment(value=5, lower=0, upper=10)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL, adjustment=ad1)
        self.scale.set_inverted(True)

        self.scale.connect("button-release-event", self.scale_change)
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

        button = Gtk.Button()
        button.add(Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE))
        button.connect_after('clicked', self.skip_scored)
        box.add(button)

        hb.pack_start(box)
        #--------------------------------------------------------------

        hbox = Gtk.Box(spacing=10)
        hbox.set_homogeneous(False)

        hbox.pack_start(self.image, False, False, 0)
        hbox.pack_end(self.scale, False, False, 0)
        self.add(hbox)

window = LabelWindow()        
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()