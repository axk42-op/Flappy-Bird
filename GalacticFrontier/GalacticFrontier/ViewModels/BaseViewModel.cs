using System.ComponentModel;
using System.Runtime.CompilerServices;
using GalacticFrontier.Services;

namespace GalacticFrontier.ViewModels;

public abstract class BaseViewModel : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    public PythonBridge Bridge { get; private set; } = NavigationService.Instance.Bridge;

    public void AttachBridge(PythonBridge bridge) => Bridge = bridge;

    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? name = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value))
            return false;
        field = value;
        OnPropertyChanged(name);
        return true;
    }

    protected void OnPropertyChanged([CallerMemberName] string? name = null) =>
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));

    public virtual Task InitializeAsync(object? parameter) => Task.CompletedTask;

    protected static async Task RunOnUi(Action action)
    {
        await System.Windows.Application.Current.Dispatcher.InvokeAsync(action);
    }
}
