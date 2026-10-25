using System;
using System.IO;
using System.Diagnostics;
using System.Windows.Forms;
using System.Runtime.InteropServices;

class Program {

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    struct SHELLEXECUTEINFO {
        public int cbSize;
        public uint fMask;
        public IntPtr hwnd;
        [MarshalAs(UnmanagedType.LPTStr)] public string lpVerb;
        [MarshalAs(UnmanagedType.LPTStr)] public string lpFile;
        [MarshalAs(UnmanagedType.LPTStr)] public string lpParameters;
        [MarshalAs(UnmanagedType.LPTStr)] public string lpDirectory;
        public int nShow;
        public IntPtr hInstApp;
        public IntPtr lpIDList;
        [MarshalAs(UnmanagedType.LPTStr)] public string lpClass;
        public IntPtr hkeyClass;
        public uint dwHotKey;
        public IntPtr hIconOrMonitor;
        public IntPtr hProcess;
    }

    [DllImport("shell32.dll", CharSet = CharSet.Auto)]
    static extern bool ShellExecuteEx(ref SHELLEXECUTEINFO lpExecInfo);

    [STAThread]
    static void Main(string[] args) {
        string dir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
        string script = Path.Combine(dir, "smartfix_app.py");

        if (!File.Exists(script)) {
            MessageBox.Show(
                "Cannot find smartfix_app.py in:\n" + dir,
                "SmartFix AI", MessageBoxButtons.OK, MessageBoxIcon.Error
            );
            return;
        }

        string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        string progFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);

        string[] candidates = {
            Path.Combine(dir, ".venv", "Scripts", "pythonw.exe"),
            Path.Combine(dir, ".venv", "Scripts", "python.exe"),
            Path.Combine(progFiles, "Python310", "pythonw.exe"),
            Path.Combine(progFiles, "Python311", "pythonw.exe"),
            Path.Combine(progFiles, "Python312", "pythonw.exe"),
            Path.Combine(localApp, "Programs", "Python", "Python311", "pythonw.exe"),
            Path.Combine(localApp, "Programs", "Python", "Python310", "pythonw.exe"),
            Path.Combine(localApp, "Programs", "Python", "Python312", "pythonw.exe"),
            "C:\\Python311\\pythonw.exe",
            "C:\\Python310\\pythonw.exe",
            Path.Combine(progFiles, "Python310", "python.exe"),
            Path.Combine(progFiles, "Python311", "python.exe"),
            Path.Combine(localApp, "Programs", "Python", "Python311", "python.exe"),
            Path.Combine(localApp, "Programs", "Python", "Python310", "python.exe"),
            "python.exe"
        };

        string pythonExe = null;
        foreach (string candidate in candidates) {
            try {
                if (File.Exists(candidate)) {
                    pythonExe = candidate;
                    break;
                }
            } catch {}
        }

        if (pythonExe == null) {
            string[] pathDirs = (Environment.GetEnvironmentVariable("PATH") ?? "").Split(';');
            foreach (string d in pathDirs) {
                string fw = Path.Combine(d.Trim(), "pythonw.exe");
                string fp = Path.Combine(d.Trim(), "python.exe");
                if (File.Exists(fw)) { pythonExe = fw; break; }
                if (File.Exists(fp)) { pythonExe = fp; break; }
            }
        }

        if (pythonExe == null) {
            MessageBox.Show(
                "Python not found.\n\nPlease run SmartFix_Setup.exe to install all dependencies.",
                "SmartFix AI", MessageBoxButtons.OK, MessageBoxIcon.Error
            );
            return;
        }

        bool isBackground = false;
        string extraArgs = "";
        if (args != null && args.Length > 0) {
            foreach (string a in args) {
                if (a.Equals("--background", StringComparison.OrdinalIgnoreCase) ||
                    a.Equals("--minimized", StringComparison.OrdinalIgnoreCase) ||
                    a.Equals("--tray", StringComparison.OrdinalIgnoreCase) ||
                    a.Equals("--autostart", StringComparison.OrdinalIgnoreCase)) {
                    isBackground = true;
                }
            }
            extraArgs = " " + string.Join(" ", args);
        }

        try {
            string fullParams = "\"" + script + "\"" + extraArgs;
            var info = new SHELLEXECUTEINFO();
            info.cbSize = Marshal.SizeOf(info);
            info.fMask = 0x00000040; // SEE_MASK_NOCLOSEPROCESS
            info.lpFile = pythonExe;
            info.lpParameters = fullParams;
            info.lpDirectory = dir;
            info.nShow = isBackground ? 0 : 1; // 0 = SW_HIDE, 1 = SW_SHOWNORMAL
            info.lpVerb = "";
            bool ok = ShellExecuteEx(ref info);
            if (!ok) {
                int err = Marshal.GetLastWin32Error();
                MessageBox.Show("ShellExecuteEx failed. Error code: " + err + "\nPython: " + pythonExe,
                    "SmartFix AI", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        } catch (Exception ex) {
            MessageBox.Show("Error launching SmartFix AI:\n" + ex.Message,
                "SmartFix AI", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
