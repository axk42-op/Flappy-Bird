using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;
using GalacticFrontier.Models;
using GalacticFrontier.ViewModels;

namespace GalacticFrontier.Views;

public partial class GalaxyMapView : UserControl
{
    private bool _dragging;
    private Point _dragStart;
    private GalaxyMapViewModel? Vm => DataContext as GalaxyMapViewModel;

    private static readonly Dictionary<string, Color> FactionColors = new()
    {
        ["empire"] = Color.FromRgb(255, 80, 80),
        ["foundation"] = Color.FromRgb(80, 180, 255),
        ["pirates"] = Color.FromRgb(255, 140, 40),
        ["guild"] = Color.FromRgb(0, 245, 255),
        ["ai"] = Color.FromRgb(180, 80, 255),
    };

    public GalaxyMapView()
    {
        InitializeComponent();
        Loaded += (_, _) => DrawMap();
        DataContextChanged += (_, _) => DrawMap();
    }

    private void DrawMap()
    {
        MapContent.Children.Clear();
        if (Vm == null) return;

        foreach (var (a, b) in Vm.Lanes)
        {
            var sa = Vm.Systems.FirstOrDefault(s => s.Id == a);
            var sb = Vm.Systems.FirstOrDefault(s => s.Id == b);
            if (sa == null || sb == null) continue;
            MapContent.Children.Add(new Line
            {
                X1 = sa.X, Y1 = sa.Y, X2 = sb.X, Y2 = sb.Y,
                Stroke = new SolidColorBrush(Color.FromArgb(60, 0, 245, 255)),
                StrokeThickness = 1,
            });
        }

        foreach (var sys in Vm.Systems)
        {
            var col = FactionColors.GetValueOrDefault(sys.Faction, Colors.Gray);
            var size = 8 + sys.Threat;
            var el = new Ellipse
            {
                Width = size, Height = size,
                Fill = new SolidColorBrush(sys.IsDiscovered ? col : Color.FromRgb(60, 60, 80)),
                Stroke = new SolidColorBrush(Colors.White),
                StrokeThickness = sys.Id == Vm.PlayerSystemId ? 2 : 0.5,
                Tag = sys,
            };
            Canvas.SetLeft(el, sys.X - size / 2);
            Canvas.SetTop(el, sys.Y - size / 2);
            el.MouseLeftButtonDown += System_OnClick;
            MapContent.Children.Add(el);
        }

        var player = Vm.Systems.FirstOrDefault(s => s.Id == Vm.PlayerSystemId);
        if (player != null)
        {
            var ship = new Polygon
            {
                Points = new PointCollection { new(0, -10), new(8, 8), new(-8, 8) },
                Fill = new SolidColorBrush(Color.FromRgb(0, 245, 255)),
                RenderTransform = new RotateTransform(0, 0, 0),
            };
            Canvas.SetLeft(ship, player.X - 8);
            Canvas.SetTop(ship, player.Y - 8);
            MapContent.Children.Add(ship);
        }
    }

    private void System_OnClick(object sender, MouseButtonEventArgs e)
    {
        if (sender is Ellipse el && el.Tag is StarSystemModel sys)
            Vm?.SelectSystem(sys);
        e.Handled = true;
    }

    private void MapCanvas_OnMouseDown(object sender, MouseButtonEventArgs e)
    {
        if (e.OriginalSource == MapCanvas)
        {
            _dragging = true;
            _dragStart = e.GetPosition(MapCanvas);
            MapCanvas.CaptureMouse();
        }
    }

    private void MapCanvas_OnMouseMove(object sender, MouseEventArgs e)
    {
        if (!_dragging || Vm == null) return;
        var pos = e.GetPosition(MapCanvas);
        MapPan.X += pos.X - _dragStart.X;
        MapPan.Y += pos.Y - _dragStart.Y;
        _dragStart = pos;
        Vm.MapOffsetX = MapPan.X;
        Vm.MapOffsetY = MapPan.Y;
    }

    private void MapCanvas_OnMouseUp(object sender, MouseButtonEventArgs e)
    {
        _dragging = false;
        MapCanvas.ReleaseMouseCapture();
    }
}
