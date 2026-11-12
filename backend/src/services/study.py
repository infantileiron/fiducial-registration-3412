import json,hashlib
from src.models.entities import RegistrationStudy
from src.utils import repository as repo
from src.utils.identity import new_id,now
def list_studies():return [{k:v for k,v in s.items() if k!='snapshot'} for s in repo.all_rows('studies')]
def lock_snapshot(dataset,frame,threshold_mm,iterations,seed):
 if frame['dataset_id']!=dataset['id']:raise ValueError('轴系声明必须属于该点对数据集')
 snapshot={'points':dataset['points'],'frame':{k:frame[k] for k in ('id','name','source_frame','target_frame','unit','axes')},'threshold_mm':threshold_mm,'iterations':iterations,'seed':seed,'convention':'target=R@source+t','dataset_name':dataset['name'],'source':dataset['source']};checksum=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest();return snapshot,checksum
def create(data):
 d=repo.get('datasets',data.dataset_id);f=repo.get('frames',data.frame_id);snapshot,checksum=lock_snapshot(d,f,data.threshold_mm,data.iterations,data.seed)
 return repo.put('studies',RegistrationStudy(new_id('study'),data.name,data.dataset_id,data.frame_id,data.threshold_mm,data.iterations,data.seed,snapshot,checksum,now()))
