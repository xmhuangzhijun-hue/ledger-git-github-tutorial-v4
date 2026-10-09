"""Episode 2: a loopback-only shared teaching ledger, without accounts."""
from pathlib import Path
import argparse, os, sqlite3, uuid
from datetime import date, datetime, timezone
from typing import Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('LEDGER_DB',str(ROOT/'data/ledger.sqlite3'))).resolve()
def connect():
    conn=sqlite3.connect(DB,timeout=5)
    conn.row_factory=sqlite3.Row
    return conn
@asynccontextmanager
async def lifespan(app):
    DB.parent.mkdir(parents=True,exist_ok=True)
    with connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS expenses (id TEXT PRIMARY KEY, amount_cents INTEGER NOT NULL CHECK(amount_cents>0), date TEXT NOT NULL, category TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)')
    yield
app=FastAPI(title='随手账 · 第二集',lifespan=lifespan)
class Expense(BaseModel):
    model_config=ConfigDict(extra='forbid')
    amount_cents: StrictInt=Field(gt=0,le=999999999)
    date: str
    category: Literal['餐饮','交通','购物','居家','其他']
    note: str=Field(default='',max_length=60)
    @field_validator('date')
    @classmethod
    def day(cls,value):
        if len(value)!=10 or date.fromisoformat(value).isoformat()!=value:
            raise ValueError('日期须为有效的YYYY-MM-DD')
        return value
@app.get('/')
def home(): return FileResponse(ROOT/'index.html')
@app.get('/legacy')
def legacy(): return FileResponse(ROOT/'legacy.html')
@app.get('/api/expenses')
def listing():
    with connect() as c: return [dict(r) for r in c.execute('SELECT * FROM expenses ORDER BY date DESC, created_at DESC')]
@app.post('/api/expenses',status_code=201)
def create(x:Expense):
    now=datetime.now(timezone.utc).isoformat(); ident=str(uuid.uuid4())
    with connect() as c:
        c.execute('INSERT INTO expenses VALUES (?,?,?,?,?,?,?)',(ident,x.amount_cents,x.date,x.category,x.note,now,now))
        row=dict(c.execute('SELECT * FROM expenses WHERE id=?',(ident,)).fetchone())
    return row
@app.patch('/api/expenses/{ident}')
def edit(ident:str,x:Expense):
    with connect() as c:
        if not c.execute('SELECT id FROM expenses WHERE id=?',(ident,)).fetchone():raise HTTPException(404,'记录不存在')
        c.execute('UPDATE expenses SET amount_cents=?,date=?,category=?,note=?,updated_at=? WHERE id=?',(x.amount_cents,x.date,x.category,x.note,datetime.now(timezone.utc).isoformat(),ident))
        row=dict(c.execute('SELECT * FROM expenses WHERE id=?',(ident,)).fetchone())
    return row
@app.delete('/api/expenses/{ident}',status_code=204)
def delete(ident:str):
    with connect() as c:
        if c.execute('DELETE FROM expenses WHERE id=?',(ident,)).rowcount==0:raise HTTPException(404,'记录不存在')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8000);args=parser.parse_args()
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=args.port)
