import random,math
import numpy as np
from src.utils import repository as repo
from src.utils.identity import now
from src.utils.security import hash_password
from src.services.statistics import analyze
from src.services.study import lock_snapshot
def demo_points():
 rng=random.Random(2405);z,y=math.radians(22),math.radians(-11);Rz=np.array([[math.cos(z),-math.sin(z),0],[math.sin(z),math.cos(z),0],[0,0,1]]);Ry=np.array([[math.cos(y),0,math.sin(y)],[0,1,0],[-math.sin(y),0,math.cos(y)]]);R=Rz@Ry;t=np.array([12.,-7.,4.5]);rows=[]
 for i in range(60):
  x=np.array([rng.uniform(-60,60),rng.uniform(-40,40),rng.uniform(-25,25)]);target=R@x+t+np.array([rng.gauss(0,.03) for _ in range(3)])
  if i<8:target+=np.array([rng.uniform(8,15),rng.uniform(-14,-8),rng.uniform(7,12)])
  rows.append({'id':f'HC{i+1:03d}','source':list(map(float,x)),'target':list(map(float,target))})
 return rows
def seed():
 repo.init_db()
 for role,name in [('admin','配准复核工程师'),('analyst','光学测量分析员'),('viewer','测量档案阅览员')]:
  email=f'{role}@haochuan.test';repo.put('users',{'id':email,'email':email,'name':name,'role':role,'password_hash':hash_password('Fiducial2026!')},insert_only=True)
 d={'id':'ds-fiducials','name':'皓川60组相机—台架标志点','source':'haochuan_fiducials_202611.csv','points':demo_points(),'created_at':now()};repo.put('datasets',d,insert_only=True)
 f={'id':'frame-camera-table','name':'相机A → 台架B / 毫米右手系','dataset_id':d['id'],'source_frame':'CAMERA-A','target_frame':'TABLE-B','unit':'mm','axes':'right-handed xyz','created_at':now()};repo.put('frames',f,insert_only=True)
 snapshot,checksum=lock_snapshot(d,f,.5,400,2405);study={'id':'study-registration','name':'十一月台架标志点稳健配准','dataset_id':d['id'],'frame_id':f['id'],'threshold_mm':.5,'iterations':400,'seed':2405,'snapshot':snapshot,'checksum':checksum,'created_at':now()};repo.put('studies',study,insert_only=True)
 repo.put('runs',{'id':'run-demo','study_id':study['id'],'status':'completed','result':analyze(snapshot,checksum),'error':'','created_at':now()},insert_only=True)
 repo.put('reviews',{'id':'review-demo','run_id':'run-demo','comment':'毫米与右手轴系锁定；全量/稳健残差、最终内点和detR核验通过。','status':'approved','reviewer':'admin@haochuan.test','created_at':now()},insert_only=True)
 repo.put('reports',{'id':'report-demo','run_id':'run-demo','review_id':'review-demo','title':'皓川光学台架刚体配准复核册','created_at':now()},insert_only=True)
 return {t:len(repo.all_rows(t)) for t in ('users','datasets','frames','studies','runs','reviews','reports')}
