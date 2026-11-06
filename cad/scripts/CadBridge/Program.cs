using ACadSharp;
using ACadSharp.IO;

if (args.Length != 2)
{
    Console.Error.WriteLine("Usage: CadBridge input.dwg|dxf output.dwg|dxf (new path)");
    return 1;
}
var source = Path.GetFullPath(args[0]);
var target = Path.GetFullPath(args[1]);
string Kind(string path) => Path.GetExtension(path).ToLowerInvariant();
if (!File.Exists(source) || File.Exists(target) ||
    !new[] { ".dwg", ".dxf" }.Contains(Kind(source)) ||
    !new[] { ".dwg", ".dxf" }.Contains(Kind(target)))
{
    Console.Error.WriteLine("Input must exist, output must be new, extensions must be DWG/DXF.");
    return 1;
}
CadDocument Read(string path)
{
    if (Kind(path) == ".dwg")
    {
        using var reader = new DwgReader(path);
        reader.OnNotification += (_, e) => Console.Error.WriteLine(e.Message);
        return reader.Read();
    }
    using var dxf = new DxfReader(path);
    dxf.OnNotification += (_, e) => Console.Error.WriteLine(e.Message);
    return dxf.Read();
}
try
{
    var document = Read(source);
    Console.WriteLine($"Input model entities: {document.Entities.Count}");
    Directory.CreateDirectory(Path.GetDirectoryName(target)!);
    if (Kind(target) == ".dwg")
    {
        using var writer = new DwgWriter(target, document);
        writer.OnNotification += (_, e) => Console.Error.WriteLine(e.Message);
        writer.Write();
    }
    else
    {
        using var writer = new DxfWriter(target, document);
        writer.OnNotification += (_, e) => Console.Error.WriteLine(e.Message);
        writer.Write();
    }
    var check = Read(target);
    Console.WriteLine($"Readback model entities: {check.Entities.Count}");
    Console.WriteLine("Readback completed; inspect notifications, geometry/text comparison and preview before delivery.");
    return document.Entities.Count == check.Entities.Count ? 0 : 2;
}
catch (Exception error)
{
    Console.Error.WriteLine($"Conversion failed: {error.GetType().Name}: {error.Message}");
    Console.Error.WriteLine("Any partial output is not a deliverable; retry to a new filename after diagnosis.");
    return 1;
}
