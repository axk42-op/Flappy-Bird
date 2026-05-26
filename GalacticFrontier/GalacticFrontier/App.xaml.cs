using System.Windows;
using GalacticFrontier.Services;
using GalacticFrontier.ViewModels;
using GalacticFrontier.Views;

namespace GalacticFrontier;

public partial class App : Application
{
    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        FontLoader.EnsureOrbitron();

        var main = new MainWindow();
        MainWindow = main;
        NavigationService.Instance.Host = main.NavHost;

        try
        {
            await NavigationService.Instance.Bridge.StartAsync();
        }
        catch (Exception ex)
        {
            main.NavHost.Content = new System.Windows.Controls.TextBlock
            {
                Text = $"{Strings.BridgeError}\n{ex.Message}",
                Foreground = System.Windows.Media.Brushes.OrangeRed,
                Margin = new Thickness(40),
                TextWrapping = TextWrapping.Wrap,
                FontSize = 14,
            };
            main.Show();
            return;
        }

        main.Show();
        await NavigationService.Instance.NavigateToAsync<LauncherView, LauncherViewModel>(pushStack: false);
    }

    protected override async void OnExit(ExitEventArgs e)
    {
        try
        {
            await SessionPersistence.SaveAsync(NavigationService.Instance.Bridge, SessionState.Instance);
            await NavigationService.Instance.Bridge.StopAsync();
        }
        catch { /* ignore on shutdown */ }
        base.OnExit(e);
    }
}
