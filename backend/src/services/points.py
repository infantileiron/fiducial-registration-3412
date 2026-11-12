import csv,io,re,math
from src.constants.domain import MAX_POINTS
def parse_points(text):
 reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')));fields=['id','sx','sy','sz','tx','ty','tz']
 if not reader.fieldnames or not set(fields)<=set(reader.fieldnames):raise ValueError('CSV需要id,sx,sy,sz,tx,ty,tz，单位毫米')
 rows=[];seen=set()
 for raw in reader:
  id=(raw.get('id') or '').strip()
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,30}',id) or id in seen:raise ValueError('点对ID需唯一，1—30位字母数字下划线连字符')
  try:values=[float((raw.get(k) or '').strip()) for k in fields[1:]]
  except (ValueError,TypeError):raise ValueError('每行需6个完整有限坐标，不允许空值')
  if not all(math.isfinite(v) and abs(v)<=1e6 for v in values):raise ValueError('坐标须有限且绝对值≤1e6毫米')
  rows.append({'id':id,'source':values[:3],'target':values[3:]});seen.add(id)
  if len(rows)>MAX_POINTS:raise ValueError('点对最多500组')
 if len(rows)<3:raise ValueError('至少3组点对')
 return sorted(rows,key=lambda r:r['id'])
