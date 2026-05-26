using System.Collections.Generic;

namespace GalacticFrontier.Models;

public class StarSystemModel
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public double X { get; set; }
    public double Y { get; set; }
    public string Faction { get; set; } = "";
    public string Economy { get; set; } = "";
    public string StarType { get; set; } = "";
    public int Threat { get; set; }
    public int Planets { get; set; }
    public Dictionary<string, int> Prices { get; set; } = new();
    public bool IsDiscovered { get; set; }
}
