# -*- coding: ISO-8859-1 -*-
#
# generated by wxGlade 0.9.3 on Fri Jun 28 16:25:14 2019
#

import wx
# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class Controller(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: Controller.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.SetSize((660, 300))
        self.bitmap_button_12 = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap("icons/icons8-connected-50.png", wx.BITMAP_TYPE_ANY))
        self.text_byte_0 = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_byte_1 = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_byte_2 = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_byte_3 = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_byte_4 = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_byte_5 = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_desc = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_packet_sent = wx.TextCtrl(self, wx.ID_ANY, "")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade
        self.project = None

    def set_project(self, project):
        self.project = project
        self.project.controller.status_listener = self.update_status
        self.project.controller.packet_listener = self.update_packet

    def update_status(self, data):
        try:
            if isinstance(data, int):
                self.text_desc.SetValue(str(data))
            elif len(data) == 6:
                self.text_byte_0.SetValue(str(data[0]))
                self.text_byte_1.SetValue(str(data[1]))
                self.text_byte_2.SetValue(str(data[2]))
                self.text_byte_3.SetValue(str(data[3]))
                self.text_byte_4.SetValue(str(data[4]))
                self.text_byte_5.SetValue(str(data[5]))
            else:
                self.text_desc.SetValue(str(data))
            self.Update()
        except RuntimeError:
            pass

    def update_packet(self, data):
        try:
            self.text_packet_sent.SetValue(str(data))
            self.Update()
        except RuntimeError:
            pass

    def __set_properties(self):
        # begin wxGlade: Controller.__set_properties
        self.SetTitle("Controller")
        _icon = wx.NullIcon
        _icon.CopyFromBitmap(wx.Bitmap("icons/icons8-usb-connector-50.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.bitmap_button_12.SetBitmapDisabled(wx.Bitmap("icons/icons8-disconnected-50.png", wx.BITMAP_TYPE_ANY))
        self.bitmap_button_12.SetSize(self.bitmap_button_12.GetBestSize())
        self.text_byte_0.Enable(False)
        self.text_byte_1.Enable(False)
        self.text_byte_2.Enable(False)
        self.text_byte_3.Enable(False)
        self.text_byte_4.Enable(False)
        self.text_byte_5.Enable(False)
        self.text_desc.Enable(False)
        self.text_packet_sent.SetMinSize((660, 23))
        self.text_packet_sent.Enable(False)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: Controller.__do_layout
        sizer_11 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2 = wx.FlexGridSizer(3, 6, 0, 0)
        sizer_12 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_12.Add(self.bitmap_button_12, 0, 0, 0)
        sizer_11.Add(sizer_12, 1, wx.EXPAND, 0)
        label_byte_0 = wx.StaticText(self, wx.ID_ANY, "byte_0")
        grid_sizer_2.Add(label_byte_0, 0, 0, 0)
        label_byte_1 = wx.StaticText(self, wx.ID_ANY, "byte_1")
        grid_sizer_2.Add(label_byte_1, 0, 0, 0)
        label_byte_2 = wx.StaticText(self, wx.ID_ANY, "byte_2")
        grid_sizer_2.Add(label_byte_2, 0, 0, 0)
        label_byte_3 = wx.StaticText(self, wx.ID_ANY, "byte_3")
        grid_sizer_2.Add(label_byte_3, 0, 0, 0)
        label_byte_4 = wx.StaticText(self, wx.ID_ANY, "byte_4")
        grid_sizer_2.Add(label_byte_4, 0, 0, 0)
        label_byte_5 = wx.StaticText(self, wx.ID_ANY, "byte_5")
        grid_sizer_2.Add(label_byte_5, 0, 0, 0)
        grid_sizer_2.Add(self.text_byte_0, 0, 0, 0)
        grid_sizer_2.Add(self.text_byte_1, 0, 0, 0)
        grid_sizer_2.Add(self.text_byte_2, 0, 0, 0)
        grid_sizer_2.Add(self.text_byte_3, 0, 0, 0)
        grid_sizer_2.Add(self.text_byte_4, 0, 0, 0)
        grid_sizer_2.Add(self.text_byte_5, 0, 0, 0)
        grid_sizer_2.Add((0, 0), 0, 0, 0)
        grid_sizer_2.Add(self.text_desc, 0, 0, 0)
        grid_sizer_2.Add((0, 0), 0, 0, 0)
        grid_sizer_2.Add((0, 0), 0, 0, 0)
        grid_sizer_2.Add((0, 0), 0, 0, 0)
        grid_sizer_2.Add((0, 0), 0, 0, 0)
        sizer_11.Add(grid_sizer_2, 1, wx.EXPAND, 0)
        sizer_11.Add(self.text_packet_sent, 0, wx.ALIGN_BOTTOM | wx.EXPAND, 0)
        self.SetSizer(sizer_11)
        self.Layout()
        # end wxGlade

# end of class Controller