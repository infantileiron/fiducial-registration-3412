import type {User} from '../types/entities';
export function savedUser():User|null {try{return JSON.parse(sessionStorage.getItem('fiducial-user')||'null')}catch{return null}}
export function saveSession(token:string,user:User){sessionStorage.setItem('fiducial-token',token);sessionStorage.setItem('fiducial-user',JSON.stringify(user))}
export function clearSession(){sessionStorage.removeItem('fiducial-token');sessionStorage.removeItem('fiducial-user')}
