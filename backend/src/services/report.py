import csv,io
from fastapi import HTTPException
from src.models.entities import Report
from src.config.settings import ARTIFACT_DIR
from src.utils import repository as repo
from src.utils.identity import new_id,now
def safe_cell(v):return "'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v
def list_reports():return repo.all_rows('reports')
def create(data):
 run,review=repo.get('runs',data.run_id),repo.get('reviews',data.review_id)
 if review['status']!='approved' or review['run_id']!=run['id'] or run['status']!='completed':raise ValueError('报告必须引用该运行批准复核')
 report=repo.put('reports',Report(new_id('rpt'),data.run_id,data.review_id,data.title,now()));ARTIFACT_DIR.mkdir(parents=True,exist_ok=True);(ARTIFACT_DIR/(report['id']+'.csv')).write_text(download(report['id']),encoding='utf-8');return report
def download(id):
 report=repo.get('reports',id);run=repo.get('runs',report['run_id']);r=run['result'];review=repo.get('reviews',report['review_id'])
 if review['status']!='approved':raise HTTPException(403,'复核未通过')
 out=io.StringIO();w=csv.writer(out);w.writerow(['report','convention','source_frame','target_frame','unit','threshold_mm','seed','iterations','checksum']);w.writerow([safe_cell(report['title']),r['convention'],safe_cell(r['frame']['source_frame']),safe_cell(r['frame']['target_frame']),'mm',r['threshold_mm'],r['seed'],r['iterations'],r['checksum']]);w.writerow([])
 for method in ['full','robust']:
  m=r[method];w.writerow([method,'det_R',m['det_R'],'rmse_all',m.get('rmse_all',m['rmse'])]);w.writerow(['R_11','R_12','R_13','t_mm'])
  for i in range(3):w.writerow(m['R'][i]+[m['t'][i]])
  if method=='robust':w.writerow(['inlier_count',m['inlier_count'],'rmse_inliers',m['rmse_inliers'],'refinement_stable',m['refinement_stable'],'best_sample_ids','|'.join(m['best_sample_ids'])])
 w.writerow([]);w.writerow(['id','sx_mm','sy_mm','sz_mm','tx_mm','ty_mm','tz_mm','full_residual_mm','robust_residual_mm','final_inlier'])
 for p in r['rows']:w.writerow([safe_cell(p['id'])]+p['source']+p['target']+[p['full_residual'],p['robust_residual'],p['inlier']])
 return '\ufeff'+out.getvalue()
