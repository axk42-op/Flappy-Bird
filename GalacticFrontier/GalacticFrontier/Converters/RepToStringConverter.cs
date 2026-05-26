using System.Globalization;
using System.Windows.Data;

namespace GalacticFrontier.Converters;

public class RepToStringConverter : IValueConverter
{
    public object Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        var rep = value is int i ? i : 0;
        if (rep >= 50) return "Allied";
        if (rep >= 0) return "Neutral";
        if (rep >= -20) return "Wary";
        return "Hostile";
    }

    public object ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture) =>
        throw new NotSupportedException();
}
