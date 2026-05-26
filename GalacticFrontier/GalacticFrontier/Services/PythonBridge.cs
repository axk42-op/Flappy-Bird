using System.Diagnostics;
using System.IO;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace GalacticFrontier.Services;

/// <summary>JSON newline RPC over Python bridge_server.py stdin/stdout.</summary>
public sealed class PythonBridge : IDisposable
{
    private Process? _process;
    private StreamWriter? _writer;
    private StreamReader? _reader;
    private readonly SemaphoreSlim _lock = new(1, 1);
    private bool _started;

    public static string FindGameRoot()
    {
        var dir = AppDomain.CurrentDomain.BaseDirectory;
        for (var i = 0; i < 10; i++)
        {
            if (File.Exists(Path.Combine(dir, "databaselogic.py")) &&
                File.Exists(Path.Combine(dir, "bridge_server.py")))
                return Path.GetFullPath(dir);
            var parent = Directory.GetParent(dir);
            if (parent == null) break;
            dir = parent.FullName;
        }
        return AppDomain.CurrentDomain.BaseDirectory;
    }

    public static string FindBridgeScript() =>
        Path.Combine(FindGameRoot(), "bridge_server.py");

    public async Task StartAsync(string? scriptPath = null)
    {
        if (_started) return;
        scriptPath ??= FindBridgeScript();
        if (!File.Exists(scriptPath))
            throw new FileNotFoundException("bridge_server.py not found", scriptPath);

        var psi = new ProcessStartInfo
        {
            FileName = "python",
            Arguments = $"\"{scriptPath}\"",
            UseShellExecute = false,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            WorkingDirectory = FindGameRoot(),
        };

        _process = Process.Start(psi) ?? throw new InvalidOperationException("Failed to start Python bridge.");
        _writer = _process.StandardInput;
        _reader = _process.StandardOutput;
        _started = true;

        var ping = await SendAsync("ping", new { }).ConfigureAwait(false);
        if (!ping.Value<bool>("success"))
            throw new InvalidOperationException("Bridge ping failed.");
    }

    public async Task<JObject> SendAsync(string method, object? parameters = null)
    {
        if (_writer == null || _reader == null)
            throw new InvalidOperationException("Bridge not started.");

        await _lock.WaitAsync().ConfigureAwait(false);
        try
        {
            var cmd = JsonConvert.SerializeObject(new { method, parameters });
            await _writer.WriteLineAsync(cmd).ConfigureAwait(false);
            await _writer.FlushAsync().ConfigureAwait(false);

            var line = await _reader.ReadLineAsync().ConfigureAwait(false);
            if (string.IsNullOrEmpty(line))
                throw new InvalidOperationException("Empty response from Python bridge.");
            return JObject.Parse(line);
        }
        finally
        {
            _lock.Release();
        }
    }

    public async Task StopAsync()
    {
        if (_writer != null)
        {
            try { _writer.Close(); } catch { /* ignore */ }
        }
        if (_process != null && !_process.HasExited)
        {
            try { _process.Kill(entireProcessTree: true); } catch { /* ignore */ }
            await _process.WaitForExitAsync().ConfigureAwait(false);
        }
        _started = false;
    }

    public void Dispose()
    {
        StopAsync().GetAwaiter().GetResult();
        _lock.Dispose();
    }
}
