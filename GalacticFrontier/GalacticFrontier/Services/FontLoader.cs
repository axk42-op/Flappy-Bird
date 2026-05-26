using System.IO;
using System.Net;
using System.Windows;
using System.Windows.Media;

namespace GalacticFrontier.Services;

public static class FontLoader
{
    private const string OrbitronUrl =
        "https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf";

    public static void EnsureOrbitron()
    {
        try
        {
            var fontsDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "GalacticFrontier", "Fonts");
            Directory.CreateDirectory(fontsDir);
            var fontPath = Path.Combine(fontsDir, "Orbitron.ttf");
            if (!File.Exists(fontPath))
            {
                using var client = new WebClient();
                client.DownloadFile(OrbitronUrl, fontPath);
            }
            if (File.Exists(fontPath))
            {
                var family = new FontFamily(new Uri(fontPath, UriKind.Absolute), "./#Orbitron");
                Application.Current.Resources["TitleFont"] = family;
            }
        }
        catch
        {
            Application.Current.Resources["TitleFont"] = new FontFamily("Courier New");
        }
    }
}
