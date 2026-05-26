using System.Collections.Generic;
using GalacticFrontier.Models;

namespace GalacticFrontier.Services;

/// <summary>Singleton session state shared across ViewModels.</summary>
public sealed class SessionState
{
    private static readonly Lazy<SessionState> _instance = new(() => new SessionState());
    public static SessionState Instance => _instance.Value;

    public string Username { get; set; } = "";
    public string SelectedShip { get; set; } = "falcon";
    public int Credits { get; set; }
    public double Hull { get; set; } = 100;
    public int Fuel { get; set; } = 100;
    public int CargoUsed { get; set; }
    public int Wave { get; set; } = 1;
    public Dictionary<string, int> FactionRep { get; set; } = new();
    public List<int> DiscoveredSystems { get; set; } = new() { 0 };
    public UserModel? User { get; set; }
    public List<StarSystemModel> Systems { get; set; } = new();
    public List<(int A, int B)> Lanes { get; set; } = new();
    public int SelectedSystemId { get; set; }

    public void ApplyUser(UserModel user)
    {
        User = user;
        Username = user.Username;
        SelectedShip = user.SelectedShip;
        Credits = user.Credits;
        FactionRep = new Dictionary<string, int>(user.FactionRep);
        DiscoveredSystems = new List<int>(user.DiscoveredSystems);
        Hull = user.Session.Hull;
        Fuel = user.Session.Fuel;
        Wave = user.Session.Wave;
    }
}
