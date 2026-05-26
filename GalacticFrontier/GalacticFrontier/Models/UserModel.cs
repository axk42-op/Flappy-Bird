using System.Collections.Generic;

namespace GalacticFrontier.Models;

public class UserModel
{
    public string Username { get; set; } = "";
    public int Credits { get; set; }
    public int Highscore { get; set; }
    public string SelectedShip { get; set; } = "falcon";
    public string CommanderTitle { get; set; } = "Commander";
    public Dictionary<string, int> ShipUpgrades { get; set; } = new();
    public Dictionary<string, int> FactionRep { get; set; } = new();
    public List<int> DiscoveredSystems { get; set; } = new();
    public SessionModel Session { get; set; } = new();
}

public class SessionModel
{
    public int CurrentSystem { get; set; }
    public double Hull { get; set; } = 100;
    public double MaxHull { get; set; } = 100;
    public int Fuel { get; set; } = 100;
    public int MaxFuel { get; set; } = 100;
    public int CargoCapacity { get; set; } = 20;
    public Dictionary<string, int> Cargo { get; set; } = new();
    public int Day { get; set; } = 1;
    public int Wave { get; set; } = 1;
}
