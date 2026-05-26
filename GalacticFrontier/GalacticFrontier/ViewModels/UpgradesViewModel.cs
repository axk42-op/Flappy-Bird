using System.Windows.Input;
using GalacticFrontier.Models;
using GalacticFrontier.Services;

namespace GalacticFrontier.ViewModels;

public class UpgradeSlotModel
{
    public string Key { get; init; } = "";
    public string Name { get; init; } = "";
    public double OffsetX { get; init; }
    public double OffsetY { get; init; }
    public int Tier { get; set; }
    public string TierRoman => Tier switch { 0 => "0", 1 => "I", 2 => "II", 3 => "III", 4 => "IV", 5 => "V", _ => "V" };
    public int NextCost => Tier >= 5 ? 0 : Costs[Tier];
    public static readonly int[] Costs = { 500, 1200, 2800, 6000, 12000 };
}

public class UpgradesViewModel : BaseViewModel
{
    private UpgradeSlotModel? _selected;
    private string _error = "";

    public static readonly UpgradeSlotModel[] Slots =
    {
        new() { Key = "engine", Name = "Engine", OffsetX = 0, OffsetY = -120 },
        new() { Key = "hull", Name = "Hull Plating", OffsetX = -140, OffsetY = -40 },
        new() { Key = "primary", Name = "Primary Weapon", OffsetX = 140, OffsetY = -40 },
        new() { Key = "secondary", Name = "Secondary Weapon", OffsetX = 160, OffsetY = 40 },
        new() { Key = "shield", Name = "Shield Generator", OffsetX = -160, OffsetY = 40 },
        new() { Key = "scanner", Name = "Scanner Array", OffsetX = -100, OffsetY = 120 },
        new() { Key = "cargo", Name = "Cargo Expander", OffsetX = 100, OffsetY = 120 },
        new() { Key = "stealth", Name = "Stealth Module", OffsetX = 0, OffsetY = 140 },
    };

    public string CreditsText => $"Credits: {SessionState.Instance.Credits}";
    public string ShipSilhouette => SessionState.Instance.SelectedShip switch
    {
        "interceptor" => "M50,5 L65,40 L50,75 L85,50 L50,35 L15,40 Z",
        "dreadnought" => "M50,15 L95,35 L85,80 L15,80 L5,35 Z",
        "merchant" => "M50,20 L95,45 L80,85 L20,85 L5,45 Z",
        "phantom" => "M50,8 L60,35 L90,55 L50,70 L10,55 L40,35 Z",
        _ => "M50,10 L90,70 L50,55 L10,70 Z",
    };

    public UpgradeSlotModel? SelectedSlot
    {
        get => _selected;
        set
        {
            if (SetProperty(ref _selected, value))
            {
                OnPropertyChanged(nameof(DetailName));
                OnPropertyChanged(nameof(DetailDescription));
                OnPropertyChanged(nameof(CurrentStat));
                OnPropertyChanged(nameof(NextStat));
                OnPropertyChanged(nameof(UpgradeCost));
                OnPropertyChanged(nameof(CanUpgrade));
            }
        }
    }

    public string DetailName => SelectedSlot?.Name ?? "";
    public string DetailDescription => SelectedSlot == null ? "" : $"Tier {SelectedSlot.TierRoman} / V";
    public string CurrentStat => SelectedSlot == null ? "" : $"Tier {SelectedSlot.Tier}";
    public string NextStat => SelectedSlot == null || SelectedSlot.Tier >= 5 ? "MAX" : $"Tier {SelectedSlot.Tier + 1}";
    public string UpgradeCost => SelectedSlot == null ? "" : $"{SelectedSlot.NextCost} CR";
    public bool CanUpgrade => SelectedSlot != null && SelectedSlot.Tier < 5 && SessionState.Instance.Credits >= SelectedSlot.NextCost;
    public string ErrorMessage { get => _error; set => SetProperty(ref _error, value); }

    public ICommand SelectSlotCommand { get; }
    public ICommand UpgradeCommand { get; }
    public ICommand BackCommand { get; }

    public UpgradesViewModel()
    {
        SelectSlotCommand = new RelayCommand(p =>
        {
            if (p is UpgradeSlotModel s) SelectedSlot = s;
        });
        UpgradeCommand = new RelayCommand(async _ => await UpgradeAsync(), _ => CanUpgrade);
        BackCommand = new RelayCommand(_ => NavigationService.Instance.GoToGalaxyMap());
    }

    public override Task InitializeAsync(object? parameter)
    {
        var ups = SessionState.Instance.User?.ShipUpgrades ?? new Dictionary<string, int>();
        foreach (var slot in Slots)
            slot.Tier = ups.GetValueOrDefault(slot.Key, 0);
        SelectedSlot = Slots[0];
        OnPropertyChanged(nameof(CreditsText));
        return Task.CompletedTask;
    }

    private async Task UpgradeAsync()
    {
        if (SelectedSlot == null) return;
        var res = await Bridge.SendAsync("apply_upgrade", new
        {
            username = SessionState.Instance.Username,
            upgrade_key = SelectedSlot.Key,
        });
        if (res.Value<bool>("success"))
        {
            SessionState.Instance.Credits = res.Value<int>("credits");
            if (res["upgrades"] is Newtonsoft.Json.Linq.JObject jo)
            {
                foreach (var p in jo.Properties())
                {
                    var tier = (int)p.Value!;
                    SessionState.Instance.User!.ShipUpgrades[p.Name] = tier;
                    var slot = Slots.FirstOrDefault(s => s.Key == p.Name);
                    if (slot != null) slot.Tier = tier;
                }
            }
            ErrorMessage = "";
            OnPropertyChanged(nameof(CreditsText));
            OnPropertyChanged(nameof(CanUpgrade));
            OnPropertyChanged(nameof(UpgradeCost));
        }
        else
            ErrorMessage = res.Value<string>("error") ?? "Upgrade failed.";
    }
}
