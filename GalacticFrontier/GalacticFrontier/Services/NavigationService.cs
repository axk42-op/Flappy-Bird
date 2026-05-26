using System.Windows;
using System.Windows.Controls;
using GalacticFrontier.ViewModels;
using GalacticFrontier.Views;

namespace GalacticFrontier.Services;

public sealed class NavigationService
{
    private static readonly Lazy<NavigationService> _instance = new(() => new NavigationService());
    public static NavigationService Instance => _instance.Value;

    public ContentControl? Host { get; set; }
    public UserControl? CurrentView { get; private set; }
    public BaseViewModel? CurrentViewModel { get; private set; }
    private readonly Stack<(Type ViewType, Type VmType, object? Param)> _stack = new();

    public PythonBridge Bridge { get; } = new();

    public async Task NavigateToAsync<TView, TViewModel>(object? parameter = null, bool pushStack = true)
        where TView : UserControl, new()
        where TViewModel : BaseViewModel, new()
    {
        if (Host == null)
            throw new InvalidOperationException("Navigation host not set.");

        if (pushStack && CurrentView != null)
            _stack.Push((typeof(TView), typeof(TViewModel), parameter));

        await Host.Dispatcher.InvokeAsync(async () =>
        {
            var fadeOut = Application.Current.TryFindResource("FadeOutStoryboard") as System.Windows.Media.Animation.Storyboard;
            if (fadeOut != null && CurrentView != null)
            {
                fadeOut.Begin(CurrentView);
                await Task.Delay(150);
            }

            var view = new TView();
            var vm = new TViewModel();
            vm.AttachBridge(Bridge);
            view.DataContext = vm;
            CurrentView = view;
            CurrentViewModel = vm;
            Host.Content = view;

            await vm.InitializeAsync(parameter).ConfigureAwait(true);

            var fadeIn = Application.Current.TryFindResource("FadeInStoryboard") as System.Windows.Media.Animation.Storyboard;
            fadeIn?.Begin(view);
        });
    }

    public void GoToLauncher() => _ = NavigateToAsync<LauncherView, LauncherViewModel>();
    public void GoToLogin(object? prefill = null) => _ = NavigateToAsync<LoginView, LoginViewModel>(prefill);
    public void GoToSignup() => _ = NavigateToAsync<SignupView, SignupViewModel>();
    public void GoToShipSelect() => _ = NavigateToAsync<ShipSelectView, ShipSelectViewModel>();
    public void GoToGalaxyMap() => _ = NavigateToAsync<GalaxyMapView, GalaxyMapViewModel>();
    public void GoToTrading() => _ = NavigateToAsync<TradingView, TradingViewModel>();
    public void GoToUpgrades() => _ = NavigateToAsync<UpgradesView, UpgradesViewModel>();
    public void GoToCombat() => _ = NavigateToAsync<CombatView, CombatViewModel>();
}
