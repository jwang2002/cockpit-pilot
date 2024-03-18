import wx
import threading
import queue
import subprocess

MAIN_SIZE = (400,250)
DIALOG_SIZE = (600,120)
COUNTDOWN = 5

class CockpitPilotApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None, title="Cockpit Pilot", size=(400, 180))
        self.frame.Show()
        return True

class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MainFrame, self).__init__(*args, **kw)
        
        self.config_path = "C:/Users/boris/anaconda3/Lib/site-packages/cockpit/pilot/device_config.py"
        self.output_queue = queue.Queue()
        
        self.InitUI()
        self.SetSize(MAIN_SIZE)
        self.Centre()
        
    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        welcome_label = wx.StaticText(panel, label="\n Welcome to Cockpit! \n", style=wx.ALIGN_CENTER)
        welcome_label.SetFont(my_font(18))
        vbox.Add(welcome_label, flag=wx.ALL | wx.EXPAND, border=10)
        
        info_label = wx.StaticText(panel, label=" Get ready to explore the microscopic world! \n", style=wx.ALIGN_CENTER)
        info_label.SetFont(my_font())
        vbox.Add(info_label, flag=wx.ALL | wx.EXPAND, border=10)
        
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        config_button = wx.Button(panel, label=" Change Config Path... ")
        config_button.Bind(wx.EVT_BUTTON, self.OnChangeConfigPath)
        button_sizer.Add(config_button, flag=wx.RIGHT, border=10)
        
        launch_button = wx.Button(panel, label=" Launch Cockpit ")
        launch_button.Bind(wx.EVT_BUTTON, self.OnPrepareCockpit)
        button_sizer.Add(launch_button)
        
        vbox.Add(button_sizer, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)

    def OnChangeConfigPath(self, event):
        dialog = DialogFrame(self, "Config Path Dialog", size=DIALOG_SIZE)
        dialog.Show()

    def OnPrepareCockpit(self, event):
        self.Hide()
        self.OpenOutputWindow()
        threading.Thread(target=self.LaunchDeviceServer, daemon=True).start()
        countdown_frame = CountdownFrame(self, "Countdown", COUNTDOWN, self)  # Pass 'self' to CountdownFrame
        countdown_frame.Show(True)

    def OpenOutputWindow(self):
        self.output_window = OutputWindow(self, "Device Server Output")
        self.PollOutputQueue()

    def PollOutputQueue(self):
        try:
            while not self.output_queue.empty():
                line = self.output_queue.get_nowait()
                if line:
                    wx.CallAfter(self.output_window.AppendText, line)
        except queue.Empty:
            pass
        finally:
            # Keep polling
            if self.output_window:
                # Re-run the polling method to continuously check for new output
                wx.CallLater(100, self.PollOutputQueue)

    def LaunchDeviceServer(self):
        command = f"python -m microscope.device_server {self.config_path}"
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in iter(proc.stdout.readline, ''):
            self.output_queue.put(line)
        proc.stdout.close()
        proc.wait() 

class DialogFrame(wx.Frame):
    def __init__(self, parent, title, size):
        super(DialogFrame, self).__init__(parent, title=title, size=size)
        
        self.parent = parent
        self.InitUI()
        self.Centre()
        
    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, label="Enter Device Config Path: ")
        hbox.Add(label, flag=wx.RIGHT, border=8)
        
        self.txtCtrl = wx.TextCtrl(panel, value=self.parent.config_path)
        hbox.Add(self.txtCtrl, proportion=1)
        
        vbox.Add(hbox, flag=wx.EXPAND | wx.ALL, border=10)
        
        # Create OK and Cancel buttons
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        okBtn = wx.Button(panel, wx.ID_OK, "OK")
        cancelBtn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btnSizer.Add(okBtn)
        btnSizer.Add(cancelBtn, flag=wx.LEFT, border=5)
        
        vbox.Add(btnSizer, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        panel.SetSizer(vbox)
        
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

    def OnOk(self, event):
        _config_path = self.txtCtrl.GetValue()
        self.parent.config_path = _config_path
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()

class OutputWindow(wx.Frame):
    def __init__(self, parent, title):
        super(OutputWindow, self).__init__(parent, title=title, size=(500, 300))
        self.InitUI()
        self.Centre()
        self.Show()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.outputTxtCtrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.outputTxtCtrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        
        panel.SetSizer(vbox)

    def AppendText(self, text):
        self.outputTxtCtrl.AppendText(text)

    def OnClose(self, event):
        # This method is called when the window is closed.
        # TERMINATE the entire application.
        self.Destroy()  # Ensure the output window is closed properly.
        wx.CallAfter(wx.GetApp().ExitMainLoop)

class CountdownFrame(wx.Frame):
    def __init__(self, parent, title, countdown_duration, main_frame_ref):
        super(CountdownFrame, self).__init__(parent, title=title, size=(400, 180))
        self.main_frame_ref = main_frame_ref  # Store the reference to MainFrame
        self.countdown_duration = countdown_duration
        self.InitUI()
        self.Centre()
        self.StartCountdown()

    def InitUI(self):
        self.panel = wx.Panel(self)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.UpdateCountdown, self.timer)

        self.countdown_label = wx.StaticText(self.panel, label="", pos=(50, 50))
        font = wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.countdown_label.SetFont(font)

    def StartCountdown(self):
        self.UpdateCountdown(None)
        self.timer.Start(1000)

    def UpdateCountdown(self, event):
        if self.countdown_duration > 0:
            self.countdown_label.SetLabel(f"Starting in {self.countdown_duration} seconds...")
            self.countdown_duration -= 1
        else:
            self.timer.Stop()
            self.Close(True)
            wx.CallAfter(self.LaunchCockpitMain)

    def LaunchCockpitMain(self):
        threading.Thread(target=self.cockpit_main, daemon=True).start()
        
    def cockpit_main(self):
        command = f"python -m cockpit"
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        for line in iter(proc.stdout.readline, ''):
            wx.CallAfter(self.main_frame_ref.output_window.AppendText, line)
        
        proc.stdout.close()
        proc.wait()
        if proc.returncode != 0:
            wx.CallAfter(wx.MessageBox, "Cockpit exited with an error.", "Error", wx.OK | wx.ICON_ERROR)

def my_font(size=10):
    '''             Example of USE: 

    text = wx.StaticText(panel, -1, 'my text', (20, 100))
    font = wx.Font(18, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)
    text.SetFont(font)
    wx.Font has the following signature:
        x.Font(pointSize, family, style, weight, underline=False, faceName="", encoding=wx.FONTENCODING_DEFAULT)
        1: family can be:

            wx.DECORATIVE, wx.DEFAULT,wx.MODERN, wx.ROMAN, wx.SCRIPT or wx.SWISS.

        2: style can be:

            wx.NORMAL, wx.SLANT or wx.ITALIC.

        3: weight can be:

            wx.NORMAL, wx.LIGHT, or wx.BOLD
    '''
    return wx.Font(size, family=wx.DECORATIVE, style=wx.NORMAL, weight=wx.BOLD)

if __name__ == "__main__":
    app = CockpitPilotApp(False)
    app.MainLoop()