using GalacticFrontier.Models;
using Newtonsoft.Json.Linq;

namespace GalacticFrontier.Services;

public static class SessionPersistence
{
    public static object BuildSavePayload(SessionState s)
    {
        var user = s.User;
        return new
        {
            credits = s.Credits,
            highscore = user?.Highscore ?? 0,
            selected_ship = s.SelectedShip,
            commander_title = user?.CommanderTitle ?? "Commander",
            ship_upgrades = user?.ShipUpgrades ?? new Dictionary<string, int>(),
            faction_rep = s.FactionRep,
            discovered_systems = s.DiscoveredSystems,
            session = new
            {
                current_system = s.SelectedSystemId,
                hull = s.Hull,
                max_hull = user?.Session.MaxHull ?? 100,
                fuel = s.Fuel,
                max_fuel = user?.Session.MaxFuel ?? 100,
                cargo = user?.Session.Cargo ?? new Dictionary<string, int>(),
                cargo_capacity = user?.Session.CargoCapacity ?? 20,
                day = user?.Session.Day ?? 1,
                wave = s.Wave,
            },
        };
    }

    public static async Task SaveAsync(PythonBridge bridge, SessionState s)
    {
        if (string.IsNullOrEmpty(s.Username)) return;
        await bridge.SendAsync("save_user_data", new
        {
            username = s.Username,
            data = BuildSavePayload(s),
        });
    }
}
