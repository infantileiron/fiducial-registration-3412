import json,hashlib
import numpy as np
from src.models.entities import RegistrationStudy
from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.services.geometry import rank_centered
def list_studies():
 out=[]
 for s in repo.all_rows('studies'):
  snap=s.get('snapshot') or {};item={k:v for k,v in s.items() if k!='snapshot'}
  if 'fit_ids' in snap:
   item['fit_point_count']=len(snap.get('fit_ids') or []);item['check_point_count']=len(snap.get('check_ids') or []);item['partition_mode']='by_point_ids'
  else:
   item['fit_point_count']=len(snap.get('points') or []);item['check_point_count']=0;item['partition_mode']='legacy_all_points'
  out.append(item)
 return out
def _validate_partition(points,fit_ids,check_ids):
 ids=[p['id'] for p in points];known=set(ids);fit=list(fit_ids);check=list(check_ids)
 if len(set(fit))!=len(fit) or len(set(check))!=len(check):raise ValueError('拟合点或检查点ID不能重复')
 if not set(fit)<=known or not set(check)<=known:raise ValueError('拟合点或检查点ID必须来自该数据集')
 if len(fit)<3:raise ValueError('拟合点不足：至少需要3组点对求变换')
 if set(fit)&set(check):raise ValueError('拟合点与检查点不能重叠：同一编号只能归入一类')
 if set(fit)|set(check)!=known:raise ValueError('拟合点与检查点必须覆盖全部点对，不能静默丢弃未分配编号')
 return sorted(fit),sorted(check)
def resolve_partition(points,fit_ids=None,check_ids=None):
 ids=sorted(p['id'] for p in points)
 if fit_ids is None and check_ids is None:return ids,[]
 if fit_ids is None:fit=[i for i in ids if i not in set(check_ids or [])];check=list(check_ids or [])
 elif check_ids is None:check=[i for i in ids if i not in set(fit_ids)];fit=list(fit_ids)
 else:fit,check=list(fit_ids),list(check_ids)
 return _validate_partition(points,fit,check)
def lock_snapshot(dataset,frame,threshold_mm,iterations,seed,fit_ids=None,check_ids=None):
 if frame['dataset_id']!=dataset['id']:raise ValueError('轴系声明必须属于该点对数据集')
 snapshot={'points':dataset['points'],'frame':{k:frame[k] for k in ('id','name','source_frame','target_frame','unit','axes')},'threshold_mm':threshold_mm,'iterations':iterations,'seed':seed,'convention':'target=R@source+t','dataset_name':dataset['name'],'source':dataset['source']}
 if fit_ids is None and check_ids is None:
  pass
 else:
  if fit_ids is None or check_ids is None:raise ValueError('拟合点与检查点必须同时锁定')
  fit_ids,check_ids=_validate_partition(dataset['points'],fit_ids,check_ids)
  snapshot['fit_ids']=fit_ids;snapshot['check_ids']=check_ids
  snapshot['partition']={'mode':'by_point_ids','fit_point_count':len(fit_ids),'check_point_count':len(check_ids)}
 checksum=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest();return snapshot,checksum
def create(data):
 d=repo.get('datasets',data.dataset_id);f=repo.get('frames',data.frame_id)
 if not data.fit_ids:raise ValueError('请按点对编号指定拟合点，至少3组；检查点可为空，但不能把全部点都当检查点')
 fit_ids,check_ids=resolve_partition(d['points'],data.fit_ids,data.check_ids)
 by_id={p['id']:p for p in d['points']};X=np.asarray([by_id[i]['source'] for i in fit_ids]);Y=np.asarray([by_id[i]['target'] for i in fit_ids])
 if min(rank_centered(X),rank_centered(Y))<2:raise ValueError('拟合点共线或重合，源/目标中心化rank<2，无法唯一确定刚体旋转；请调整拟合点编号')
 snapshot,checksum=lock_snapshot(d,f,data.threshold_mm,data.iterations,data.seed,fit_ids,check_ids)
 return repo.put('studies',RegistrationStudy(new_id('study'),data.name,data.dataset_id,data.frame_id,data.threshold_mm,data.iterations,data.seed,snapshot,checksum,now()))
