import argparse,csv,hashlib,json,os,pathlib,re,shutil,subprocess,tempfile,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent

def validate():
    d=json.loads((ROOT/'translations/zh-CN.json').read_text(encoding='utf-8'))
    j=json.loads((ROOT/'translations/VOCALOID6.ja-JP.json').read_text(encoding='utf-8'))
    e=json.loads((ROOT/'translations/en-US.json').read_text(encoding='utf-8'))
    assert len(j)==len(e)==731 and len(d)==733 and d.keys()==j.keys()|e.keys()
    for key,value in d.items():
        source=j.get(key,e.get(key))
        assert value and not re.search(r'[\u3040-\u30ff]',value),key
        assert sorted(re.findall(r'\{\d+(?:[^{}]*)\}',source))==sorted(re.findall(r'\{\d+(?:[^{}]*)\}',value)),key
        assert re.findall(r'_[A-Za-z]',source)==re.findall(r'_[A-Za-z]',value),key
        assert source.count('\n')==value.count('\n'),key
        if key.endswith('_Filter'):
            assert source.split('|')[1::2]==value.split('|')[1::2],key
        if re.match(r'https?://',source) or key.endswith('_Gesture'):
            assert source==value,key
    return d

def prepare():
    d=validate();j=json.loads((ROOT/'translations/VOCALOID6.ja-JP.json').read_text(encoding='utf8'));e=json.loads((ROOT/'translations/en-US.json').read_text(encoding='utf8'))
    for culture in ['zh-CN','ja-JP']:
        root=ET.Element('root')
        for name,value in [('resmimetype','text/microsoft-resx'),('version','2.0'),('reader','System.Resources.ResXResourceReader, System.Windows.Forms'),('writer','System.Resources.ResXResourceWriter, System.Windows.Forms')]:
            ET.SubElement(ET.SubElement(root,'resheader',name=name),'value').text=value
        for key in sorted(d):ET.SubElement(ET.SubElement(root,'data',{'name':key,'xml:space':'preserve'}),'value').text=d[key]
        ET.indent(root);ET.ElementTree(root).write(ROOT/'src'/('Strings.'+culture+'.resx'),encoding='utf-8',xml_declaration=True)
    with (ROOT/'translations/词库.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['ResourceKey','English','Japanese','Chinese','ReviewStatus']);w.writerows((k,e.get(k,''),j.get(k,''),d[k],'文本审校完成；界面待验收') for k in sorted(d))

def manifest():
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'payload').rglob('*')) if p.is_file()}
    (ROOT/'payload-manifest.json').write_text(json.dumps(files,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--dotnet',default='dotnet');a.add_argument('--validate-only',action='store_true');args=a.parse_args();prepare()
    if args.validate_only:print('733 keys validated.');raise SystemExit()
    env=os.environ.copy()
    with tempfile.TemporaryDirectory(prefix='v6cn-build-') as work:
        work=pathlib.Path(work)
        def build(project,out,*props):
            subprocess.run([args.dotnet,'build',str(ROOT/project),'-c','Release','-o',str(out),'--nologo',*props],check=True,env=env)
        for module in ['VOCALOID6','VOCALOID6Plugin']:
            out=work/module;build('src/Satellite.csproj',out,'-p:ParentName='+module)
            for culture in ['zh-CN','ja-JP']:
                dest=ROOT/'payload'/culture;dest.mkdir(parents=True,exist_ok=True);shutil.copy2(out/culture/(module+'.resources.dll'),dest)
        build('src/Hook/Hook.csproj',work/'hook');shutil.copy2(work/'hook/V6CN.StartupHook.dll',ROOT/'payload/V6CN.StartupHook.dll')
        build('src/Toolkit/Toolkit.csproj',work/'toolkit');dest=ROOT/'payload/toolkit';dest.mkdir(parents=True,exist_ok=True)
        for name in ['V6CN.Toolkit.dll','V6CN.Toolkit.deps.json','V6CN.Toolkit.runtimeconfig.json']:shutil.copy2(work/'toolkit'/name,dest/name)
    manifest();print('Candidate resources and tools built; Windows acceptance is required.')
