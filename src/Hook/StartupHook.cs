using System.Globalization;
using System.Reflection;

public static class StartupHook
{
    private static readonly object Sync = new();
    public static void Initialize()
    {
        AppDomain.CurrentDomain.AssemblyLoad += (_, e) => Apply(e.LoadedAssembly);
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies()) Apply(assembly);
    }
    private static void Apply(Assembly assembly)
    {
        var name = assembly.GetName();
        if (name.Name is not ("VOCALOID6" or "VOCALOID6Plugin")) return;
        var root = Environment.GetEnvironmentVariable("V6CN_TARGET_ROOT");
        if (string.IsNullOrEmpty(root)) return;
        var expected = Path.Combine(Path.GetFullPath(root), name.Name + ".dll");
        if (!string.Equals(Path.GetFullPath(assembly.Location), expected,
            OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal)) return;
        if (name.Version != new Version(6, 13, 3, 1)) throw new InvalidOperationException("V6CN: Unsupported assembly version.");
        var resourceType = assembly.GetType("Yamaha.VOCALOID.Properties.Resources", true)!;
        var culture = resourceType.GetProperty("Culture", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)!;
        culture.SetValue(null, CultureInfo.GetCultureInfo("zh-CN"));
        var manager = (System.Resources.ResourceManager)resourceType.GetProperty("ResourceManager", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)!.GetValue(null)!;
        if (manager.GetString("Button_Cancel", CultureInfo.GetCultureInfo("zh-CN")) != "取消")
            throw new InvalidOperationException("V6CN: Chinese satellite assembly was not loaded.");
        lock (Sync)
        {
            var log = Environment.GetEnvironmentVariable("V6CN_LOG");
            if (!string.IsNullOrEmpty(log)) File.AppendAllText(log,
                $"{DateTimeOffset.UtcNow:O} APPLIED {name.Name} {name.Version} zh-CN{Environment.NewLine}");
        }
    }
}
