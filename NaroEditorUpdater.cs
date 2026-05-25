// NaroEditorUpdater.cs  —  .NET Framework 4.x WinForms updater
// Compiled with:
//   csc.exe /target:winexe /optimize+ /reference:System.Windows.Forms.dll
//           /reference:System.Drawing.dll /win32icon:NaroEditor.ico
//           /out:dist\NaroEditorUpdater.exe NaroEditorUpdater.cs
//
// Usage (invoked by NaroEditor.exe):
//   NaroEditorUpdater.exe --pid <pid> --source <tmp_path> --target <target_path> --version <ver>
//
// The calling process (NaroEditor) has already downloaded the new EXE to
// <tmp_path>. This program waits for <pid> to exit, then replaces
// <target_path> with <tmp_path> and launches the updated NaroEditor.

using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("NaroEditorUpdater")]
[assembly: System.Reflection.AssemblyDescription("NaroEditor automatic updater")]
[assembly: System.Reflection.AssemblyProduct("NaroEditor")]
[assembly: System.Reflection.AssemblyVersion("1.0.0.0")]

namespace NaroEditorUpdater
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            string pid = "0", source = "", target = "", version = "unknown";
            for (int i = 0; i + 1 < args.Length; i += 2)
            {
                switch (args[i])
                {
                    case "--pid":     pid     = args[i + 1]; break;
                    case "--source":  source  = args[i + 1]; break;
                    case "--target":  target  = args[i + 1]; break;
                    case "--version": version = args[i + 1]; break;
                }
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            int pidInt = 0;
            int.TryParse(pid, out pidInt);

            if (source == "" || target == "" || pidInt == 0)
            {
                MessageBox.Show(
                    "引数が不足しています。",
                    "NaroEditorUpdater",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
                return;
            }

            Application.Run(new UpdaterForm(pidInt, source, target, version));
        }
    }

    sealed class UpdaterForm : Form
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern IntPtr OpenProcess(
            uint dwDesiredAccess,
            [MarshalAs(UnmanagedType.Bool)] bool bInheritHandle,
            int dwProcessId);

        [DllImport("kernel32.dll")]
        static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

        [DllImport("kernel32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool CloseHandle(IntPtr hObject);

        private const uint SYNCHRONIZE  = 0x00100000;
        private const uint WAIT_TIMEOUT = 0x00000102;

        private readonly Label       _label;
        private readonly ProgressBar _bar;
        private readonly int    _pid;
        private readonly string _source, _target, _version;
        private readonly string _logPath;

        public UpdaterForm(int pid, string source, string target, string version)
        {
            _pid = pid; _source = source; _target = target; _version = version;
            _logPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "NaroEditor", "updater.log");

            Text            = "NaroEditor アップデート";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox     = false;
            MinimizeBox     = false;
            ControlBox      = false;
            ClientSize      = new System.Drawing.Size(440, 90);
            StartPosition   = FormStartPosition.CenterScreen;
            TopMost         = true;

            _label = new Label
            {
                AutoSize = false,
                Bounds   = new System.Drawing.Rectangle(20, 14, 400, 20),
                Text     = "NaroEditor の終了を待っています…",
            };
            _bar = new ProgressBar
            {
                Bounds                = new System.Drawing.Rectangle(20, 44, 400, 22),
                Style                 = ProgressBarStyle.Marquee,
                MarqueeAnimationSpeed = 30,
            };
            Controls.Add(_label);
            Controls.Add(_bar);

            Load += (s, e) => new Thread(Worker) { IsBackground = true }.Start();
        }

        void Log(string msg)
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(_logPath));
                File.AppendAllText(
                    _logPath,
                    string.Format("[{0}] {1}\r\n", DateTime.Now.ToString("HH:mm:ss.fff"), msg),
                    System.Text.Encoding.UTF8);
            }
            catch { }
        }

        void SetStatus(string text, int progress)
        {
            if (InvokeRequired)
            {
                BeginInvoke((Action<string, int>)SetStatus, text, progress);
                return;
            }
            _label.Text = text;
            if (progress >= 0)
            {
                _bar.Style = ProgressBarStyle.Continuous;
                _bar.Value = Math.Min(Math.Max(progress, 0), 100);
            }
        }

        void Worker()
        {
            try
            {
                Log("=== NaroEditorUpdater started, PID=" + Process.GetCurrentProcess().Id
                    + ", target=" + _target);

                // 1. Wait for NaroEditor to exit
                Log("Waiting for PID=" + _pid + " to exit...");
                IntPtr h = OpenProcess(SYNCHRONIZE, false, _pid);
                if (h != IntPtr.Zero)
                {
                    uint waitResult = WaitForSingleObject(h, 30000);
                    CloseHandle(h);
                    if (waitResult == WAIT_TIMEOUT)
                        Log("WaitForSingleObject timed out for PID=" + _pid
                            + ". Proceeding with file replacement.");
                }
                else
                {
                    Log("OpenProcess failed for PID=" + _pid
                        + ", Win32Error=" + Marshal.GetLastWin32Error()
                        + ". Falling back to sleep.");
                    Thread.Sleep(2000);
                }
                Log("PID=" + _pid + " wait complete.");

                SetStatus(string.Format("NaroEditor v{0} を適用中…", _version), 50);
                Thread.Sleep(300);

                // 2. Replace target with downloaded file (retry for file locks)
                Log("Replacing: " + _source + " -> " + _target);
                string backup = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "NaroEditor", "NaroEditor.exe.bak");
                for (int i = 0; i < 5; i++)
                {
                    try
                    {
                        if (File.Exists(_target))
                        {
                            File.Replace(_source, _target, backup, true);
                            try { if (File.Exists(backup)) File.Delete(backup); }
                            catch (Exception bex) { Log("Backup cleanup failed: " + bex.Message); }
                        }
                        else
                        {
                            File.Move(_source, _target);
                        }
                        Log("File replaced successfully on attempt " + (i + 1) + ".");
                        break;
                    }
                    catch (IOException ex)
                    {
                        Log("Replace attempt " + (i + 1) + " failed: " + ex.Message);
                        if (i == 4) throw;
                        Thread.Sleep(2000);
                    }
                }

                // 3. Update complete — prompt manual restart
                Log("Update complete. Prompting user to start manually.");
                BeginInvoke((Action)(() =>
                {
                    SetStatus("アップデート完了", 100);
                    MessageBox.Show(
                        string.Format("NaroEditor v{0} へのアップデートが完了しました。\n\n", _version) +
                        "NaroEditor.exe を起動してください。",
                        "NaroEditor アップデート完了",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Information);
                    Close();
                }));
            }
            catch (Exception ex)
            {
                Log("EXCEPTION: " + ex.GetType().Name + ": " + ex.Message
                    + "\r\n" + ex.StackTrace);
                SetStatus(string.Format("エラー: {0}  (8秒後に自動的に閉じます)", ex.Message), 0);
                try { if (File.Exists(_source)) File.Delete(_source); } catch { }
                Thread.Sleep(8000);
                BeginInvoke((Action)Close);
            }
        }
    }
}
