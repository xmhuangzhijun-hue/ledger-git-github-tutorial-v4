import argparse,json,urllib.request,urllib.error
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8000');a=p.parse_args()
def call(method,path,data=None):
    req=urllib.request.Request(a.url+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'},method=method)
    try:
        with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
_,before=call('GET','/api/expenses')
base={'amount_cents':0,'date':'2026-10-07','category':'餐饮','note':'非法输入验收'}
for delta in [{},{'amount_cents':-1},{'amount_cents':1.2},{'amount_cents':True},{'amount_cents':100,'date':'2026-02-30'}]:
    status,_=call('POST','/api/expenses',{**base,**delta});assert status==422,(delta,status)
    print(json.dumps({'input':{**base,**delta},'HTTP':status,'result':'rejected'},ensure_ascii=False))
_,after=call('GET','/api/expenses');assert before==after,'数据发生变化，请停止操作并核对'
print(json.dumps({'unchanged':True,'records':len(after)},ensure_ascii=False))
