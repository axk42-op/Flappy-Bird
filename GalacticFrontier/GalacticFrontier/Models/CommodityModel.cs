namespace GalacticFrontier.Models;

public class CommodityModel
{
    public string Key { get; set; } = "";
    public string Name { get; set; } = "";
    public int BuyPrice { get; set; }
    public int SellPrice { get; set; }
    public int Owned { get; set; }
    public string Trend { get; set; } = "flat";
}
