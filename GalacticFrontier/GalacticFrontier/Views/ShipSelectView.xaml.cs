using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using GalacticFrontier.Models;
using GalacticFrontier.ViewModels;

namespace GalacticFrontier.Views;

public partial class ShipSelectView : UserControl
{
    public ShipSelectView()
    {
        InitializeComponent();
        DataContextChanged += (_, _) => HighlightSelected();
    }

    private void ShipCard_OnClick(object sender, MouseButtonEventArgs e)
    {
        if (sender is Border border && border.DataContext is ShipModel ship
            && DataContext is ShipSelectViewModel vm)
        {
            vm.SelectedShip = ship;
            HighlightSelected();
        }
    }

    private void HighlightSelected()
    {
        if (DataContext is not ShipSelectViewModel vm) return;
        void Walk(DependencyObject parent)
        {
            if (parent is Border b && b.Tag is string id)
                b.BorderThickness = id == vm.SelectedShip?.Id ? new Thickness(2) : new Thickness(1);
            for (var i = 0; i < VisualTreeHelper.GetChildrenCount(parent); i++)
                Walk(VisualTreeHelper.GetChild(parent, i));
        }
        Walk(this);
    }
}
