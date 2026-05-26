using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;
using GalacticFrontier.ViewModels;

namespace GalacticFrontier.Views;

public partial class CombatView : UserControl
{
    private CombatViewModel? Vm => DataContext as CombatViewModel;

    public CombatView()
    {
        InitializeComponent();
    }

    private void CombatView_OnLoaded(object sender, RoutedEventArgs e)
    {
        Focus();
        if (Vm != null)
        {
            Vm.PlayWidth = GameCanvas.ActualWidth > 0 ? GameCanvas.ActualWidth : 1280;
            Vm.PlayHeight = GameCanvas.ActualHeight > 0 ? GameCanvas.ActualHeight : 720;
        }
        CompositionTarget.Rendering += OnRendering;
    }

    private void CombatView_OnUnloaded(object sender, RoutedEventArgs e) =>
        CompositionTarget.Rendering -= OnRendering;

    private void OnRendering(object? sender, EventArgs e)
    {
        if (Vm == null) return;
        var ts = DateTime.UtcNow.Ticks / 10000.0;
        Vm.PlayWidth = GameCanvas.ActualWidth;
        Vm.PlayHeight = GameCanvas.ActualHeight;
        Vm.UpdateFrame(ts);
        DrawFrame();
    }

    private void DrawFrame()
    {
        GameCanvas.Children.Clear();
        if (Vm == null) return;

        foreach (var p in Vm.Projectiles.Where(x => x.Alive))
        {
            var rect = new Rectangle
            {
                Width = 6, Height = 12,
                Fill = p.PlayerOwned ? (Brush)FindResource("CyanBrush") : (Brush)FindResource("DangerBrush"),
            };
            Canvas.SetLeft(rect, p.X - 3);
            Canvas.SetTop(rect, p.Y - 6);
            GameCanvas.Children.Add(rect);
        }

        foreach (var en in Vm.Enemies.Where(x => x.Alive))
        {
            var el = new Ellipse
            {
                Width = en.IsBoss ? 40 : 24,
                Height = en.IsBoss ? 40 : 24,
                Fill = (Brush)FindResource("DangerBrush"),
            };
            Canvas.SetLeft(el, en.X - el.Width / 2);
            Canvas.SetTop(el, en.Y - el.Height / 2);
            GameCanvas.Children.Add(el);
        }

        var ship = new Polygon
        {
            Points = new PointCollection { new(0, -12), new(10, 10), new(-10, 10) },
            Fill = (Brush)FindResource("CyanBrush"),
            RenderTransform = new RotateTransform(Vm.Player.Angle * 180 / Math.PI, 0, 0),
        };
        Canvas.SetLeft(ship, Vm.Player.X);
        Canvas.SetTop(ship, Vm.Player.Y);
        GameCanvas.Children.Add(ship);
    }

    private void CombatView_OnPreviewKeyDown(object sender, KeyEventArgs e) =>
        Vm?.SetKey(e.Key.ToString(), true);

    private void CombatView_OnPreviewKeyUp(object sender, KeyEventArgs e) =>
        Vm?.SetKey(e.Key.ToString(), false);

    private void CombatView_OnMouseMove(object sender, MouseEventArgs e)
    {
        var pos = e.GetPosition(GameCanvas);
        Vm?.AimAt(pos.X, pos.Y);
    }

    private void CombatView_OnMouseLeftDown(object sender, MouseButtonEventArgs e) => Vm?.FirePrimary();
    private void CombatView_OnMouseRightDown(object sender, MouseButtonEventArgs e) => Vm?.FireSecondary();
}
