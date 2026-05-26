using System.Windows;
using System.Windows.Input;
using System.Windows.Threading;
using GalacticFrontier.Services;
using Newtonsoft.Json.Linq;

namespace GalacticFrontier.ViewModels;

public class LoginViewModel : BaseViewModel
{
    private string _username = "";
    private string _password = "";
    private string _error = "";
    private bool _showPassword;
    private int _attempts;
    private int _lockoutSeconds;
    private DispatcherTimer? _lockoutTimer;

    public string Username { get => _username; set => SetProperty(ref _username, value); }
    public string Password { get => _password; set => SetProperty(ref _password, value); }
    public string ErrorMessage { get => _error; set => SetProperty(ref _error, value); }
    public bool HasError => !string.IsNullOrEmpty(_error);
    public bool ShowPassword { get => _showPassword; set => SetProperty(ref _showPassword, value); }
    public bool IsLockedOut => _lockoutSeconds > 0;
    public string LockoutText => string.Format(Strings.Lockout, _lockoutSeconds);

    public ICommand LoginCommand { get; }
    public ICommand TogglePasswordCommand { get; }
    public ICommand BackCommand { get; }

    public LoginViewModel()
    {
        LoginCommand = new RelayCommand(async _ => await LoginAsync(), _ => !IsLockedOut);
        TogglePasswordCommand = new RelayCommand(_ => ShowPassword = !ShowPassword);
        BackCommand = new RelayCommand(_ => NavigationService.Instance.GoToLauncher());
    }

    public override Task InitializeAsync(object? parameter)
    {
        if (parameter is string prefill)
            Username = prefill;
        return Task.CompletedTask;
    }

    private async Task LoginAsync()
    {
        ErrorMessage = "";
        try
        {
            var res = await Bridge.SendAsync("verify_login", new { username = Username, password = Password });
            if (res.Value<bool>("success"))
            {
                var dataRes = await Bridge.SendAsync("get_user_data", new { username = Username });
                if (dataRes.Value<bool>("success"))
                {
                    await RunOnUi(() =>
                    {
                        SessionState.Instance.ApplyUser(ParseUser(dataRes["data"]!));
                        NavigationService.Instance.GoToShipSelect();
                    });
                    return;
                }
            }
            _attempts++;
            await RunOnUi(() =>
            {
                ErrorMessage = res.Value<string>("error") ?? Strings.InvalidCredentials;
                if (_attempts >= 3)
                    StartLockout();
            });
        }
        catch (Exception ex)
        {
            await RunOnUi(() => ErrorMessage = ex.Message);
        }
    }

    private void StartLockout()
    {
        _attempts = 0;
        _lockoutSeconds = 5;
        OnPropertyChanged(nameof(IsLockedOut));
        OnPropertyChanged(nameof(LockoutText));
        _lockoutTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
        _lockoutTimer.Tick += (_, _) =>
        {
            _lockoutSeconds--;
            OnPropertyChanged(nameof(LockoutText));
            OnPropertyChanged(nameof(IsLockedOut));
            if (_lockoutSeconds <= 0)
            {
                _lockoutTimer.Stop();
                ErrorMessage = "";
            }
        };
        _lockoutTimer.Start();
    }

    internal static Models.UserModel ParseUser(JToken token)
    {
        var u = new Models.UserModel
        {
            Username = token.Value<string>("username") ?? "",
            Credits = token.Value<int?>("credits") ?? 0,
            Highscore = token.Value<int?>("highscore") ?? 0,
            SelectedShip = token.Value<string>("selected_ship") ?? "falcon",
            CommanderTitle = token.Value<string>("commander_title") ?? "Commander",
        };
        if (token["ship_upgrades"] is JObject up)
            foreach (var p in up.Properties())
                u.ShipUpgrades[p.Name] = p.Value.Value<int>();
        if (token["faction_rep"] is JObject rep)
            foreach (var p in rep.Properties())
                u.FactionRep[p.Name] = p.Value.Value<int>();
        if (token["discovered_systems"] is JArray disc)
            u.DiscoveredSystems = disc.Select(x => x.Value<int>()).ToList();
        if (token["session"] is JObject sess)
        {
            u.Session = new Models.SessionModel
            {
                CurrentSystem = sess.Value<int?>("current_system") ?? 0,
                Hull = sess.Value<double?>("hull") ?? 100,
                MaxHull = sess.Value<double?>("max_hull") ?? 100,
                Fuel = sess.Value<int?>("fuel") ?? 100,
                MaxFuel = sess.Value<int?>("max_fuel") ?? 100,
                CargoCapacity = sess.Value<int?>("cargo_capacity") ?? 20,
                Day = sess.Value<int?>("day") ?? 1,
                Wave = sess.Value<int?>("wave") ?? 1,
            };
            if (sess["cargo"] is JObject cargo)
                foreach (var p in cargo.Properties())
                    u.Session.Cargo[p.Name] = p.Value.Value<int>();
        }
        return u;
    }
}
