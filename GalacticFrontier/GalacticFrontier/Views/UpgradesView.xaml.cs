using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using GalacticFrontier.ViewModels;

namespace GalacticFrontier.Views;

public partial class UpgradesView : UserControl
{
    private readonly Dictionary<string, (Button Btn, Line Line)> _nodes = new();

    public UpgradesView()
    {
        InitializeComponent();
        Loaded += (_, _) => BuildNodes();
        DataContextChanged += (_, _) => BuildNodes();
    }

    private void UpgradeCanvas_OnSizeChanged(object sender, SizeChangedEventArgs e) => BuildNodes();

    private void BuildNodes()
    {
        if (DataContext is not UpgradesViewModel vm || UpgradeCanvas.ActualWidth < 100) return;
        UpgradeCanvas.Children.Clear();
        _nodes.Clear();
        var cx = UpgradeCanvas.ActualWidth / 2;
        var cy = UpgradeCanvas.ActualHeight / 2;

        var shipPath = new Path
        {
            Data = Geometry.Parse(vm.ShipSilhouette),
            Fill = new SolidColorBrush(Color.FromArgb(80, 30, 144, 255)),
            Stroke = (Brush)FindResource("CyanBrush"),
            StrokeThickness = 2,
            Width = 120, Height = 120,
        };
        Canvas.SetLeft(shipPath, cx - 60);
        Canvas.SetTop(shipPath, cy - 60);
        UpgradeCanvas.Children.Add(shipPath);

        foreach (var slot in UpgradesViewModel.Slots)
        {
            var nx = cx + slot.OffsetX;
            var ny = cy + slot.OffsetY;
            var line = new Line
            {
                X1 = cx, Y1 = cy, X2 = nx, Y2 = ny,
                Stroke = (Brush)FindResource("BlueBrush"),
                StrokeThickness = 1,
                Opacity = 0.5,
            };
            UpgradeCanvas.Children.Add(line);

            var btn = new Button
            {
                Width = 44, Height = 44,
                Content = new TextBlock { Text = slot.TierRoman, Foreground = Brushes.White, FontSize = 10 },
                Tag = slot,
                Style = (Style)FindResource("SciFiButton"),
            };
            btn.Click += (_, _) => vm.SelectSlotCommand.Execute(slot);
            Canvas.SetLeft(btn, nx - 22);
            Canvas.SetTop(btn, ny - 22);
            UpgradeCanvas.Children.Add(btn);
            _nodes[slot.Key] = (btn, line);
        }
    }
}
