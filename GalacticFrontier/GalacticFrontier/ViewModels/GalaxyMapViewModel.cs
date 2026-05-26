using System.Windows.Input;
using GalacticFrontier.Models;
using GalacticFrontier.Services;
namespace GalacticFrontier.ViewModels;

public class GalaxyMapViewModel : BaseViewModel
{
    private StarSystemModel? _selected;
    private double _offsetX;
    private double _offsetY;
    private string _status = "";

    public IReadOnlyList<StarSystemModel> Systems => SessionState.Instance.Systems;
    public IReadOnlyList<(int A, int B)> Lanes => SessionState.Instance.Lanes;
    public double MapOffsetX { get => _offsetX; set => SetProperty(ref _offsetX, value); }
    public double MapOffsetY { get => _offsetY; set => SetProperty(ref _offsetY, value); }

    public StarSystemModel? SelectedSystem
    {
        get => _selected;
        set
        {
            if (SetProperty(ref _selected, value))
            {
                OnPropertyChanged(nameof(HasSelection));
                OnPropertyChanged(nameof(SelectedName));
                OnPropertyChanged(nameof(SelectedFaction));
                OnPropertyChanged(nameof(SelectedEconomy));
                OnPropertyChanged(nameof(SelectedThreat));
                OnPropertyChanged(nameof(ThreatStars));
            }
        }
    }

    public bool HasSelection => SelectedSystem != null;
    public string SelectedName => SelectedSystem?.Name ?? "—";
    public string SelectedFaction => SelectedSystem?.Faction ?? "";
    public string SelectedEconomy => SelectedSystem?.Economy ?? "";
    public int SelectedThreat => SelectedSystem?.Threat ?? 0;
    public string ThreatStars => SelectedSystem == null ? "" : new string('★', SelectedSystem.Threat) + new string('☆', 5 - SelectedSystem.Threat);
    public string HudCredits => $"Credits: {SessionState.Instance.Credits}";
    public string HudFuel => $"Fuel: {SessionState.Instance.Fuel}";
    public string HudHull => $"Hull: {SessionState.Instance.Hull:F0}%";
    public string HudCargo => $"Cargo: {SessionState.Instance.CargoUsed}/{SessionState.Instance.User?.Session.CargoCapacity ?? 20}";
    public string HudWave => $"Wave: {SessionState.Instance.Wave}";
    public string StatusMessage { get => _status; set => SetProperty(ref _status, value); }

    public int PlayerSystemId => SessionState.Instance.User?.Session.CurrentSystem ?? 0;

    public ICommand TravelCommand { get; }
    public ICommand TradeCommand { get; }
    public ICommand ScanCommand { get; }
    public ICommand EngageCommand { get; }
    public ICommand UpgradesCommand { get; }

    public GalaxyMapViewModel()
    {
        TravelCommand = new RelayCommand(async _ => await TravelAsync(), _ => SelectedSystem != null);
        TradeCommand = new RelayCommand(_ => NavigationService.Instance.GoToTrading(), _ => SelectedSystem != null);
        ScanCommand = new RelayCommand(async _ => await ScanAsync(), _ => SelectedSystem != null);
        EngageCommand = new RelayCommand(_ => NavigationService.Instance.GoToCombat(), _ => SelectedSystem != null);
        UpgradesCommand = new RelayCommand(_ => NavigationService.Instance.GoToUpgrades());
    }

    public override async Task InitializeAsync(object? parameter)
    {
        var s = SessionState.Instance;
        if (s.Systems.Count == 0)
            await ReloadGalaxyAsync();
        SelectedSystem = s.Systems.FirstOrDefault(x => x.Id == s.SelectedSystemId)
                         ?? s.Systems.FirstOrDefault(x => x.Id == PlayerSystemId)
                         ?? s.Systems.FirstOrDefault();
        RefreshHud();
    }

    public void SelectSystem(StarSystemModel sys)
    {
        SelectedSystem = sys;
        SessionState.Instance.SelectedSystemId = sys.Id;
    }

    private void RefreshHud()
    {
        OnPropertyChanged(nameof(HudCredits));
        OnPropertyChanged(nameof(HudFuel));
        OnPropertyChanged(nameof(HudHull));
        OnPropertyChanged(nameof(HudCargo));
        OnPropertyChanged(nameof(HudWave));
    }

    private async Task ReloadGalaxyAsync()
    {
        var res = await Bridge.SendAsync("get_galaxy", new { username = SessionState.Instance.Username });
        if (!res.Value<bool>("success")) return;
        SessionState.Instance.Systems = res["systems"]!.Select(t => ShipSelectViewModel.ParseSystemFromToken(t)).ToList();
        SessionState.Instance.Lanes = res["lanes"]!.Select(l => (l[0]!.ToObject<int>(), l[1]!.ToObject<int>())).ToList();
        foreach (var sys in SessionState.Instance.Systems)
            sys.IsDiscovered = SessionState.Instance.DiscoveredSystems.Contains(sys.Id);
        OnPropertyChanged(nameof(Systems));
        OnPropertyChanged(nameof(Lanes));
    }

    private async Task TravelAsync()
    {
        if (SelectedSystem == null) return;
        var s = SessionState.Instance;
        var fuelCost = 8 + SelectedSystem.Threat * 2;
        if (s.Fuel < fuelCost)
        {
            StatusMessage = "Insufficient fuel.";
            return;
        }
        s.Fuel -= fuelCost;
        if (s.User != null)
        {
            s.User.Session.CurrentSystem = SelectedSystem.Id;
            s.User.Session.Fuel = s.Fuel;
        }
        await Bridge.SendAsync("mark_system_discovered", new { username = s.Username, system_id = SelectedSystem.Id });
        if (!s.DiscoveredSystems.Contains(SelectedSystem.Id))
            s.DiscoveredSystems.Add(SelectedSystem.Id);
        SelectedSystem.IsDiscovered = true;
        StatusMessage = $"Arrived at {SelectedSystem.Name}.";
        await SessionPersistence.SaveAsync(Bridge, s);
        RefreshHud();
    }

    private async Task ScanAsync()
    {
        if (SelectedSystem == null) return;
        StatusMessage = $"{SelectedSystem.Name}: {SelectedSystem.StarType}, {SelectedSystem.Planets} worlds, {SelectedSystem.Economy} economy.";
        await Bridge.SendAsync("mark_system_discovered", new
        {
            username = SessionState.Instance.Username,
            system_id = SelectedSystem.Id,
        });
        SelectedSystem.IsDiscovered = true;
    }
}
