#!/usr/bin/python3
import sys
import time
import os
import platform
import wx
import threading

PRINT_EVENT_TYPE = wx.NewEventType()
PRINT_EVENT = wx.PyEventBinder(PRINT_EVENT_TYPE, 1)
class PrintEvent(wx.PyCommandEvent):
    def __init__(self, value=None):
        wx.PyCommandEvent.__init__(self, PRINT_EVENT_TYPE, -1)
        self._value = value

    def GetValue(self):
        return self._value

class AppFrame(wx.Frame):
    def __init__(self, parent, id, title="Printer Daemon"):
        wx.Frame.__init__(self, parent, id, title, size=(600, 350), style=wx.DEFAULT_FRAME_STYLE)

        self.CenterOnScreen()

        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+X")
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.OnClose, id=wx.ID_EXIT)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.Bind(PRINT_EVENT, self.print_received)

    def print_received(self, event):
        print(event)
        print("Received print job for {}".format(event.GetValue()))

    def OnBtnPrint(self, event):
        text = self.tc.GetValue()

        #------------

        pd = wx.PrintData()

        pd.SetPrinterName("")
        pd.SetOrientation(wx.PORTRAIT)
        pd.SetPaperId(wx.PAPER_A4)
        pd.SetQuality(wx.PRINT_QUALITY_DRAFT)
        # Black and white printing if False.
        pd.SetColour(True)
        pd.SetNoCopies(1)
        pd.SetCollate(True)

        #------------

        pdd = wx.PrintDialogData()

        pdd.SetPrintData(pd)
        pdd.SetMinPage(1)
        pdd.SetMaxPage(1)
        pdd.SetFromPage(1)
        pdd.SetToPage(1)
        pdd.SetPrintToFile(False)
        # pdd.SetSetupDialog(False)
        # pdd.EnableSelection(True)
        # pdd.EnablePrintToFile(True)
        # pdd.EnablePageNumbers(True)
        # pdd.SetAllPages(True)

        #------------

        dlg = wx.PrintDialog(self, pdd)

        if dlg.ShowModal() == wx.ID_OK:
            dc = dlg.GetPrintDC()

            dc.StartDoc("My document title")
            dc.StartPage()

            # (wx.MM_METRIC) ---> Each logical unit is 1 mm.
            # (wx.MM_POINTS) ---> Each logical unit is a "printer point" i.e.
            dc.SetMapMode(wx.MM_METRIC)

            dc.SetTextForeground("red")
            dc.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
            dc.DrawText(text, 50, 100)

            dc.EndPage()
            dc.EndDoc()
            del dc

        else :
            dlg.Destroy()

    def OnClose(self, event):
        self.Close(True)

    def OnExit(self, event):
        self.Destroy()

class App(wx.App):
    def OnInit(self):
        frame = AppFrame(None, id=-1)
        self.SetTopWindow(frame)
        frame.Show(True)

        return True

class DBThread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self._parent = parent
    
    def run(self):
        while True:
            evt = PRINT_EVENT("Hello World")
            wx.PostEvent(self._parent, evt)
            time.sleep(10)

def main():
    app = App(False)
    dbThread = DBThread(1)
    dbThread.start()
    app.MainLoop()

if __name__ == "__main__" :
    main()