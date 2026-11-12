using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;
class Launcher {
 [STAThread] static void Main() {
  try {
   string root=AppDomain.CurrentDomain.BaseDirectory;
   string python=Path.Combine(root,@".venv\Scripts\pythonw.exe");
   if(!File.Exists(python)) {
    python=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),@"Programs\Python\Python314\pythonw.exe");
    if(!File.Exists(python)) python="pythonw.exe";
   }
   Process.Start(new ProcessStartInfo(python,"\""+Path.Combine(root,"desktop.py")+"\"") {WorkingDirectory=root,UseShellExecute=false,CreateNoWindow=true});
  } catch(Exception e) {MessageBox.Show("Python 실행 환경을 확인하세요.\n"+e.Message,"MaintQA");}
 }
}
