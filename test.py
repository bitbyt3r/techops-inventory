import win32ui
import win32print
import win32con

INCH = 1440

hDC = win32ui.CreateDC ()
hDC.CreatePrinterDC (win32print.GetDefaultPrinter ())
hDC.StartDoc ("Test doc")
hDC.StartPage ()
hDC.SetMapMode (win32con.MM_TWIPS)
hDC.DrawText ("TEST", (0, INCH * -1, INCH * 2, INCH * -2), win32con.DT_CENTER)
hDC.EndPage ()
hDC.EndDoc ()