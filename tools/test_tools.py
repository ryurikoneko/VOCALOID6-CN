import argparse,hashlib,json,os,pathlib,shutil,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--dotnet',required=True);p.add_argument('--source',required=True);args=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1];source=pathlib.Path(args.source).resolve();dotnet=str(pathlib.Path(args.dotnet).resolve());dll=str(root/'payload/toolkit/V6CN.Toolkit.dll');results=[]
def run(name,command,ok=True,env=None):
 r=subprocess.run([dotnet,dll,*map(str,command)],text=True,capture_output=True,env=env)
 assert (r.returncode==0)==ok,(name,r.stdout,r.stderr)
 results.append({'name':name,'status':'PASS','exitCode':r.returncode})
def hashes(path):return {p.relative_to(path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}
before=hashes(source)
with tempfile.TemporaryDirectory(prefix='v6cn-tools-test-') as folder:
 base=pathlib.Path(folder);dest=base/'isolated';run('payload_integrity',['verify'])
 run('isolated_install',['install',source,dest]);assert hashes(source)==before
 receipt=json.loads((dest/'V6CN-install.json').read_text(encoding='utf-8'));assert len(receipt['Copied'])==len(before)
 for key,value in receipt['Copied'].items():assert hashlib.sha256((dest/key).read_bytes()).hexdigest()==value
 results.append({'name':'all_copied_bytes_and_original_tree','status':'PASS','fileCount':len(before)})
 run('existing_destination_refused',['install',source,dest],False)
 run('nested_destination_refused',['install',source,source/'must-not-create'],False);assert not (source/'must-not-create').exists()
 bad=base/'bad-source';bad.mkdir();(bad/'VOCALOID6.dll').write_bytes(b'wrong version')
 run('wrong_source_refused',['install',bad,base/'wrong-copy'],False);assert not (base/'wrong-copy').exists()
 (dest/'keep-user-project.vpr').write_text('sentinel')
 hook=dest/'V6CN.StartupHook.dll';original=hook.read_bytes();hook.write_bytes(original+b'changed')
 run('modified_patch_restore_refused',['restore',dest],False);assert hook.exists();hook.write_bytes(original)
 run('restore_removes_patch_only',['restore',dest]);assert not hook.exists();assert not (dest/'zh-CN').exists();assert not (dest/'Start-Chinese.cmd').exists();assert (dest/'keep-user-project.vpr').read_text()=='sentinel'
 assert all(hashlib.sha256((dest/k).read_bytes()).hexdigest()==v for k,v in before.items());assert hashes(source)==before
 results.append({'name':'restored_copy_and_original_tree_unchanged','status':'PASS','fileCount':len(before)})
 run('repeat_restore_refused',['restore',dest],False)
 linked=base/'linked';linked.symlink_to(source,target_is_directory=True)
 run('linked_destination_parent_refused',['install',source,linked/'must-not-create'],False);assert not (source/'must-not-create').exists()
 run('linked_source_refused',['install',linked,base/'link-copy'],False);assert not (base/'link-copy').exists()
(root/'reports/tool-tests.json').write_text(json.dumps({'platform':os.name,'results':results},indent=2)+'\n')
print(len(results),'checks passed')
