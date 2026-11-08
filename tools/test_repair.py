import argparse,hashlib,json,os,pathlib,shutil,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--dotnet',required=True);p.add_argument('--powershell',required=True);p.add_argument('--source',required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[1];dotnet=str(pathlib.Path(a.dotnet).resolve());pwsh=str(pathlib.Path(a.powershell).resolve());source=pathlib.Path(a.source).resolve();results=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(command,ok=True):
 result=subprocess.run(list(map(str,command)),capture_output=True,text=True)
 assert (result.returncode==0)==ok,result.stdout+result.stderr
 return result
with tempfile.TemporaryDirectory(prefix='v6cn-recovery-test-') as work:
 work=pathlib.Path(work);dest=work/'Editor'
 run([dotnet,r/'payload/toolkit/V6CN.Toolkit.dll','install',source,dest]);receipt=json.loads((dest/'V6CN-install.json').read_text());copied=receipt['Copied']
 def repair(package=r,ok=True):return run([pwsh,'-NoLogo','-NoProfile','-File',package/'Repair-Launcher.ps1','-InstallDir',dest,'-NoDesktopShortcut'],ok)
 def check():
  m=json.loads((r/'repair-payload.json').read_text());state=json.loads((dest/'V6CN-install.json').read_text())
  for name,value in m.items():assert sha(dest/name)==value;assert state['Managed'][name.replace('/',os.sep)]==value
  assert (dest/'Start-Chinese.cmd').read_bytes()==(r/'tools/Start-Chinese.template.cmd').read_bytes()
  assert all(sha(dest/name)==value for name,value in copied.items())
 (dest/'zh-CN/VOCALOID6.resources.dll').unlink();repair();check();results.append('missing_editor_satellite_restored')
 shutil.rmtree(dest/'zh-CN');(dest/'V6CN.StartupHook.dll').unlink();(dest/'Start-Chinese.cmd').unlink();repair();check();results.append('missing_satellite_directory_hook_and_launcher_restored')
 (dest/'zh-CN/VOCALOID6.resources.dll').write_bytes(b'damaged-resource');repair();check()
 assert any(p.read_bytes()==b'damaged-resource' for p in (dest/'V6CN-launcher-backups').glob('*/zh-CN/VOCALOID6.resources.dll'))
 results.append('damaged_satellite_backed_up_and_replaced')
 bad=work/'damaged-package';bad.mkdir();shutil.copy2(r/'Repair-Launcher.ps1',bad);shutil.copy2(r/'repair-payload.json',bad);shutil.copytree(r/'tools',bad/'tools',ignore=shutil.ignore_patterns('__pycache__'))
 for name in json.loads((r/'repair-payload.json').read_text()):
  dst=bad/'payload'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/'payload'/name,dst)
 (bad/'payload/V6CN.StartupHook.dll').write_bytes(b'damaged-package')
 before={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()};repair(bad,False)
 after={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()};assert before==after;results.append('damaged_package_refused_before_mutation')
 run([dotnet,r/'payload/toolkit/V6CN.Toolkit.dll','restore',dest]);assert not (dest/'zh-CN').exists();assert all(sha(dest/k)==v for k,v in copied.items());results.append('restore_accepted_repaired_receipt')
(r/'reports/resource-recovery-tests.json').write_text(json.dumps({'platform':os.name,'tests':[{'name':n,'status':'PASS'} for n in results],'originalCopiedFilesUnchanged':len(copied),'windowsCmdAndShortcut':'NOT_TESTED'},indent=2)+'\n')
print(len(results),'resource recovery checks passed; original copied files preserved:',len(copied))
