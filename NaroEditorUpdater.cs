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

            if (source == "" || target == "")
            {
                MessageBox.Show(
                    "引数が不足しています。",
                    "NaroEditorUpdater",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
                return;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            int pidInt = 0;
            int.TryParse(pid, out pidInt);
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

        private const uint SYNCHRONIZE = 0x00100000;

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
                Log("_MEIPASS2 at startup: "
                    + (Environment.GetEnvironmentVariable("_MEIPASS2") ?? "(not set)"));

                // 1. Wait for NaroEditor to fully exit
                if (_pid > 0)
                {
                    Log("Waiting for PID=" + _pid + " to exit...");
                    IntPtr h = OpenProcess(SYNCHRONIZE, false, _pid);
                    if (h != IntPtr.Zero)
                    {
                        WaitForSingleObject(h, 30000);
                        CloseHandle(h);
                    }
                    else
                    {
                        Thread.Sleep(2000);
                    }
                    Log("PID=" + _pid + " has exited.");
                }

                SetStatus(string.Format("NaroEditor v{0} を適用中…", _version), 50);
                Thread.Sleep(300);

                // 2. Replace target with downloaded file (retry for file locks)
                Log("Replacing: " + _source + " -> " + _target);
                for (int i = 0; i < 5; i++)
                {
                    try
                    {
                        if (File.Exists(_target)) File.Delete(_target);
                        File.Move(_source, _target);
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

                SetStatus("再起動中…", 100);
                Thread.Sleep(500);

                // 3. Launch updated NaroEditor without PyInstaller env vars.
                //
                // Strategy: build an EXPLICIT environment dictionary for ProcessStartInfo
                // (triggering lpEnvironment != NULL in CreateProcess) and remove _MEIPASS2
                // from it.  Using lpEnvironment=NULL (inheritance) proved unreliable even
                // after SetEnvironmentVariable; an explicit dict is the only guaranteed way
                // to prevent the child from seeing _MEIPASS2.
                Log("_MEIPASS2 before launch: "
                    + (Environment.GetEnvironmentVariable("_MEIPASS2") ?? "(not set)"));
                Log("TEMP before launch: "
                    + (Environment.GetEnvironmentVariable("TEMP") ?? "(not set)"));
                Log("TMP  before launch: "
                    + (Environment.GetEnvironmentVariable("TMP") ?? "(not set)"));

                // Also clear from this process env as defense-in-depth
                Environment.SetEnvironmentVariable("_MEIPASS2", null);

                var psi = new ProcessStartInfo(_target) { UseShellExecute = false };
                // Accessing EnvironmentVariables populates it from current process env
                // (StringDictionary; keys stored lowercase, lookups case-insensitive)
                var ev = psi.EnvironmentVariables;
                bool hadMei = ev.ContainsKey("_MEIPASS2");
                if (hadMei) ev.Remove("_MEIPASS2");
                Log("_MEIPASS2 was in env dict: " + hadMei.ToString()
                    + " | present after remove: " + ev.ContainsKey("_MEIPASS2").ToString());

                // Log what TEMP/TMP the new process will receive
                string tempInDict = ev.ContainsKey("TEMP") ? (string)ev["TEMP"] : "(not in dict)";
                string tmpInDict  = ev.ContainsKey("TMP")  ? (string)ev["TMP"]  : "(not in dict)";
                Log("TEMP in env dict: " + tempInDict);
                Log("TMP  in env dict: " + tmpInDict);
                // Log total env var count for sanity check
                Log("Env dict entry count: " + ev.Count.ToString());

                // TEMP/TMP を標準 Windows 一時フォルダに強制設定する。
                // PyInstaller ブートローダーは GetTempPathW() で展開先を決めるため
                // TEMP/TMP が誤ったパスになっていると _MEI* フォルダがそこに作られ
                // 旧 DLL を参照して起動に失敗する。
                string localAppData = Environment.GetFolderPath(
                    Environment.SpecialFolder.LocalApplicationData);
                string correctTemp = System.IO.Path.Combine(localAppData, "Temp");
                System.IO.Directory.CreateDirectory(correctTemp);
                ev["TEMP"] = correctTemp;
                ev["TMP"]  = correctTemp;
                Log("TEMP forced to: " + correctTemp);

                // config.json から旧 _MEI* 展開ディレクトリのパスを読み取り削除する。
                // PyInstaller 6.x は TEMP/TMP に関わらず独自のキャッシュ場所に
                // 展開ディレクトリを作るため、環境変数での制御は効かない。
                // NaroEditor 側が終了前に "_meipass_cleanup" キーへパスを書き込み、
                // ここで読んで削除することで新 NaroEditor の起動時に旧キャッシュが
                // 参照されなくなる。
                CleanupMeiPass();

                Log("Calling Process.Start: " + _target);
                Process.Start(psi);
                Log("Process.Start returned successfully.");

                Thread.Sleep(800);
                BeginInvoke((Action)Close);
            }
            catch (Exception ex)
            {
                Log("EXCEPTION: " + ex.GetType().Name + ": " + ex.Message
                    + "\r\n" + ex.StackTrace);
                SetStatus(string.Format("エラー: {0}", ex.Message), 0);
                Thread.Sleep(8000);
                BeginInvoke((Action)Close);
            }
        }

        void CleanupMeiPass()
        {
            // %LOCALAPPDATA%\NaroEditor\ 内の _MEI* ディレクトリをすべて削除する。
            // PyInstaller 6.x はこの場所を永続キャッシュとして使うため、
            // 旧バージョンの _MEI* が残っていると新 NaroEditor が誤参照して
            // DLL 読み込みに失敗する。
            // このメソッドは NaroEditor.exe の終了後に呼ばれるため、
            // すべての _MEI* ディレクトリを安全に削除できる。
            try
            {
                string localAppData = Environment.GetFolderPath(
                    Environment.SpecialFolder.LocalApplicationData);
                string cacheDir = Path.Combine(localAppData, "NaroEditor");
                Log("CleanupMeiPass: scanning " + cacheDir);

                if (!Directory.Exists(cacheDir))
                {
                    Log("CleanupMeiPass: cache dir does not exist, nothing to clean");
                    return;
                }

                string[] dirs = Directory.GetDirectories(cacheDir, "_MEI*");
                Log("CleanupMeiPass: found " + dirs.Length + " _MEI* director(ies)");

                foreach (string dir in dirs)
                {
                    try
                    {
                        Directory.Delete(dir, true);
                        Log("CleanupMeiPass: deleted " + dir);
                    }
                    catch (Exception ex)
                    {
                        Log("CleanupMeiPass: failed to delete " + dir + ": " + ex.Message);
                    }
                }
            }
            catch (Exception ex)
            {
                Log("CleanupMeiPass ERROR: " + ex.GetType().Name + ": " + ex.Message);
            }
        }
    }
}
