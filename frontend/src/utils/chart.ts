export function extent(values:number[]){const lo=Math.min(...values),hi=Math.max(...values),pad=Math.max((hi-lo)*.08,1);return[lo-pad,hi+pad]}
