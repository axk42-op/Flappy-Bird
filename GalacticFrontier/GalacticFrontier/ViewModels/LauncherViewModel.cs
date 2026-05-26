using System.Windows;
using System.Windows.Input;
using GalacticFrontier.Services;

namespace GalacticFrontier.ViewModels;

public class LauncherViewModel : BaseViewModel
{
    public ICommand LaunchCommand { get; }
    public ICommand SignupCommand { get; }
    public ICommand ExitCommand { get; }

    public string Title => Strings.AppTitle;
    public string Subtitle => Strings.TerminalVersion;
    public string StatusText => Strings.SystemOnline;

    public LauncherViewModel()
    {
        LaunchCommand = new RelayCommand(_ => NavigationService.Instance.GoToLogin());
        SignupCommand = new RelayCommand(_ => NavigationService.Instance.GoToSignup());
        ExitCommand = new RelayCommand(_ => System.Windows.Application.Current.Shutdown());
    }
}

public sealed class RelayCommand : ICommand
{
    private readonly Action<object?> _execute;
    private readonly Func<object?, bool>? _canExecute;
    public RelayCommand(Action<object?> execute, Func<object?, bool>? canExecute = null)
    {
        _execute = execute;
        _canExecute = canExecute;
    }
    public bool CanExecute(object? parameter) => _canExecute?.Invoke(parameter) ?? true;
    public void Execute(object? parameter) => _execute(parameter);
    public event EventHandler? CanExecuteChanged
    {
        add => CommandManager.RequerySuggested += value;
        remove => CommandManager.RequerySuggested -= value;
    }
}
