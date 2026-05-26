using System.Windows.Input;
using GalacticFrontier.Models;
using GalacticFrontier.Services;

namespace GalacticFrontier.ViewModels;

public class ShipSelectViewModel : BaseViewModel
{
    private ShipModel? _selected;

    public IReadOnlyList<ShipModel> Ships { get; } = new List<ShipModel>
    {
        new() { Id = "falcon", Name = "Falcon", Speed = 6, Hull = 6, Firepower = 6, Cargo = 5,
            Special = "Balanced starter hull", SilhouettePath = "M50,10 L90,70 L50,55 L10,70 Z" },
        new() { Id = "interceptor", Name = "Interceptor", Speed = 9, Hull = 4, Firepower = 7, Cargo = 3,
            Special = "Afterburner dash", SilhouettePath = "M50,5 L65,40 L50,75 L85,50 L50,35 L15,40 Z" },
        new() { Id = "dreadnought", Name = "Dreadnought", Speed = 3, Hull = 10, Firepower = 9, Cargo = 4,
            Special = "Auto-repair hull", SilhouettePath = "M50,15 L95,35 L85,80 L15,80 L5,35 Z" },
        new() { Id = "merchant", Name = "Merchant", Speed = 4, Hull = 5, Firepower = 3, Cargo = 10,
            Special = "Trade discount", SilhouettePath = "M50,20 L95,45 L80,85 L20,85 L5,45 Z" },
        new() { Id = "phantom", Name = "Phantom", Speed = 7, Hull = 5, Firepower = 6, Cargo = 5,
            Special = "Stealth cloak", SilhouettePath = "M50,8 L60,35 L90,55 L50,70 L10,55 L40,35 Z" },
    };

    public ShipModel? SelectedShip
    {
        get => _selected;
        set => SetProperty(ref _selected, value);
    }

    public ICommand SelectShipCommand { get; }
    public ICommand ConfirmCommand { get; }

    public ShipSelectViewModel()
    {
        SelectShipCommand = new RelayCommand(p =>
        {
            if (p is ShipModel s) SelectedShip = s;
        });
        ConfirmCommand = new RelayCommand(async _ => await ConfirmAsync(), _ => SelectedShip != null);
    }

    public override Task InitializeAsync(object? parameter)
    {
        SelectedShip = Ships.FirstOrDefault(s => s.Id == SessionState.Instance.SelectedShip) ?? Ships[0];
        return Task.CompletedTask;
    }

    private async Task ConfirmAsync()
    {
        if (SelectedShip == null) return;
        var user = SessionState.Instance.Username;
        var res = await Bridge.SendAsync("set_selected_ship", new { username = user, ship_id = SelectedShip.Id });
        if (res.Value<bool>("success"))
        {
            SessionState.Instance.SelectedShip = SelectedShip.Id;
            await LoadGalaxyAsync();
            NavigationService.Instance.GoToGalaxyMap();
        }
    }

    private async Task LoadGalaxyAsync()
    {
        var res = await Bridge.SendAsync("get_galaxy", new { username = SessionState.Instance.Username });
        if (!res.Value<bool>("success")) return;
        SessionState.Instance.Systems = res["systems"]!.Select(ParseSystemFromToken).ToList();
        SessionState.Instance.Lanes = res["lanes"]!.Select(l => (l[0]!.ToObject<int>(), l[1]!.ToObject<int>())).ToList();
        foreach (var s in SessionState.Instance.Systems)
            s.IsDiscovered = SessionState.Instance.DiscoveredSystems.Contains(s.Id);
    }

    internal static StarSystemModel ParseSystemFromToken(Newtonsoft.Json.Linq.JToken t)
    {
        var sys = new StarSystemModel
        {
            Id = (int)t["id"]!,
            Name = (string?)t["name"] ?? "",
            X = (double)t["x"]!,
            Y = (double)t["y"]!,
            Faction = (string?)t["faction"] ?? "",
            Economy = (string?)t["economy"] ?? "",
            StarType = (string?)t["star_type"] ?? "",
            Threat = (int)t["threat"]!,
            Planets = (int)t["planets"]!,
        };
        if (t["prices"] is Newtonsoft.Json.Linq.JObject jo)
            foreach (var p in jo.Properties())
                sys.Prices[p.Name] = (int)p.Value!;
        return sys;
    }
}
