using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;

namespace GalacticFrontier.Controls;

public partial class StarfieldControl : UserControl
{
    private readonly List<Star> _stars = new();
    private readonly Random _rng = new();
    private bool _running;

    private sealed class Star
    {
        public Ellipse Shape = null!;
        public double X, Y, Speed;
        public double Phase;
        public int Layer;
    }

    public StarfieldControl()
    {
        InitializeComponent();
        Loaded += OnLoaded;
        Unloaded += OnUnloaded;
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        if (_stars.Count == 0)
            InitStars(200);
        if (!_running)
        {
            _running = true;
            CompositionTarget.Rendering += OnRendering;
        }
    }

    private void OnUnloaded(object sender, RoutedEventArgs e)
    {
        _running = false;
        CompositionTarget.Rendering -= OnRendering;
    }

    private void InitStars(int count)
    {
        StarCanvas.Children.Clear();
        _stars.Clear();
        var w = ActualWidth > 0 ? ActualWidth : 1280;
        var h = ActualHeight > 0 ? ActualHeight : 800;
        for (var i = 0; i < count; i++)
        {
            var layer = _rng.Next(3);
            var speed = layer switch { 0 => 0.2, 1 => 0.5, _ => 1.0 } * _rng.NextDouble() * 0.5 + 0.5;
            var size = _rng.NextDouble() < 0.7 ? 1.5 : 2.5;
            var star = new Star
            {
                X = _rng.NextDouble() * w,
                Y = _rng.NextDouble() * h,
                Speed = speed,
                Phase = _rng.NextDouble() * Math.PI * 2,
                Layer = layer,
            };
            star.Shape = new Ellipse
            {
                Width = size,
                Height = size,
                Fill = Brushes.White,
            };
            Canvas.SetLeft(star.Shape, star.X);
            Canvas.SetTop(star.Shape, star.Y);
            StarCanvas.Children.Add(star.Shape);
            _stars.Add(star);
        }
    }

    private void OnRendering(object? sender, EventArgs e)
    {
        if (!_running || ActualWidth <= 0 || ActualHeight <= 0) return;
        var h = ActualHeight;
        var w = ActualWidth;
        var t = DateTime.Now.TimeOfDay.TotalSeconds;
        foreach (var s in _stars)
        {
            s.Y += s.Speed;
            if (s.Y > h)
            {
                s.Y = 0;
                s.X = _rng.NextDouble() * w;
            }
            var bright = 0.45 + 0.55 * (0.5 + 0.5 * Math.Sin(t * 2 + s.Phase));
            s.Shape.Opacity = bright;
            Canvas.SetLeft(s.Shape, s.X);
            Canvas.SetTop(s.Shape, s.Y);
        }
    }
}
