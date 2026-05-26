using System.Text.RegularExpressions;
using System.Windows.Input;
using GalacticFrontier.Services;

namespace GalacticFrontier.ViewModels;

public class SignupViewModel : BaseViewModel
{
    private static readonly Regex UserRe = new(@"^[A-Za-z0-9_]{3,14}$");

    private string _username = "";
    private string _password = "";
    private string _confirm = "";
    private string _title = "Commander";
    private string _error = "";
    private string _usernameHint = "";
    private bool _showPassword;

    public string Username { get => _username; set { SetProperty(ref _username, value); ValidateUsername(); } }
    public string Password { get => _password; set => SetProperty(ref _password, value); }
    public string ConfirmPassword { get => _confirm; set => SetProperty(ref _confirm, value); }
    public string CommanderTitle { get => _title; set => SetProperty(ref _title, value); }
    public string ErrorMessage { get => _error; set => SetProperty(ref _error, value); }
    public bool HasError => !string.IsNullOrEmpty(_error);
    public string UsernameHint { get => _usernameHint; set => SetProperty(ref _usernameHint, value); }
    public bool ShowPassword { get => _showPassword; set => SetProperty(ref _showPassword, value); }

    public string[] Titles { get; } = { "Admiral", "Commander", "Pilot", "Rogue" };

    public ICommand EnlistCommand { get; }
    public ICommand TogglePasswordCommand { get; }
    public ICommand BackCommand { get; }

    public SignupViewModel()
    {
        EnlistCommand = new RelayCommand(async _ => await EnlistAsync());
        TogglePasswordCommand = new RelayCommand(_ => ShowPassword = !ShowPassword);
        BackCommand = new RelayCommand(_ => NavigationService.Instance.GoToLauncher());
    }

    private void ValidateUsername()
    {
        if (string.IsNullOrWhiteSpace(Username))
            UsernameHint = "";
        else if (!UserRe.IsMatch(Username))
            UsernameHint = "3–14 alphanumeric characters";
        else if (Username.All(char.IsDigit))
            UsernameHint = "Cannot be numbers only";
        else
            UsernameHint = "✓ Valid";
    }

    private async Task EnlistAsync()
    {
        ErrorMessage = "";
        if (!UserRe.IsMatch(Username) || Username.All(char.IsDigit))
        {
            ErrorMessage = "Invalid username format.";
            return;
        }
        if (Password.Length < 8)
        {
            ErrorMessage = "Password must be at least 8 characters.";
            return;
        }
        if (Password != ConfirmPassword)
        {
            ErrorMessage = "Passwords do not match.";
            return;
        }
        try
        {
            var res = await Bridge.SendAsync("create_user", new
            {
                username = Username,
                password = Password,
                commander_title = CommanderTitle,
            });
            if (res.Value<bool>("success"))
                NavigationService.Instance.GoToLogin(Username);
            else
                ErrorMessage = res.Value<string>("error") ?? Strings.RegistrationFailed;
        }
        catch (Exception ex)
        {
            ErrorMessage = ex.Message;
        }
    }
}
