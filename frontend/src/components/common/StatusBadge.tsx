import {statusLabels} from '../../constants/enums';
export default function StatusBadge({status}:{status:string}){return <span className={'badge '+status}>{statusLabels[status]||status}</span>}
