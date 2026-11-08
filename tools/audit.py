import argparse,csv,hashlib,json,pathlib,sys
from extract import extract
p=argparse.ArgumentParser();p.add_argument('editor');p.add_argument('--old-csv-directory');args=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];editor=pathlib.Path(args.editor);cn=json.loads((root/'translations/zh-CN.json').read_text(encoding='utf-8'));results=[]
for module in ['VOCALOID6','VOCALOID6Plugin']:
 ja=extract(editor/'ja-JP'/(module+'.resources.dll'));en=extract(editor/(module+'.dll'))
 assert len(ja)==len(en)==731 and ja.keys()|en.keys()==cn.keys()
 assert ja==json.loads((root/'translations'/(module+'.ja-JP.json')).read_text(encoding='utf-8'))
 data={'module':module,'jaCount':len(ja),'neutralCount':len(en),'chineseCount':len(cn),'jaOnly':sorted(ja.keys()-en.keys()),'neutralOnly':sorted(en.keys()-ja.keys()),'jaFileSha256':hashlib.sha256((editor/'ja-JP'/(module+'.resources.dll')).read_bytes()).hexdigest()}
 if args.old_csv_directory:
  rows=list(csv.DictReader(open(pathlib.Path(args.old_csv_directory)/(module+'_日语资源完整清单.csv'),encoding='utf-8-sig')))
  assert len(rows)==len({x['ResourceKey'] for x in rows})==len(ja)
  assert all(x['JapaneseValue'].replace('\r\n','\n')==ja[x['ResourceKey']].replace('\r\n','\n') for x in rows)
  data['oldCsvMatch']=True
 results.append(data)
(root/'reports/resource-audit.json').write_text(json.dumps({'results':results},ensure_ascii=False,indent=2)+'\n');print('Audit passed.')
