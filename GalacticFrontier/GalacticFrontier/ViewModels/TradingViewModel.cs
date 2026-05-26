using System.Windows.Input;
using GalacticFrontier.Models;
using GalacticFrontier.Services;

namespace GalacticFrontier.ViewModels;

public class TradingViewModel : BaseViewModel
{
    private static readonly Dictionary<string, string> Labels = new()
    {
        ["ore"] = "Ore", ["fuel_cells"] = "Fuel Cells", ["food"] = "Food", ["medicine"] = "Medicine",
        ["weapons"] = "Weapons", ["luxury"] = "Luxury Goods", ["tech_parts"] = "Tech Parts",
        ["contraband"] = "Contraband", ["artifacts"] = "Alien Artifacts", ["spice"] = "Spice",
        ["data_chips"] = "Data Chips", ["nanites"] = "Nanites",
    };

    private CommodityModel? _selected;
    private int _quantity = 1;
    private string _error = "";
    private string _routeHint = "";

    public List<CommodityModel> Commodities { get; } = new();
    public CommodityModel? SelectedCommodity
    {
        get => _selected;
        set
        {
            if (SetProperty(ref _selected, value))
            {
                OnPropertyChanged(nameof(SelectedName));
                OnPropertyChanged(nameof(SelectedDescription));
                OnPropertyChanged(nameof(MaxQuantity));
            }
        }
    }

    public string SelectedName => SelectedCommodity?.Name ?? "Select commodity";
    public string SelectedDescription => SelectedCommodity == null ? "" : $"Buy {SelectedCommodity.BuyPrice} CR · Sell {SelectedCommodity.SellPrice} CR";
    public int Quantity { get => _quantity; set => SetProperty(ref _quantity, Math.Max(1, value)); }
    public int MaxQuantity { get; set; } = 20;
    public string ErrorMessage { get => _error; set => SetProperty(ref _error, value); }
    public string RouteHint { get => _routeHint; set => SetProperty(ref _routeHint, value); }
    public bool ShowRouteHint => !string.IsNullOrEmpty(RouteHint);
    public string CreditsText => $"Credits: {SessionState.Instance.Credits}";
    public IEnumerable<KeyValuePair<string, int>> CargoItems =>
        SessionState.Instance.User?.Session.Cargo.Where(kv => kv.Value > 0) ?? Enumerable.Empty<KeyValuePair<string, int>>();

    public ICommand BuyCommand { get; }
    public ICommand SellCommand { get; }
    public ICommand BackCommand { get; }

    public TradingViewModel()
    {
        BuyCommand = new RelayCommand(async _ => await BuyAsync());
        SellCommand = new RelayCommand(async _ => await SellAsync());
        BackCommand = new RelayCommand(_ => NavigationService.Instance.GoToGalaxyMap());
    }

    public override Task InitializeAsync(object? parameter)
    {
        LoadCommodities();
        if (SessionState.Instance.DiscoveredSystems.Count >= 3)
            RouteHint = "Route hint: sell luxury at agricultural systems for best margin.";
        return Task.CompletedTask;
    }

    private void LoadCommodities()
    {
        Commodities.Clear();
        var sys = SessionState.Instance.Systems.FirstOrDefault(s => s.Id == SessionState.Instance.SelectedSystemId)
                  ?? SessionState.Instance.Systems.FirstOrDefault();
        if (sys == null) return;
        var cargo = SessionState.Instance.User?.Session.Cargo ?? new Dictionary<string, int>();
        var rng = new Random(sys.Id + (SessionState.Instance.User?.Session.Day ?? 1));
        foreach (var key in Labels.Keys)
        {
            var basePrice = sys.Prices.GetValueOrDefault(key, 50);
            var buy = (int)(basePrice * rng.NextDouble() * 0.15 + basePrice * 1.05);
            var sell = (int)(basePrice * rng.NextDouble() * 0.1 + basePrice * 0.92);
            Commodities.Add(new CommodityModel
            {
                Key = key,
                Name = Labels[key],
                BuyPrice = buy,
                SellPrice = sell,
                Owned = cargo.GetValueOrDefault(key, 0),
                Trend = rng.Next(3) switch { 0 => "up", 1 => "down", _ => "flat" },
            });
        }
        SelectedCommodity = Commodities.FirstOrDefault();
        OnPropertyChanged(nameof(Commodities));
        OnPropertyChanged(nameof(CreditsText));
        OnPropertyChanged(nameof(CargoItems));
    }

    private int CargoWeight()
    {
        var w = new Dictionary<string, int> { ["ore"] = 2, ["artifacts"] = 3 };
        return SessionState.Instance.User?.Session.Cargo.Sum(kv => kv.Value * w.GetValueOrDefault(kv.Key, 1)) ?? 0;
    }

    private async Task BuyAsync()
    {
        if (SelectedCommodity == null) return;
        var s = SessionState.Instance;
        var cost = SelectedCommodity.BuyPrice * Quantity;
        if (s.Credits < cost) { ErrorMessage = "Insufficient credits."; return; }
        var cap = s.User?.Session.CargoCapacity ?? 20;
        if (CargoWeight() + Quantity > cap) { ErrorMessage = "Cargo hold full."; return; }
        s.Credits -= cost;
        var cargo = s.User!.Session.Cargo;
        cargo[SelectedCommodity.Key] = cargo.GetValueOrDefault(SelectedCommodity.Key, 0) + Quantity;
        SelectedCommodity.Owned = cargo[SelectedCommodity.Key];
        s.CargoUsed = CargoWeight();
        await SessionPersistence.SaveAsync(Bridge, s);
        ErrorMessage = "";
        OnPropertyChanged(nameof(CreditsText));
        OnPropertyChanged(nameof(CargoItems));
    }

    private async Task SellAsync()
    {
        if (SelectedCommodity == null) return;
        var s = SessionState.Instance;
        var cargo = s.User!.Session.Cargo;
        var owned = cargo.GetValueOrDefault(SelectedCommodity.Key, 0);
        if (owned < Quantity) { ErrorMessage = "Not enough stock."; return; }
        s.Credits += SelectedCommodity.SellPrice * Quantity;
        cargo[SelectedCommodity.Key] = owned - Quantity;
        if (cargo[SelectedCommodity.Key] <= 0) cargo.Remove(SelectedCommodity.Key);
        SelectedCommodity.Owned = cargo.GetValueOrDefault(SelectedCommodity.Key, 0);
        s.CargoUsed = CargoWeight();
        await SessionPersistence.SaveAsync(Bridge, s);
        ErrorMessage = "";
        OnPropertyChanged(nameof(CreditsText));
        OnPropertyChanged(nameof(CargoItems));
    }
}
