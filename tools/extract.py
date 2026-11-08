import argparse, csv, io, json, pathlib, struct, logging
import dnfile
logging.disable(logging.CRITICAL)
def resources(data):
    f=io.BytesIO(data)
    def i32(): return struct.unpack('<i',f.read(4))[0]
    def seven():
        n=0
        for shift in range(0,35,7):
            b=f.read(1)[0];n|=(b&127)<<shift
            if b<128:return n
        raise ValueError('Invalid 7-bit integer')
    def string(enc='utf-8'):return f.read(seven()).decode(enc)
    assert f.read(4)==b'\xce\xca\xef\xbe'
    header=i32();size=i32();f.seek(size,1)
    assert i32()==2
    count=i32();types=i32()
    for _ in range(types):string()
    f.seek((-f.tell())%8,1);f.seek(count*4,1)
    offsets=[i32() for _ in range(count)];data_start=i32();name_start=f.tell();out={}
    for off in offsets:
        f.seek(name_start+off);name=string('utf-16-le');value_offset=i32();f.seek(data_start+value_offset)
        assert seven()==1, name
        value=string();assert name not in out,name;out[name]=value
    assert len(out)==count
    return dict(sorted(out.items()))
def extract(path):
    p=dnfile.dnPE(str(path));out={}
    for res in p.net.resources:
        if str(res.name).startswith('Yamaha.VOCALOID.Properties.Resources'):
            out=resources(res.data._data)
    assert out
    return out
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('editor');a.add_argument('output');args=a.parse_args();dest=pathlib.Path(args.output);dest.mkdir(parents=True,exist_ok=True)
    for name in ['VOCALOID6','VOCALOID6Plugin']:
        out=extract(pathlib.Path(args.editor)/'ja-JP'/(name+'.resources.dll'))
        (dest/(name+'.ja-JP.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(name,len(out))
