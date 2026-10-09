"""Read only. Never creates a missing database. No sqlite3 CLI needed."""
from pathlib import Path
import sqlite3, argparse, json
def read_database(path):
    target=Path(path).resolve()
    if not target.is_file(): raise FileNotFoundError('数据库不存在；请核对路径并先启动服务。')
    with sqlite3.connect(target.as_uri()+'?mode=ro',uri=True) as c:
        c.row_factory=sqlite3.Row
        rows=[dict(r) for r in c.execute('SELECT id,amount_cents,date,category,note FROM expenses ORDER BY created_at')]
    return {'count':len(rows),'total_cents':sum(r['amount_cents'] for r in rows),'rows':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',default=str(Path(__file__).resolve().parent/'data/ledger.sqlite3'));a=p.parse_args()
    print(json.dumps(read_database(a.db),ensure_ascii=False,indent=2))
