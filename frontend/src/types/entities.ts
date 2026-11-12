export type User={email:string;name:string;role:string};export type Point={id:string;source:number[];target:number[]};
export type Dataset={id:string;name:string;source:string;point_count:number};
export type Frame={id:string;name:string;dataset_id:string;source_frame:string;target_frame:string;unit:string;axes:string};
export type Study={id:string;name:string;dataset_id:string;frame_id:string;threshold_mm:number;iterations:number;seed:number;checksum:string};
export type Fit={R:number[][];t:number[];predicted:number[][];residuals:number[];rmse:number;det_R:number;orthogonality_error:number;source_rank:number;target_rank:number;reflection_corrected:boolean;note:string};
export type Robust=Fit&{rmse_all:number;rmse_inliers:number;max_error_all:number;inlier_count:number;outlier_count:number;threshold_mm:number;iterations:number;valid_samples:number;seed:number;inlier_mask:boolean[];inlier_ids:string[];best_sample_ids:string[];fitted_ids:string[];refinement_steps:number;refinement_stable:boolean};
export type Row=Point&{full_predicted:number[];robust_predicted:number[];full_residual:number;robust_residual:number;inlier:boolean};
export type Result={rows:Row[];point_count:number;full:Fit;robust:Robust;frame:Frame;threshold_mm:number;iterations:number;seed:number;source:string;convention:string;checksum:string;limitations:string[]};
export type Run={id:string;study_id:string;status:string;result:Result;error:string};export type Review={id:string;run_id:string;comment:string;status:string;reviewer:string};export type Report={id:string;run_id:string;review_id:string;title:string};
