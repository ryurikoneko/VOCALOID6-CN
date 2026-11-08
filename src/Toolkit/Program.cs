using System.Globalization;
using System.Reflection;
using System.Runtime.Loader;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Resources;

internal static class Program
{
    static readonly JsonSerializerOptions Json = new() { WriteIndented = true };
    static readonly string[] Modules = ["VOCALOID6", "VOCALOID6Plugin"];
    static string Hash(string p) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(p))).ToLowerInvariant();
    static string Full(string p) => Path.GetFullPath(p);
    static void Write(string p, object o) => File.WriteAllText(p, JsonSerializer.Serialize(o, Json), new UTF8Encoding(false));
    static T Read<T>(string p) => JsonSerializer.Deserialize<T>(File.ReadAllText(p))!;
    static void Require(bool ok, string message) { if (!ok) throw new InvalidOperationException(message); }
    static string Package => Full(Path.Combine(AppContext.BaseDirectory, "../.."));
    public static int Main(string[] args)
    {
        try
        {
            switch (args.FirstOrDefault())
            {
                case "install": Install(args[1], args[2]); break;
                case "restore": Restore(args[1]); break;
                case "verify": VerifyPayload(); break;
                case "probe": Probe(args[1], args[2], args.Contains("--hook")); break;
                default: throw new ArgumentException("Commands: verify | install <Editor> <new destination> | restore <destination> | probe <Editor> <output.json> [--hook]");
            }
            return 0;
        }
        catch (Exception e) { Console.Error.WriteLine(e.ToString()); return 1; }
    }
    static void VerifyPayload()
    {
        foreach (var f in Read<Dictionary<string,string>>(Path.Combine(Package,"payload-manifest.json")))
            Require(Hash(Path.Combine(Package,f.Key))==f.Value,"Payload hash mismatch: "+f.Key);
        Console.WriteLine("Payload hashes verified.");
    }
    static void CheckAncestors(string path)
    {
        for(var current=new DirectoryInfo(path); current is not null; current=current.Parent)
            if(current.Exists) Require((current.Attributes&FileAttributes.ReparsePoint)==0,"Linked path ancestor detected: "+current.FullName);
    }
    static void Install(string source, string destination)
    {
        VerifyPayload(); source=Full(source); destination=Full(destination);
        CheckAncestors(source); CheckAncestors(destination);
        var comparison=OperatingSystem.IsWindows()?StringComparison.OrdinalIgnoreCase:StringComparison.Ordinal;
        Require(Directory.Exists(source),"Editor directory not found.");
        Require(!Directory.Exists(destination) && !File.Exists(destination),"Destination already exists. Choose a new directory.");
        Require(!destination.StartsWith(source+Path.DirectorySeparatorChar,comparison) && !source.StartsWith(destination+Path.DirectorySeparatorChar,comparison),"Source and destination must be separate trees.");
        var baseline=Read<Dictionary<string,string>>(Path.Combine(Package,"baseline.json"));
        foreach(var f in baseline) Require(Hash(Path.Combine(source,f.Key))==f.Value,"Source version/hash mismatch: "+f.Key);
        Require(!Directory.Exists(Path.Combine(source,"zh-CN")),"Source already contains zh-CN resources. Use an original copy.");
        var files=new List<string>();
        void Scan(string dir)
        {
            Require((File.GetAttributes(dir)&FileAttributes.ReparsePoint)==0,"Linked directories are not supported.");
            foreach(var entry in Directory.EnumerateFileSystemEntries(dir))
            {
                Require((File.GetAttributes(entry)&FileAttributes.ReparsePoint)==0,"Linked files are not supported.");
                if(Directory.Exists(entry)) Scan(entry); else files.Add(entry);
            }
        }
        Scan(source);
        Require(files.Count>0,"Source is empty.");
        Require(!File.Exists(Path.Combine(source,"V6CN.StartupHook.dll")),"Source contains an existing adapter.");
        Directory.CreateDirectory(destination);
        File.WriteAllText(Path.Combine(destination,"V6CN-INCOMPLETE.txt"),"Installation is incomplete. Original files were not modified.");
        var copied=new Dictionary<string,string>();
        var managed=new Dictionary<string,string>();
        foreach(var f in files)
        {
            var rel=Path.GetRelativePath(source,f);var target=Path.Combine(destination,rel);
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);File.Copy(f,target,false);
            var sha=Hash(f);Require(Hash(target)==sha,"Copy verification failed: "+rel);copied.Add(rel,sha);
        }
        void Add(string rel,string from)
        {
            var target=Path.Combine(destination,rel);Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(from,target,false);managed.Add(rel,Hash(target));
        }
        foreach(var n in Modules) Add(Path.Combine("zh-CN",n+".resources.dll"),Path.Combine(Package,"payload","zh-CN",n+".resources.dll"));
        Add("V6CN.StartupHook.dll",Path.Combine(Package,"payload","V6CN.StartupHook.dll"));
        var launcher=Path.Combine(destination,"Start-Chinese.cmd");
        File.Copy(Path.Combine(Package,"tools","Start-Chinese.template.cmd"),launcher,false);
        managed.Add("Start-Chinese.cmd",Hash(launcher));
        Write(Path.Combine(destination,"V6CN-install.json"),new Receipt(source,destination,copied,managed));
        File.Delete(Path.Combine(destination,"V6CN-INCOMPLETE.txt"));
        foreach(var f in baseline) Require(Hash(Path.Combine(source,f.Key))==f.Value,"Original files changed during installation.");
        Console.WriteLine("Installed isolated test copy: "+destination);
        Console.WriteLine("Start with Start-Chinese.cmd. Windows UI acceptance is required.");
    }
    static void Restore(string destination)
    {
        destination=Full(destination);
        CheckAncestors(destination);
        Require((File.GetAttributes(destination)&FileAttributes.ReparsePoint)==0,"Linked destination detected.");
        var culturePath=Path.Combine(destination,"zh-CN");
        Require(!Directory.Exists(culturePath)||(File.GetAttributes(culturePath)&FileAttributes.ReparsePoint)==0,"Linked culture directory detected.");
        var receipt=Read<Receipt>(Path.Combine(destination,"V6CN-install.json"));
        Require(Full(receipt.Destination)==destination,"Receipt path mismatch.");
        var allowed=new HashSet<string>(Modules.Select(n=>Path.Combine("zh-CN",n+".resources.dll"))) {"V6CN.StartupHook.dll","Start-Chinese.cmd"};
        Require(receipt.Managed.Keys.ToHashSet().SetEquals(allowed),"Receipt contains unexpected paths.");
        foreach(var f in receipt.Managed)
        {
            var p=Path.Combine(destination,f.Key);
            Require(!File.Exists(p) || (File.GetAttributes(p)&FileAttributes.ReparsePoint)==0,"Linked patch file detected.");
            Require(!File.Exists(p) || Hash(p)==f.Value,"Patch file was modified; restore stopped: "+f.Key);
        }
        foreach(var f in receipt.Managed) File.Delete(Path.Combine(destination,f.Key));
        var cultureDir=Path.Combine(destination,"zh-CN");
        if(Directory.Exists(cultureDir)&&!Directory.EnumerateFileSystemEntries(cultureDir).Any())Directory.Delete(cultureDir);
        File.Move(Path.Combine(destination,"V6CN-install.json"),Path.Combine(destination,"V6CN-restored-"+DateTime.UtcNow.ToString("yyyyMMddHHmmssfff")+".json"));
        Console.WriteLine("Chinese resources and adapter removed. Start VOCALOID6.exe for the original interface. The copied application and user files were retained.");
    }
    static void Probe(string editor,string output,bool hook)
    {
        editor=Full(editor);var expected=Read<Dictionary<string,string>>(Path.Combine(Package,"translations","zh-CN.json"));
        var results=new List<object>();
        foreach(var n in Modules)
        {
            var context=new AssemblyLoadContext(n,true);
            var wpf=Environment.GetEnvironmentVariable("V6CN_PROBE_WPF_ROOT");
            if(!string.IsNullOrEmpty(wpf)) context.Resolving += (c,a) => { var path=Path.Combine(wpf,a.Name+".dll"); return File.Exists(path)?c.LoadFromAssemblyPath(path):null; };
            var assembly=context.LoadFromAssemblyPath(Path.Combine(editor,n+".dll"));
            var manager=new ResourceManager("Yamaha.VOCALOID.Properties.Resources",assembly);
            var chinese=CultureInfo.GetCultureInfo("zh-CN");
            int checkedCount=0; int accessors=0;
            foreach(var entry in expected)
            {
                Require(manager.GetString(entry.Key,chinese)==entry.Value,n+" ResourceManager mismatch: "+entry.Key);
                checkedCount++;
            }
            if(hook)
            {
                CultureInfo.CurrentUICulture=CultureInfo.GetCultureInfo("en-US");
                var type=assembly.GetType("Yamaha.VOCALOID.Properties.Resources",true)!;
                Require(((CultureInfo)type.GetProperty("Culture",BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)!.GetValue(null)!).Name=="zh-CN","Adapter did not set resource culture.");
                foreach(var entry in expected)
                {
                    var property=type.GetProperty(entry.Key,BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)!;
                    if(property is null) continue;
                    Require((string)property.GetValue(null)! == entry.Value,"Accessor mismatch: "+entry.Key);
                    accessors++;
                }
            }
            var satellite=assembly.GetSatelliteAssembly(chinese);
            Require(satellite.GetName().Version==new Version(6,13,3,1),"Satellite version mismatch.");
            results.Add(new {module=n,version=assembly.GetName().Version!.ToString(),culture=satellite.GetName().CultureName,resourceCount=checkedCount,accessors,ui="NOT_TESTED"});
        }
        Write(output,new{platform=System.Runtime.InteropServices.RuntimeInformation.OSDescription,results});
        Console.WriteLine("All resource checks passed. UI and audio functions were not exercised.");
    }
    record Receipt(string Source,string Destination,Dictionary<string,string> Copied,Dictionary<string,string> Managed);
}
