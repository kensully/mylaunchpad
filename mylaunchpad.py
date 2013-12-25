#!/usr/bin/env python
import os, sys
import pygtk
import logging
import re
from appsmenu import MenuCache
pygtk.require('2.0')

ICON_SIZE = 64
ROW_PADDING = 32
COL_PADDING = 32
BUTTON_PADDING = 22
CONTAINER_PADDING = 4
OPACITY = 85

try:
    from lxml import etree
except:
    print "lxml missing, please install pyhton-lxml "

try:
    import gtk
except:
    print "pyGTK missing, install python-gtk2"
    sys.exit()

try:
    import cairo
except:
    print "Cairo modules missing, install python-cairo"

try:
    from PIL import Image, ImageFilter
except:
    print "PIL missing, install python-imaging"
    sys.exit()

class AppStore:
    def __init__(self, mainbox, launcher):
        self.window = launcher.window
        self.mainbox = mainbox
        
        # Get Menu
	menu = MenuCache()
        self.appsmenu = menu.getMenu()

        # Get Categories
        categories = self.getCategories()
 
        self.mainContainer = gtk.HBox(False, 0)
	self.buttonsContainer = gtk.VBox(False)

        # Get maxcolums and max rows
        self.maxcolums = self.calculate_maxcolums()
        self.maxrows = self.calculate_maxrows()

        self.font_style = self.buttonsContainer.get_style().font_desc.to_string()
        self.fontsize = int(re.search(r"(\d+)", self.font_style).group(1))
        
        # Pack in the button box into the panel box, with two padder boxes
	self.mainContainer.pack_start(gtk.HBox(), True, True)
	self.mainContainer.pack_start(self.buttonsContainer, False, True, 0)
        self.mainContainer.pack_start(gtk.HBox(), True, True)
        
        self.add_toolbar(mainbox, categories, launcher)
        mainbox.pack_start(self.mainContainer)

        self.load("ALL")
        self.search.connect("key-press-event", self.activate_search)
	self.window.add(mainbox)

    #load apps
    def load(self, id_category):
        self.buttonContainer_size_w = self.buttonsContainer.get_allocation().width
        self.buttonContainer_size_h = self.buttonsContainer.get_allocation().height
        if self.buttonsContainer.get_children():
           for widget in self.buttonsContainer.get_children():
              self.buttonsContainer.remove(widget)
           self.buttonsContainer.set_size_request(self.buttonContainer_size_w, self.buttonContainer_size_h) 
        apps = self.getApps(id_category)
        self.fill_buttonsContainer(apps)   
        self.buttonsContainer.show_all()

    def activate_search(self, widget=None, event=None, data=None):
       if not self.search.get_editable():
          self.search.set_text("")
          self.search.set_editable(True)

    def add_toolbar(self, widget, categories, launcher):

        # create toolbar
        toolbar = gtk.HBox()
        toolbar.set_border_width(5)
        
        # Add Categories as buttons
        button = gtk.Button("All")
        button.set_relief(gtk.RELIEF_NONE)
        button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        button.child.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        button.set_focus_on_click(False)
        button.set_border_width(0)
        button.set_property('can-focus', False)
        button.connect("clicked", self.activate_category, "ALL")
        toolbar.pack_start(button, False, False, 5)
        for category in categories:
           button = gtk.Button(category['label'])
           button.set_relief(gtk.RELIEF_NONE)
           button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
           button.child.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
           button.set_focus_on_click(False)
           button.set_border_width(0)
           button.set_property('can-focus', False)
           button.connect("clicked", self.activate_category, category['id'])
           toolbar.pack_start(button, False, False, 5)
        # Add search box
        self.search = gtk.Entry()
        self.search.set_editable(False)
        self.search.set_text("Start tipping...")
        toolbar.pack_end(self.search, False, False, 5)
        # Add toolbar to widget
        widget.pack_start(toolbar, False , False, 5)
    
    # closing the window from the WM
    def destroy(self, widget=None, event=None):
        gtk.main_quit()
        return False
    #Calculate max columns 
    def calculate_maxcolums(self):   
	maxcolums = (gtk.gdk.screen_width() / (ICON_SIZE + COL_PADDING*2 + BUTTON_PADDING*2+CONTAINER_PADDING*2))
	return maxcolums
    #Calculate max row
    def calculate_maxrows(self):   
	maxrows = (gtk.gdk.screen_height() / (ICON_SIZE*2 + ROW_PADDING*2 + BUTTON_PADDING*2))
	return maxrows
    # Get icon
    def get_icon(self, icon_name):
        try:
           theme = gtk.icon_theme_get_default()
           pixbuf = theme.load_icon(icon_name, ICON_SIZE, 0)
           return gtk.image_new_from_pixbuf(pixbuf)
        except:
           return gtk.image_new_from_file (icon_name)

    def paginate(self, lista):
        nPages = (len(lista) / (self.maxcolums * self.maxrows)) + 1
        #print "pages: " + str(nPages)
        paginationbox = gtk.HBox()
        footer = gtk.HBox()
        for i in range(1,nPages+1):
                  button = gtk.Button(str(i))
                  button.set_relief(gtk.RELIEF_NONE)
                  button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
                  button.child.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
                  button.set_focus_on_click(False)
                  button.set_border_width(0)
                  button.set_property('can-focus', False)
                  button.connect("clicked", self.navigate_page, lista, i)
                  paginationbox.pack_start(button, False , False, 5)
        footer.pack_start(gtk.HBox())
        footer.pack_start(paginationbox, False , False, 5)
        footer.pack_start(gtk.HBox())
        self.buttonsContainer.pack_end(footer, False , False, 5)

    def fill_buttonsContainer(self, lista, Page=1):
        self.paginate(lista)
	
        row_widget = self.new_row(self.buttonsContainer)
        iconCounter=0
	rowCounter=0

        for item in lista[(self.maxrows*self.maxcolums)*(Page-1):(self.maxrows*self.maxcolums)*(Page)]:
               if (iconCounter)%self.maxcolums == 0:
                  #if (rowCounter+1) > maxrows:
                     #break
                  rowCounter+=1
                  row_widget = self.new_row(self.buttonsContainer)
               iconCounter+=1
               self.add_button(item, row_widget)

    def new_row(self, widget):
        row=gtk.HBox(False)
        widget.pack_start(row, False, False, ROW_PADDING)
        return row

    def add_button(self, item, row):
        """ Add a button to the panel """
        box = gtk.VBox(False)

        image = gtk.Image()
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        button.set_focus_on_click(False)
        button.set_border_width(0)
        button.set_property('can-focus', False)
        icon_name = item['icon']
        icon = self.get_icon(icon_name)
        button.add(icon)
        button.set_size_request(ICON_SIZE+BUTTON_PADDING, ICON_SIZE+BUTTON_PADDING)
        button.show()
        box.pack_start(button, False, False, BUTTON_PADDING)
        button.connect("clicked", self.click_button, item['command'])
	labelString = item['label']
        ## label to big
	if len(item['label']) > 15:
            if len(item['command']) < 15:
               labelString = item['command'].replace('-', ' ').capitalize()
        if len(labelString) * self.fontsize > ICON_SIZE+BUTTON_PADDING*2:
            labelString = item['label'][0:((ICON_SIZE+BUTTON_PADDING*2) / self.fontsize)-3]+"..."
        label = gtk.Label(labelString)
        label.set_tooltip_text(item['label'])
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        #if len(labelString) > 12:
           #label.set_line_wrap(True)
        label.set_justify(gtk.JUSTIFY_CENTER)
        
        box.set_size_request(ICON_SIZE+BUTTON_PADDING*2, ICON_SIZE*2)
        box.pack_end(label, False, True)
	
        row.pack_start(box, False, False, COL_PADDING)

    def click_button(self, widget, command):
        self.destroy()
        self.run_command(command)

    def activate_category(self, widget, category_id):
        self.load(category_id)

    def navigate_page(self, widget, apps, page):
        self.buttonContainer_size_w = self.buttonsContainer.get_allocation().width
        self.buttonContainer_size_h = self.buttonsContainer.get_allocation().height
        if self.buttonsContainer.get_children():
           for widget in self.buttonsContainer.get_children():
              self.buttonsContainer.remove(widget)
           self.buttonsContainer.set_size_request(self.buttonContainer_size_w, self.buttonContainer_size_h) 
        self.fill_buttonsContainer(apps, Page=page)   
        self.buttonsContainer.show_all()
        
    def run_command(self, command):
         print "%s pressed" %command
         os.system(command + ' &')

## xpath tutorial:
## http://www.w3schools.com/xpath/xpath_syntax.asp

    def getApps(self, Category="ALL", Page=1):
       root = etree.parse(self.appsmenu)
       apps = []
       if Category == "ALL": 
          for item in root.xpath("/xdg-menu/menu[@id]/item"):
             apps.append({'label': item.attrib["label"], 'icon': item.attrib["icon"], 'command': item.find(".//command").text})
       else:
          for item in root.xpath("/xdg-menu/menu[@id='"+Category+"']/item"):
             apps.append({'label': item.attrib["label"], 'icon': item.attrib["icon"], 'command': item.find(".//command").text})
       return apps

    def getCategories(self):
       root = etree.parse(self.appsmenu)
       categories = []
       for item in root.xpath("/xdg-menu/menu[@id]"):
          categories.append({'id': item.attrib["id"], 'label': item.attrib["label"]})
       return categories
    


class MyLauncher:
    def __init__(self):
        # Start logger
        self.logger = logging.getLogger(self.__class__.__name__)
        # bgcolor and opacity
        self.opacity = OPACITY
        self.bgcolor = gtk.gdk.color_parse("black")
        self.init_window()

    def quit(self, widget=None, data=None):
        gtk.main_quit()

    def on_keypress(self, widget=None, event=None, data=None):
        #print("Keypress: %s/%s" % (event.keyval, gtk.gdk.keyval_name(event.keyval)))
        if gtk.gdk.keyval_name(event.keyval) == "Escape":
            self.quit()
            

    def on_window_state_change(self, widget, event, *args):
        if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.window_in_fullscreen = True
        else:
            self.window_in_fullscreen = False
    def on_screen_changed(self, widget, old_screen=None):

        # To check if the display supports alpha channels, get the colormap
        screen = widget.get_screen()
        self.colormap = screen.get_rgba_colormap()
        if self.colormap == None:
            self.logger.debug("Screen does not support alpha channels!")
            colormap = screen.get_rgb_colormap()
            self.supports_alpha = False
        else:
            self.logger.debug("Screen supports alpha channels!")
            self.supports_alpha = True

        # Now we have a colormap appropriate for the screen, use it
        widget.set_colormap(self.colormap)

    def on_expose(self, widget, event):

        cr = widget.window.cairo_create()

        if self.supports_alpha == True:
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.0) # Transparent
        else:
            cr.set_source_rgb(1.0, 1.0, 1.0) # Opaque white

        # Draw the background
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        #(width, height) = widget.get_size()
        cr.set_source_rgba(self.bgcolor.red, self.bgcolor.green, self.bgcolor.blue, float(self.opacity)/100)


        cr.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        cr.fill()
        cr.stroke()
        return False

    def init_window(self):
         # Start pyGTK setup
        self.window = gtk.Window()
        self.window.set_title("MyLaunchpad")

        self.window.connect("destroy", self.quit)
        self.window.connect("key-press-event", self.on_keypress)
        self.window.connect("window-state-event", self.on_window_state_change)

        if not self.window.is_composited():
            self.logger.debug("No compositing, enabling rendered effects")
            # Window isn't composited, enable rendered effects
            self.rendered_effects = True
        else:
            # Link in Cairo rendering events
            #self.window.connect("delete_event", self.delete_event)
            self.window.connect('expose-event', self.on_expose)
            self.window.connect('screen-changed', self.on_screen_changed)
            self.on_screen_changed(self.window)
            self.rendered_effects = False
        print "Compositing %s" %self.window.is_composited()

        self.window.set_size_request(620,200)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))

        self.window.set_decorated(False)
        self.window.set_position(gtk.WIN_POS_CENTER)

	mainbox = gtk.VBox(False, 0);
	
	apps = AppStore(mainbox, self)

        if self.rendered_effects == True:
            self.logger.debug("Stepping though render path")
            w = gtk.gdk.get_default_root_window()
            sz = w.get_size()
            pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
            pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])

            self.logger.debug("Rendering Fade")
            # Convert Pixbuf to PIL Image
            wh = (pb.get_width(),pb.get_height())
            pilimg = Image.fromstring("RGB", wh, pb.get_pixels())

            pilimg = pilimg.point(lambda p: (p * self.opacity) / 255 )

            # "Convert" the PIL to Pixbuf via PixbufLoader
            buf = StringIO.StringIO()
            pilimg.save(buf, "ppm")
            del pilimg
            loader = gtk.gdk.PixbufLoader("pnm")
            loader.write(buf.getvalue())
            pixbuf = loader.get_pixbuf()

            # Cleanup IO
            buf.close()
            loader.close()

            pixmap, mask = pixbuf.render_pixmap_and_mask()
            # width, height = pixmap.get_size()
        else:
            pixmap = None

        self.window.set_app_paintable(True)
        self.window.resize(gtk.gdk.screen_width(), gtk.gdk.screen_height())
        self.window.realize()

        if pixmap:
            self.window.window.set_back_pixmap(pixmap, False)
        self.window.move(0,0)

    def run_launcher(self):
        self.window.show_all()
        gtk.main()

launcher = MyLauncher()
launcher.run_launcher()
