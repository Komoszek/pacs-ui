#! /usr/bin/env python

import gi
import subprocess
import re

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class NewSinkDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title="New Sink", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(150, 200)

        box = self.get_content_area()

        print(box.get_homogeneous())

        box.set_margin_start(7)
        box.set_margin_end(7)
        box.set_margin_top(7)
        box.set_margin_bottom(7)

        self.description_set = set()

        self.name_set = set()

        self.buttonOK = self.get_widget_for_response(Gtk.ResponseType.OK)
        self.buttonOK.set_sensitive(False)

        name_label = Gtk.Label(label="Sink Name")
        name_label.set_xalign(0.0)

        box.add(name_label)

        self.name_entry = Gtk.Entry()
        self.name_entry.set_text("")
        self.name_entry.connect("changed", self.entry_changed)

        box.add(self.name_entry)

        description_label = Gtk.Label(label="Device description")
        description_label.set_xalign(0.0)

        description_label.set_margin_top(10)

        self.description_entry = Gtk.Entry()
        self.description_entry.set_text("")

        self.description_entry.set_margin_bottom(10)
        self.description_entry.connect("changed", self.entry_changed)

        box.add(description_label)
        box.add(self.description_entry)

        self.sinks_liststore = Gtk.ListStore(bool, str, str)
        self.refresh_sink_list()

        self.treeview = Gtk.TreeView(model=self.sinks_liststore)

        box.add(self.treeview)

        button_refresh_sinks = Gtk.Button(image=Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.SMALL_TOOLBAR) , label=" Refresh")
        button_refresh_sinks.connect("clicked", self.click_button_refresh)
        button_refresh_sinks.set_hexpand(False)
        box.pack_start(button_refresh_sinks, False, False, 0)

        button_refresh_sinks.set_margin_bottom(3)

        renderer_toggle = Gtk.CellRendererToggle()
        column = Gtk.TreeViewColumn("Toggle", renderer_toggle, active=0)

        renderer_toggle.connect("toggled", self.on_cell_toggled)

        self.treeview.append_column(column)

        for i, column_title in enumerate(
            [ "Description", "Sink Name"]
        ):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i+1)
            self.treeview.append_column(column)

        self.show_all()

    def refresh_sink_list(self):
        self.sinks_liststore.clear()
        for sink in self.SinkList():
            self.sinks_liststore.append([False, sink[1], sink[0]])

    def on_cell_toggled(self, widget, path):
        self.sinks_liststore[path][0] = not self.sinks_liststore[path][0]
        if self.sinks_liststore[path][0]:
            if self.sinks_liststore[path][2] not in self.name_set:
                self.description_set.add(self.sinks_liststore[path][1])
                self.name_set.add(self.sinks_liststore[path][2])
        else:
            if self.sinks_liststore[path][2] in self.name_set:
                self.description_set.remove(self.sinks_liststore[path][1])
                self.name_set.remove(self.sinks_liststore[path][2])

        self.description_entry.set_text(' + '.join(self.description_set))
        self.update_button_state()

    def SinkList(self):
        s = subprocess.getstatusoutput(f'pacmd list-sinks')

        if s[0] == 0:
            return re.findall(r'name: <([\w.,-]+)>[\s\S]*?device\.description = "([\S ]+?)"', s[1])
        return []

    def get_new_sink_data(self):
        return (self.name_entry.get_text(), self.description_entry.get_text(), self.name_set)

    def update_button_state(self):
        sink_name = self.name_entry.get_text()
        if len(self.name_set) < 1 or sink_name in self.name_set or not sink_name or not self.description_entry.get_text():
            self.buttonOK.set_sensitive(False)
        else:
            self.buttonOK.set_sensitive(True)

    def entry_changed(self, widget):
        self.update_button_state()

    def click_button_refresh(self, widget):
        self.refresh_sink_list()

class TreeViewFilterWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Combined Sinks Manager")
        self.set_border_width(10)

        self._build_context_menu()

        self.selected_sink = None

        # Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        # Creating the ListStore model
        self.combined_sinks_liststore = Gtk.ListStore(str, str, str)
        self.refresh_combined_sink_list()

        self.treeview = Gtk.TreeView.new_with_model(self.combined_sinks_liststore)
        for i, column_title in enumerate(
            ["ID", "Sink name", "Description"]
        ):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)

        self.buttons = list()
        button_new_sink = Gtk.Button(image=Gtk.Image.new_from_icon_name("list-add", Gtk.IconSize.SMALL_TOOLBAR),label=" New sink")
        button_new_sink.connect("clicked", self.click_button_new_sink)

        self.buttons.append(button_new_sink)

        button_refresh_sinks = Gtk.Button(image=Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.SMALL_TOOLBAR) , label=" Refresh")
        button_refresh_sinks.connect("clicked", self.click_button_refresh)

        self.buttons.append(button_refresh_sinks)

        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 4, 5)
        self.grid.attach_next_to(
            self.buttons[0], self.scrollable_treelist, Gtk.PositionType.BOTTOM, 1, 1
        )
        self.grid.attach(
            self.buttons[1], 3, 5, 1, 1
        )

        self.scrollable_treelist.add(self.treeview)
        self.treeview.connect("button_release_event", self.mouse_click)

        self.show_all()

    def _build_context_menu(self):
        self.cmenu = Gtk.Menu.new()

        self.edit_sink_item = Gtk.MenuItem.new_with_label('Edit')
        self.cmenu.append(self.edit_sink_item)

        self.remove_sink_item = Gtk.MenuItem.new_with_label('Remove')
        self.cmenu.append(self.remove_sink_item)
        self.remove_sink_item.connect('button-press-event', self.remove_sink)

        self.cmenu.show_all()

    def mouse_click(self, tv, event):
        if event.button == 3:
            selection = self.treeview.get_selection()
            (model, iter) = selection.get_selected()
            if iter:
                self.selected_sink = model[iter][0]

                if self.selected_sink:
                    self.cmenu.popup_at_pointer()
            else:
                self.selected_sink = None

    def click_button_new_sink(self, widget):
        dialog = NewSinkDialog(self)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            sink_data = dialog.get_new_sink_data()
            sink_descroption = sink_data[1].replace(" ", "\\ ")
            s = subprocess.getstatusoutput(f"pacmd load-module module-combine-sink sink_name={sink_data[0]} sink_properties=device.description=\"'{sink_descroption}'\" slaves={','.join(sink_data[2])} channels=2")
            if s[0] == 0:
                self.refresh_combined_sink_list()

        elif response == Gtk.ResponseType.CANCEL:
            print("The Cancel button was clicked")

        dialog.destroy()

    def click_button_refresh(self, widget):
        self.refresh_combined_sink_list()

    def CombinedSinkList(self):
        s = subprocess.getstatusoutput(f'pactl list short modules | grep module-combine-sink')

        if s[0] == 0:
            return re.findall(r'(\d+).*?sink_name=([\w.,-]+).*?device\.description=([\w.,-]+?|\'[\S ]+?\')', s[1])
        return []

    def refresh_combined_sink_list(self):
        self.combined_sinks_liststore.clear()
        for sink in self.CombinedSinkList():
            cleaned_sink = list(sink)
            cleaned_sink[2] = cleaned_sink[2].replace("\\ ", " ").lstrip("\\'").rstrip("\\'")

            self.combined_sinks_liststore.append(cleaned_sink)

    def remove_sink(self, tv, event):
        subprocess.getstatusoutput(f'pactl unload-module {self.selected_sink}')
        self.refresh_combined_sink_list()


win = TreeViewFilterWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
