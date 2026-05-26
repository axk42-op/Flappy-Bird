using System.Windows.Controls;
using GalacticFrontier.ViewModels;

namespace GalacticFrontier.Views;

public partial class SignupView : UserControl
{
    public SignupView() => InitializeComponent();

    private void Pw1_OnPasswordChanged(object sender, System.Windows.RoutedEventArgs e)
    {
        if (DataContext is SignupViewModel vm) vm.Password = Pw1.Password;
    }

    private void Pw2_OnPasswordChanged(object sender, System.Windows.RoutedEventArgs e)
    {
        if (DataContext is SignupViewModel vm) vm.ConfirmPassword = Pw2.Password;
    }
}
