namespace GalacticFrontier.Models;

public class ShipModel
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public int Speed { get; set; }
    public int Hull { get; set; }
    public int Firepower { get; set; }
    public int Cargo { get; set; }
    public string Special { get; set; } = "";
    public string SilhouettePath { get; set; } = "";
}
