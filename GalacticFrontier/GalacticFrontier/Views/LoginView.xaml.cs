using System.Windows;
using System.Windows.Controls;
using GalacticFrontier.ViewModels;

namespace GalacticFrontier.Views;

public partial class LoginView : UserControl
{
    public LoginView()
    {
        InitializeComponent();
        DataContextChanged += (_, _) =>
        {
            if (Vm != null)
                Vm.PropertyChanged += (_, args) =>
                {
                    if (args.PropertyName == nameof(LoginViewModel.ShowPassword))
                        SyncPasswordVisibility();
                };
            SyncPasswordVisibility();
        };
    }

    private LoginViewModel? Vm => DataContext as LoginViewModel;

    private void PasswordBox_OnPasswordChanged(object sender, RoutedEventArgs e)
    {
        if (Vm != null && !Vm.ShowPassword)
            Vm.Password = PasswordBox.Password;
    }

    private void PasswordVisible_OnTextChanged(object sender, TextChangedEventArgs e)
    {
        if (Vm != null && Vm.ShowPassword)
            Vm.Password = PasswordVisible.Text;
    }

    private void SyncPasswordVisibility()
    {
        if (Vm == null) return;
        if (Vm.ShowPassword)
        {
            PasswordVisible.Text = Vm.Password;
            PasswordVisible.Visibility = Visibility.Visible;
            PasswordBox.Visibility = Visibility.Collapsed;
        }
        else
        {
            PasswordBox.Password = Vm.Password;
            PasswordBox.Visibility = Visibility.Visible;
            PasswordVisible.Visibility = Visibility.Collapsed;
        }
    }
}
