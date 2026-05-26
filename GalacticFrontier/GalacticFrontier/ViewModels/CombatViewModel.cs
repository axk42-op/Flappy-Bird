using System.Windows.Input;
using GalacticFrontier.Services;

namespace GalacticFrontier.ViewModels;

public class CombatEntity
{
    public double X, Y, Vx, Vy, Angle;
    public double Hull, MaxHull;
    public bool IsPlayer;
    public bool Alive = true;
    public bool IsBoss;
}

public class CombatProjectile
{
    public double X, Y, Vx, Vy;
    public bool Alive = true;
    public bool PlayerOwned;
}

public class CombatViewModel : BaseViewModel
{
    private readonly Random _rng = new();
    public CombatEntity Player { get; } = new() { IsPlayer = true, MaxHull = 100, Hull = 100 };
    public List<CombatEntity> Enemies { get; } = new();
    public List<CombatProjectile> Projectiles { get; } = new();
    private bool _combatEnded;
    private bool _showSummary;
    private int _score;
    private int _kills;
    private string _summaryText = "";

    public bool CombatEnded { get => _combatEnded; private set => SetProperty(ref _combatEnded, value); }
    public bool ShowSummary { get => _showSummary; private set => SetProperty(ref _showSummary, value); }
    public int Score { get => _score; private set => SetProperty(ref _score, value); }
    public int Kills { get => _kills; private set => SetProperty(ref _kills, value); }
    public string SummaryText { get => _summaryText; private set => SetProperty(ref _summaryText, value); }
    public double Shield { get; set; } = 50;
    public double MaxShield { get; set; } = 50;
    public bool ShowBossBar { get; private set; }
    public double BossHpPercent { get; private set; }
    public string HudHull => $"Hull {Player.Hull:F0}/{Player.MaxHull:F0}";
    public string HudShield => $"Shield {Shield:F0}/{MaxShield:F0}";
    public string HudEnemies => $"Hostiles: {Enemies.Count(e => e.Alive)}";
    public string WeaponInfo => "Primary: LASER | Secondary: MISSILE";

    private bool _w, _a, _s, _d;
    private double _lastTick;
    public double PlayWidth { get; set; } = 1280;
    public double PlayHeight { get; set; } = 720;

    public ICommand BackCommand { get; }
    public ICommand ReturnCommand { get; }

    public CombatViewModel()
    {
        BackCommand = new RelayCommand(_ => { if (!CombatEnded) _ = FinishCombatAsync(false); });
        ReturnCommand = new RelayCommand(async _ =>
        {
            await SessionPersistence.SaveAsync(Bridge, SessionState.Instance);
            NavigationService.Instance.GoToGalaxyMap();
        });
    }

    public override Task InitializeAsync(object? parameter)
    {
        var sess = SessionState.Instance;
        Player.Hull = sess.Hull;
        Player.MaxHull = sess.User?.Session.MaxHull ?? 100;
        Player.X = PlayWidth / 2;
        Player.Y = PlayHeight / 2;
        SpawnWave();
        CombatEnded = false;
        ShowSummary = false;
        Score = 0;
        Kills = 0;
        _lastTick = 0;
        return Task.CompletedTask;
    }

    public void SetKey(string key, bool down)
    {
        switch (key.ToUpperInvariant())
        {
            case "W": _w = down; break;
            case "A": _a = down; break;
            case "S": _s = down; break;
            case "D": _d = down; break;
        }
    }

    public void AimAt(double mx, double my) =>
        Player.Angle = Math.Atan2(my - Player.Y, mx - Player.X);

    public void FirePrimary()
    {
        if (CombatEnded) return;
        var spd = 12.0;
        Projectiles.Add(new CombatProjectile
        {
            X = Player.X, Y = Player.Y,
            Vx = Math.Cos(Player.Angle) * spd,
            Vy = Math.Sin(Player.Angle) * spd,
            PlayerOwned = true,
        });
    }

    public void FireSecondary()
    {
        if (CombatEnded) return;
        for (var i = -1; i <= 1; i++)
        {
            var a = Player.Angle + i * 0.15;
            Projectiles.Add(new CombatProjectile
            {
                X = Player.X, Y = Player.Y,
                Vx = Math.Cos(a) * 8,
                Vy = Math.Sin(a) * 8,
                PlayerOwned = true,
            });
        }
    }

    public void UpdateFrame(double timestamp)
    {
        if (CombatEnded) return;
        if (_lastTick <= 0) { _lastTick = timestamp; return; }
        var dt = Math.Min(0.05, (timestamp - _lastTick) / 1000.0);
        _lastTick = timestamp;

        var speed = 220.0;
        if (_w) Player.Vy = -speed;
        else if (_s) Player.Vy = speed;
        else Player.Vy *= 0.85;
        if (_a) Player.Vx = -speed;
        else if (_d) Player.Vx = speed;
        else Player.Vx *= 0.85;

        Player.X = Math.Clamp(Player.X + Player.Vx * dt, 20, PlayWidth - 20);
        Player.Y = Math.Clamp(Player.Y + Player.Vy * dt, 20, PlayHeight - 20);

        foreach (var e in Enemies.Where(x => x.Alive))
        {
            var dx = Player.X - e.X;
            var dy = Player.Y - e.Y;
            var len = Math.Sqrt(dx * dx + dy * dy) + 0.001;
            e.X += dx / len * 80 * dt;
            e.Y += dy / len * 80 * dt;
            if (len < 40 && _rng.NextDouble() < 0.02 * dt * 60)
            {
                if (Shield > 0) Shield = Math.Max(0, Shield - 5);
                else Player.Hull -= 8 * dt * 60;
            }
        }

        foreach (var p in Projectiles.Where(x => x.Alive).ToList())
        {
            p.X += p.Vx * dt * 60;
            p.Y += p.Vy * dt * 60;
            if (p.X < -20 || p.X > PlayWidth + 20 || p.Y < -20 || p.Y > PlayHeight + 20)
                p.Alive = false;
            if (p.PlayerOwned)
            {
                foreach (var e in Enemies.Where(x => x.Alive))
                {
                    var d = Math.Sqrt((p.X - e.X) * (p.X - e.X) + (p.Y - e.Y) * (p.Y - e.Y));
                    if (d < 22)
                    {
                        e.Hull -= 25;
                        p.Alive = false;
                        if (e.Hull <= 0)
                        {
                            e.Alive = false;
                            Kills++;
                            Score += e.IsBoss ? 2000 : 150;
                        }
                        break;
                    }
                }
            }
        }

        if (Player.Hull <= 0)
            _ = FinishCombatAsync(false);
        else if (Enemies.All(e => !e.Alive))
            _ = FinishCombatAsync(true);

        OnPropertyChanged(nameof(HudHull));
        OnPropertyChanged(nameof(HudShield));
        OnPropertyChanged(nameof(HudEnemies));
        OnPropertyChanged(nameof(BossHpPercent));
    }

    private void SpawnWave()
    {
        Enemies.Clear();
        var count = 4 + SessionState.Instance.Wave;
        for (var i = 0; i < count; i++)
        {
            Enemies.Add(new CombatEntity
            {
                X = _rng.Next(80, (int)PlayWidth - 80),
                Y = _rng.Next(80, (int)PlayHeight - 80),
                Hull = 40 + SessionState.Instance.Wave * 10,
                MaxHull = 40 + SessionState.Instance.Wave * 10,
            });
        }
        if (SessionState.Instance.Wave % 3 == 0)
        {
            var boss = new CombatEntity
            {
                X = PlayWidth / 2, Y = 120, Hull = 300, MaxHull = 300, IsBoss = true,
            };
            Enemies.Add(boss);
            ShowBossBar = true;
            BossHpPercent = 100;
        }
        else ShowBossBar = false;
    }

    private async Task FinishCombatAsync(bool victory)
    {
        if (CombatEnded) return;
        CombatEnded = true;
        ShowSummary = true;
        SummaryText = victory
            ? $"Victory — Score {Score} · Kills {Kills}"
            : "Hull breached — retreating.";
        SessionState.Instance.Hull = Math.Max(0, Player.Hull);
        OnPropertyChanged(nameof(ShowSummary));
        OnPropertyChanged(nameof(SummaryText));
        if (victory)
        {
            SessionState.Instance.Wave++;
            var reward = Score / 10;
            await Bridge.SendAsync("add_credits", new { username = SessionState.Instance.Username, amount = reward });
            var res = await Bridge.SendAsync("get_user_data", new { username = SessionState.Instance.Username });
            if (res.Value<bool>("success"))
                SessionState.Instance.Credits = res["data"]!.Value<int>("credits");
            await Bridge.SendAsync("update_highscore", new { username = SessionState.Instance.Username, score = Score });
        }
        await SessionPersistence.SaveAsync(Bridge, SessionState.Instance);
    }
}
