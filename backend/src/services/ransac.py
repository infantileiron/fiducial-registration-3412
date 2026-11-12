import random,math
import numpy as np
from src.services.geometry import point_arrays,evaluate,rank_centered
from src.services.kabsch import kabsch
def ransac(source,target,ids=None,threshold=.5,max_iter=400,seed=2405,max_refine=10):
 X,Y=point_arrays(source,target);n=len(X);ids=[str(i) for i in range(n)] if ids is None else list(ids)
 if len(ids)!=n or len(set(ids))!=n or not all(isinstance(k,str) for k in ids):raise ValueError('点对ID必须等长唯一字符串')
 if not math.isfinite(threshold) or threshold<=0 or not isinstance(max_iter,int) or not 1<=max_iter<=2000 or not isinstance(max_refine,int) or not 1<=max_refine<=20:raise ValueError('RANSAC阈值或预算无效')
 if min(rank_centered(X),rank_centered(Y))<2:raise ValueError('点集共线或重合，不能配准')
 rng=random.Random(seed);population=sorted(range(n),key=lambda i:ids[i]);best=None;valid=0
 for iteration in range(max_iter):
  sample=sorted(rng.sample(population,3),key=lambda i:ids[i])
  try:fit=kabsch(X[sample],Y[sample])
  except ValueError:continue
  valid+=1;R=np.asarray(fit['R']);t=np.asarray(fit['t']);_,errs=evaluate(X,Y,R,t);mask=errs<=threshold;count=int(mask.sum())
  if count<3:continue
  rmse=float(np.sqrt(np.mean(errs[mask]**2)));key=(-count,rmse,tuple(ids[i] for i in sample))
  if best is None or key<best['key']:best={'key':key,'mask':mask,'sample':[ids[i] for i in sample]}
 if best is None:raise ValueError('有限RANSAC预算内未找到至少3个非共线内点')
 mask=best['mask'];stable=False;fitted_ids=[]
 for step in range(1,max_refine+1):
  fitted_ids=sorted(ids[i] for i in range(n) if mask[i]);fit=kabsch(X[mask],Y[mask]);R=np.asarray(fit['R']);t=np.asarray(fit['t']);predicted,errs=evaluate(X,Y,R,t);newmask=errs<=threshold
  if int(newmask.sum())<3 or min(rank_centered(X[newmask]),rank_centered(Y[newmask]))<2:raise ValueError('精炼后不足3个非共线内点，需复查阈值或点对')
  if np.array_equal(newmask,mask):stable=True;mask=newmask;break
  mask=newmask
 return {**fit,'fitted_point_count':fit['point_count'],'fitted_rmse':fit['rmse'],'point_count':n,'rmse':float(np.sqrt(np.mean(errs**2))),'max_error':float(np.max(errs)),'predicted':predicted.tolist(),'residuals':errs.tolist(),'rmse_all':float(np.sqrt(np.mean(errs**2))),'rmse_inliers':float(np.sqrt(np.mean(errs[mask]**2))),'max_error_all':float(np.max(errs)),'inlier_mask':mask.tolist(),'inlier_ids':sorted(ids[i] for i in range(n) if mask[i]),'inlier_count':int(mask.sum()),'outlier_count':int((~mask).sum()),'threshold_mm':threshold,'iterations':max_iter,'valid_samples':valid,'seed':seed,'best_sample_ids':best['sample'],'fitted_ids':fitted_ids,'refinement_steps':step,'refinement_stable':stable,'note':'有限随机预算不保证全局最优；精炼后按最终R/t重新评估全部残差和内点。'+('内点集合稳定' if stable else '精炼达上限，最终内点与拟合集合可能不同，请人工复核')}
