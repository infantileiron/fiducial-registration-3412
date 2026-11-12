import numpy as np
from src.services.kabsch import kabsch
from src.services.ransac import ransac
from src.services.geometry import evaluate,rank_centered

def _legacy(snapshot,checksum):
 points=snapshot['points'];X=[p['source'] for p in points];Y=[p['target'] for p in points];ids=[p['id'] for p in points];full=kabsch(X,Y);robust=ransac(X,Y,ids,snapshot['threshold_mm'],snapshot['iterations'],snapshot['seed']);rows=[]  # 历史快照无划分：沿用升级前口径，全部点对同时拟合与判内点
 for i,p in enumerate(points):rows.append({**p,'full_predicted':full['predicted'][i],'robust_predicted':robust['predicted'][i],'full_residual':full['residuals'][i],'robust_residual':robust['residuals'][i],'inlier':robust['inlier_mask'][i]})
 return {'rows':rows,'point_count':len(points),'full':full,'robust':robust,'frame':snapshot['frame'],'threshold_mm':snapshot['threshold_mm'],'iterations':snapshot['iterations'],'seed':snapshot['seed'],'source':snapshot['source'],'convention':snapshot['convention'],'checksum':checksum,'limitations':['y=R*x+t，全部欧氏残差为毫米；proper rotation，不拟合缩放或镜像','RANSAC有限预算不保证全局最优；最终内点由精炼后的模型重新评估','平面rank2可用，但平面镜像可能与空间旋转不可区分','模拟光学点对，不替代真实设备标定或精度保证']}

def _partition(snapshot):
 fit_ids=[str(i) for i in snapshot['fit_ids']];check_ids=[str(i) for i in snapshot['check_ids']];ids=[p['id'] for p in snapshot['points']]
 if len(fit_ids)!=len(set(fit_ids)) or len(check_ids)!=len(set(check_ids)):raise ValueError('拟合点或检查点ID不能重复')
 if not set(fit_ids)<=set(ids) or not set(check_ids)<=set(ids):raise ValueError('快照中的拟合点或检查点ID不属于点对数据')
 if set(fit_ids)&set(check_ids):raise ValueError('拟合点与检查点不能重叠，检查点必须未参与拟合')
 if set(fit_ids)|set(check_ids)!=set(ids):raise ValueError('快照中的拟合点与检查点必须覆盖全部点对')
 if len(fit_ids)<3:raise ValueError('拟合点不足：至少3组点对参与求变换')
 return sorted(fit_ids),sorted(check_ids)

def _residual_metrics(errs,threshold_mm):
 if len(errs)==0:return None
 return {'point_count':int(len(errs)),'rmse':float(np.sqrt(np.mean(errs**2))),'max_error':float(np.max(errs)),'min_error':float(np.min(errs)),'threshold_mm':threshold_mm,'threshold_exceeded_count':int((errs>threshold_mm).sum())}

def _partitioned(snapshot,checksum):
 fit_ids,check_ids=_partition(snapshot);by_id={p['id']:p for p in snapshot['points']};fit_points=[by_id[i] for i in fit_ids];check_points=[by_id[i] for i in check_ids]
 Xf=[p['source'] for p in fit_points];Yf=[p['target'] for p in fit_points]
 if min(rank_centered(np.asarray(Xf)),rank_centered(np.asarray(Yf)))<2:raise ValueError('拟合点共线或重合，无法唯一求刚体变换；请调整拟合点编号划分')
 try:
  full=kabsch(Xf,Yf);robust=ransac(Xf,Yf,fit_ids,snapshot['threshold_mm'],snapshot['iterations'],snapshot['seed'])
 except ValueError as exc:
  raise ValueError('拟合点无法配准：'+str(exc))
 threshold_mm=snapshot['threshold_mm']
 if check_points:
  Xc=np.asarray([p['source'] for p in check_points],dtype=np.float64);Yc=np.asarray([p['target'] for p in check_points],dtype=np.float64)
  check_full_pred,check_full_err=evaluate(Xc,Yc,np.asarray(full['R']),np.asarray(full['t']))
  check_robust_pred,check_robust_err=evaluate(Xc,Yc,np.asarray(robust['R']),np.asarray(robust['t']))
  check={'status':'verified','point_count':len(check_points),'ids':check_ids,'full':_residual_metrics(check_full_err,threshold_mm),'robust':_residual_metrics(check_robust_err,threshold_mm)}
 else:
  check_full_pred=check_robust_pred=None;check_full_err=check_robust_err=None
  check={'status':'unverified','point_count':0,'ids':[],'full':None,'robust':None,'note':'未设置检查点，未做独立验证；不得以拟合点残差宣称泛化精度'}
 fit_index={pid:i for i,pid in enumerate(fit_ids)};check_index={pid:i for i,pid in enumerate(check_ids)};inlier_set=set(robust['inlier_ids']);rows=[]
 for p in snapshot['points']:
  if p['id'] in fit_index:
   i=fit_index[p['id']]
   rows.append({**p,'role':'fit','full_predicted':full['predicted'][i],'robust_predicted':robust['predicted'][i],'full_residual':full['residuals'][i],'robust_residual':robust['residuals'][i],'inlier':p['id'] in inlier_set,'check_threshold_exceeded':None})
  else:
   j=check_index[p['id']]
   rows.append({**p,'role':'check','full_predicted':check_full_pred[j].tolist(),'robust_predicted':check_robust_pred[j].tolist(),'full_residual':float(check_full_err[j]),'robust_residual':float(check_robust_err[j]),'inlier':None,'check_threshold_exceeded':bool(check_robust_err[j]>threshold_mm)})
 fit_metrics={'point_count':len(fit_ids),'full':{'point_count':len(fit_ids),'rmse':full['rmse'],'max_error':full['max_error'],'threshold_mm':threshold_mm},'robust':{'point_count':len(fit_ids),'rmse_all':robust['rmse_all'],'rmse_inliers':robust['rmse_inliers'],'inlier_count':robust['inlier_count'],'outlier_count':robust['outlier_count'],'threshold_mm':threshold_mm}}
 limitations=['y=R*x+t，全部欧氏残差为毫米；proper rotation，不拟合缩放或镜像','两种变换只使用拟合点求解；检查点不参与拟合、内点判定或精炼，仅用最终R/t独立计算误差','无检查点时为未验证状态，不能以拟合点内点RMSE宣称全部点或泛化精度','RANSAC有限预算不保证全局最优；最终内点由精炼后的模型重新评估','平面rank2可用，但平面镜像可能与空间旋转不可区分','模拟光学点对，不替代真实设备标定或精度保证']
 return {'rows':rows,'point_count':len(snapshot['points']),'partition':{'mode':'by_point_ids','fit_ids':fit_ids,'check_ids':check_ids,'fit_point_count':len(fit_ids),'check_point_count':len(check_ids),'check_status':check['status']},'fit_metrics':fit_metrics,'check_metrics':check,'full':full,'robust':robust,'frame':snapshot['frame'],'threshold_mm':threshold_mm,'iterations':snapshot['iterations'],'seed':snapshot['seed'],'source':snapshot['source'],'convention':snapshot['convention'],'checksum':checksum,'limitations':limitations}

def analyze(snapshot,checksum):
 if snapshot.get('fit_ids') is not None or snapshot.get('check_ids') is not None:
  return _partitioned(snapshot,checksum)
 return _legacy(snapshot,checksum)
