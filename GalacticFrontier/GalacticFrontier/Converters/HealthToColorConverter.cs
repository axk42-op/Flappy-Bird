using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;

namespace GalacticFrontier.Converters;

public class HealthToColorConverter : IValueConverter
{
    public object Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        var pct = value is double d ? d : value is int i ? i : 100.0;
        if (pct > 60) return new SolidColorBrush(Color.FromRgb(0, 255, 136));
        if (pct > 30) return new SolidColorBrush(Color.FromRgb(255, 170, 0));
        return new SolidColorBrush(Color.FromRgb(255, 51, 51));
    }

    public object ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture) =>
        throw new NotSupportedException();
}
