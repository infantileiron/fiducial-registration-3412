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
def _matrix_rows(w,method,m,partitioned=False):
 w.writerow([method,'det_R',m['det_R'],'orthogonality_error',m['orthogonality_error'],'rmse_all',m.get('rmse_all',m['rmse'])]);w.writerow(['R_11','R_12','R_13','t_mm'])
 for i in range(3):w.writerow(m['R'][i]+[m['t'][i]])
 if method=='robust':
  row=['inlier_count',m['inlier_count'],'rmse_inliers',m['rmse_inliers'],'refinement_stable',m['refinement_stable'],'best_sample_ids','|'.join(m['best_sample_ids'])]
  if partitioned:row+=['fitted_ids','|'.join(m['fitted_ids'])]
  w.writerow(row)
def _check_rows(w,label,metrics):
 if metrics is None:w.writerow([label,'unverified','未设置检查点，未做独立验证']);return
 w.writerow([label,metrics['point_count'],'rmse_mm',metrics['rmse'],'max_error_mm',metrics['max_error'],'min_error_mm',metrics['min_error'],'threshold_exceeded_count',metrics['threshold_exceeded_count'],'threshold_mm',metrics['threshold_mm']])
def _legacy(report,r):
 out=io.StringIO();w=csv.writer(out);_header(w,report,r);w.writerow([])
 for method in ['full','robust']:_matrix_rows(w,method,r[method])
 w.writerow([]);w.writerow(['id','sx_mm','sy_mm','sz_mm','tx_mm','ty_mm','tz_mm','full_residual_mm','robust_residual_mm','final_inlier'])
 for p in r['rows']:w.writerow([safe_cell(p['id'])]+p['source']+p['target']+[p['full_residual'],p['robust_residual'],p['inlier']])
 return out.getvalue()
def _partitioned(report,r):
 out=io.StringIO();w=csv.writer(out);_header(w,report,r);part=r['partition']
 w.writerow([]);w.writerow(['validation_mode','fit_points_only_with_withheld_check_points','fit_point_count',part['fit_point_count'],'check_point_count',part['check_point_count'],'check_status',part['check_status']])
 w.writerow(['fit_ids','|'.join(part['fit_ids'])]);w.writerow(['check_ids','|'.join(part['check_ids'])])
 w.writerow([]);w.writerow(['FIT / 仅拟合点求解的变换（检查点未参与）'])
 for method in ['full','robust']:_matrix_rows(w,method,r[method],True)
 w.writerow([]);w.writerow(['CHECK / 检查点独立误差（不参与拟合、内点判定或精炼）'])
 _check_rows(w,'full_holdout',r['check_metrics']['full']);_check_rows(w,'robust_holdout',r['check_metrics']['robust'])
 if r['check_metrics']['status']=='unverified':w.writerow(['note','未设置检查点：本次仅拟合点结果，未独立验证'])
 w.writerow([]);w.writerow(['id','role','sx_mm','sy_mm','sz_mm','tx_mm','ty_mm','tz_mm','full_residual_mm','robust_residual_mm','fit_inlier','check_threshold_exceeded'])
 for p in r['rows']:w.writerow([safe_cell(p['id']),p['role']]+p['source']+p['target']+[p['full_residual'],p['robust_residual'],p['inlier'],p['check_threshold_exceeded']])
 return out.getvalue()
def _header(w,report,r):
 w.writerow(['report','convention','source_frame','target_frame','unit','threshold_mm','seed','iterations','checksum']);w.writerow([safe_cell(report['title']),r['convention'],safe_cell(r['frame']['source_frame']),safe_cell(r['frame']['target_frame']),'mm',r['threshold_mm'],r['seed'],r['iterations'],r['checksum']])
def _rows_for_mode(report,r):
 return _legacy(report,r) if r.get('partition') is None else _partitioned(report,r)
def download(id):
 report=repo.get('reports',id);run=repo.get('runs',report['run_id']);r=run['result'];review=repo.get('reviews',report['review_id'])
 if review['status']!='approved':raise HTTPException(403,'复核未通过')
 body=_rows_for_mode(report,r)
 return '﻿'+body
