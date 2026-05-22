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
using System.Collections;
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
                // 診断ログ: 環境変数と NaroEditor.exe の場所を記録
                Log("[DIAG] TEMP="      + (Environment.GetEnvironmentVariable("TEMP")         ?? "(not set)"));
                Log("[DIAG] TMP="       + (Environment.GetEnvironmentVariable("TMP")          ?? "(not set)"));
                Log("[DIAG] APPDATA="   + (Environment.GetEnvironmentVariable("APPDATA")      ?? "(not set)"));
                Log("[DIAG] LOCALAPPDATA=" + (Environment.GetEnvironmentVariable("LOCALAPPDATA") ?? "(not set)"));
                Log("[DIAG] _MEIPASS2=" + (Environment.GetEnvironmentVariable("_MEIPASS2")    ?? "(not set)"));
                Log("[DIAG] target path=" + _target);
                Log("[DIAG] target dir=" + Path.GetDirectoryName(_target));

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

                SetStatus("再起動中…", 90);
                Thread.Sleep(500);

                // 3. Launch updated NaroEditor.
                //
                // 背景: PyInstaller onefile は起動時に _MEI<hash> へ全 DLL を展開する。
                // Updater が旧 _MEI* を削除してから新 NaroEditor を起動すると、
                // Windows Defender が展開直後の DLL をリアルタイムスキャンし、
                // bootloader の LoadLibrary が読み取りロック中に呼ばれて失敗する。
                //
                // 対策: CleanupMeiPass で旧 _MEI* を削除後、NaroEditor を起動する。
                // 1 回目の起動でブートローダーがクラッシュした場合（高速終了）、
                // AV スキャン完了を待機してから再起動する。
                // 2 回目以降: _MEI<hash> が既に存在するため展開スキップ → ロック競合なし。
                CleanupMeiPass();

                LaunchWithAvRetry();

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

        /// <summary>
        /// NaroEditor を起動し、AV スキャン競合によるブートローダークラッシュを
        /// 自動リトライで回避する。
        ///
        /// PyInstaller onefile は _MEI&lt;hash&gt; が存在する場合は展開をスキップする。
        /// 1 回目が失敗して _MEI* ディレクトリが残存していれば、
        /// AV スキャン完了後の 2 回目は展開スキップ → DLL ロード成功となる。
        /// </summary>
        void LaunchWithAvRetry()
        {
            const int maxAttempts    = 3;
            const int crashWindowMs  = 6000;   // この時間内に終了 = ブートローダークラッシュ
            const int avPollInterval = 500;    // AV スキャン完了ポーリング間隔
            const int avPollTimeout  = 60000;  // AV 完了待ちの最大時間

            // runtime_tmpdir の展開先ディレクトリ（AV スキャン確認に使用）
            string runtimeDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "NaroEditor", "runtime");

            for (int attempt = 1; attempt <= maxAttempts; attempt++)
            {
                Log(string.Format("Launch attempt {0}/{1}: {2}", attempt, maxAttempts, _target));

                // UseShellExecute=false: 確実なプロセスハンドルと環境変数制御のため。
                // 子プロセスには現プロセスの環境を渡しつつ、_MEIPASS2 と _MEI* PATH を除去。
                var psi = new ProcessStartInfo(_target)
                {
                    UseShellExecute = false,
                };

                // _MEIPASS2 を除去して bootloader が必ず展開処理を行うようにする
                if (psi.EnvironmentVariables.ContainsKey("_MEIPASS2"))
                    psi.EnvironmentVariables.Remove("_MEIPASS2");

                // PATH から _MEI* エントリを除去（旧 DLL が残留している場合の競合防止）
                if (psi.EnvironmentVariables.ContainsKey("PATH"))
                {
                    string original = psi.EnvironmentVariables["PATH"] ?? "";
                    string[] parts = original.Split(';');
                    var clean = new System.Collections.Generic.List<string>();
                    foreach (string p in parts)
                    {
                        string basename = Path.GetFileName(p.TrimEnd('\\', '/'));
                        if (!basename.Contains("_MEI"))
                            clean.Add(p);
                    }
                    psi.EnvironmentVariables["PATH"] = string.Join(";", clean.ToArray());
                }

                Process proc;
                try { proc = Process.Start(psi); }
                catch (Exception ex)
                {
                    Log("Process.Start exception: " + ex.Message);
                    if (attempt >= maxAttempts) throw;
                    WaitForAvScan(runtimeDir, avPollTimeout, avPollInterval, attempt);
                    continue;
                }

                if (proc == null)
                {
                    Log("Process.Start returned null.");
                    if (attempt >= maxAttempts)
                        throw new InvalidOperationException("Process.Start returned null.");
                    WaitForAvScan(runtimeDir, avPollTimeout, avPollInterval, attempt);
                    continue;
                }

                Log(string.Format("Process started, PID={0}. Watching for {1}s...",
                    proc.Id, crashWindowMs / 1000));

                bool exitedQuickly = proc.WaitForExit(crashWindowMs);

                if (!exitedQuickly)
                {
                    Log(string.Format(
                        "Process still running after {0}s → launch successful.", crashWindowMs / 1000));
                    return;
                }

                int code = proc.ExitCode;
                Log(string.Format("Process exited quickly, exit code={0}.", code));

                if (code == 0)
                {
                    Log("Process exited cleanly (exit code 0).");
                    return;
                }

                // 非ゼロ高速終了 = ブートローダークラッシュ（AV スキャン競合が最有力）
                if (attempt < maxAttempts)
                {
                    Log("Bootloader crash detected. Waiting for AV scan to complete...");
                    WaitForAvScan(runtimeDir, avPollTimeout, avPollInterval, attempt);
                }
            }

            Log("WARNING: All launch attempts exhausted. User must start NaroEditor manually.");
            SetStatus("自動起動に失敗しました。NaroEditor.exe を手動で起動してください。", 0);
            Thread.Sleep(10000);
        }

        /// <summary>
        /// _MEI* ディレクトリ内の Python DLL がアクセス可能になるまで待機する。
        /// Windows Defender 等の AV スキャナが展開直後の DLL をロックしている間はブロックする。
        /// </summary>
        void WaitForAvScan(string runtimeDir, int maxWaitMs, int pollInterval, int attemptNum)
        {
            SetStatus(string.Format(
                "セキュリティソフトのスキャン完了待機中… (試行 {0})", attemptNum), 70);

            int elapsed = 0;
            string meiDir = null;
            string targetDll = null;

            Log(string.Format("[AV-WAIT] Polling for DLL access (max {0}s)...", maxWaitMs / 1000));

            while (elapsed < maxWaitMs)
            {
                // _MEI* ディレクトリを探す（前回の失敗起動で残存したはず）
                if (targetDll == null && Directory.Exists(runtimeDir))
                {
                    try
                    {
                        string[] meiDirs = Directory.GetDirectories(runtimeDir, "_MEI*");
                        if (meiDirs.Length > 0)
                        {
                            meiDir = meiDirs[0];
                            // python*.dll を探す
                            string[] dlls = Directory.GetFiles(meiDir, "python*.dll");
                            if (dlls.Length > 0)
                                targetDll = dlls[0];
                        }
                    }
                    catch { }
                }

                if (targetDll != null)
                {
                    try
                    {
                        // DLL が読み取れれば AV ロック解除済み
                        using (FileStream fs = File.Open(
                            targetDll, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                        { }
                        Log(string.Format(
                            "[AV-WAIT] DLL accessible after {0}ms: {1}", elapsed, targetDll));
                        Thread.Sleep(500); // ロック解除後の安定待機
                        return;
                    }
                    catch (IOException) { }
                }

                Thread.Sleep(pollInterval);
                elapsed += pollInterval;
            }

            Log(string.Format("[AV-WAIT] Timed out after {0}ms.", maxWaitMs));
        }

        void CleanupMeiPass()
        {
            // v1.2.21+: 正規展開先 %APPDATA%\NaroEditor\runtime\_MEI* をスキャン。
            // v1.2.13 以前の遺物: %LOCALAPPDATA%\NaroEditor\_MEI* も引き続きスキャン。
            SweepMeiDirs(Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "NaroEditor", "runtime"));
            SweepMeiDirs(Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "NaroEditor"));
        }

        void SweepMeiDirs(string cacheDir)
        {
            try
            {
                Log("SweepMeiDirs: scanning " + cacheDir);
                if (!Directory.Exists(cacheDir))
                {
                    Log("SweepMeiDirs: does not exist, skipping");
                    return;
                }
                string[] dirs = Directory.GetDirectories(cacheDir, "_MEI*");
                Log("SweepMeiDirs: found " + dirs.Length + " _MEI* director(ies)");
                foreach (string dir in dirs)
                {
                    try
                    {
                        Directory.Delete(dir, true);
                        Log("SweepMeiDirs: deleted " + dir);
                    }
                    catch (Exception ex)
                    {
                        Log("SweepMeiDirs: failed to delete " + dir + ": " + ex.Message);
                    }
                }
            }
            catch (Exception ex)
            {
                Log("SweepMeiDirs ERROR (" + cacheDir + "): " + ex.GetType().Name + ": " + ex.Message);
            }
        }
    }
}
