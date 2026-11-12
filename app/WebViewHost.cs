using System;
using System.IO;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

internal static class WebViewHost {
    static string sdk;
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern bool SetDllDirectory(string path);
    [STAThread] static void Main(string[] args) {
        try {
            sdk=args.Length>0?args[0]:@"C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin";
            SetDllDirectory(sdk);
            AppDomain.CurrentDomain.AssemblyResolve += (sender,e) => {
                string file=Path.Combine(sdk,new AssemblyName(e.Name).Name+".dll");
                return File.Exists(file)?Assembly.LoadFrom(file):null;
            };
            Run();
        } catch(Exception e) { MessageBox.Show(e.Message,"MaintQA 실행 안내"); }
    }
    [MethodImpl(MethodImplOptions.NoInlining)] static void Run() {
        Application.EnableVisualStyles();
        var form=new Form {Text="MaintQA · 선박 정비이력",Width=1280,Height=900,MinimumSize=new System.Drawing.Size(840,640),StartPosition=FormStartPosition.CenterScreen};
        var view=new WebView2 {Dock=DockStyle.Fill};
        form.Controls.Add(view);
        form.Shown += async (s,e) => {
            try {
                var options=new CoreWebView2EnvironmentOptions("--disable-background-networking --disable-component-update --disable-sync");
                var env=await CoreWebView2Environment.CreateAsync(null,Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"runtime","webview"),options);
                await view.EnsureCoreWebView2Async(env);
                view.CoreWebView2.Settings.AreDevToolsEnabled=false;
                view.CoreWebView2.Settings.AreDefaultContextMenusEnabled=false;
                view.CoreWebView2.Settings.IsStatusBarEnabled=false;
                view.CoreWebView2.AddWebResourceRequestedFilter("*",CoreWebView2WebResourceContext.All);
                view.CoreWebView2.WebResourceRequested += (sender,request) => {
                    Uri uri;
                    if (!Uri.TryCreate(request.Request.Uri,UriKind.Absolute,out uri) || uri.Scheme!="http" || uri.Host!="127.0.0.1" || uri.Port!=8760)
                        request.Response=env.CreateWebResourceResponse(new MemoryStream(),403,"Local only","");
                };
                view.CoreWebView2.NavigationStarting += (sender,navigation) => {
                    if(!navigation.Uri.StartsWith("http://127.0.0.1:8760/",StringComparison.Ordinal)) navigation.Cancel=true;
                };
                view.CoreWebView2.NewWindowRequested += (sender,request) => request.Handled=true;
                view.Source=new Uri("http://127.0.0.1:8760/");
            } catch(Exception error) {MessageBox.Show(error.Message,"WebView2 초기화 실패");form.Close();}
        };
        Application.Run(form);
        view.Dispose();
    }
}
