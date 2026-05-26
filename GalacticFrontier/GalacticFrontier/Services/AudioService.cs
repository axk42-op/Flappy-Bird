using System.IO;
using System.Windows.Media;

namespace GalacticFrontier.Services;

/// <summary>Optional ambient UI sounds via MediaPlayer.</summary>
public sealed class AudioService
{
    private static readonly Lazy<AudioService> _instance = new(() => new AudioService());
    public static AudioService Instance => _instance.Value;

    private readonly MediaPlayer _player = new();

    public void PlayUiClick()
    {
        try
        {
            _player.Stop();
            _player.Volume = 0.15;
        }
        catch
        {
            // Audio is optional
        }
    }
}
