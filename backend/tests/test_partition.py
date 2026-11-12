import math, random
import numpy as np
import pytest
from fastapi import HTTPException

from src.services.study import lock_snapshot, resolve_partition
from src.services.statistics import analyze
from src.services import report as report_service
from src.services import study as study_service
from src.utils import repository as repo


def _make_points(count=60):
    rng = random.Random(2405)
    z, y = math.radians(22), math.radians(-11)
    Rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    R = Rz @ Ry
    t = np.array([12., -7., 4.5])
    rows = []
    for i in range(count):
        x = np.array([rng.uniform(-60, 60), rng.uniform(-40, 40), rng.uniform(-25, 25)])
        target = R @ x + t + np.array([rng.gauss(0, .03) for _ in range(3)])
        if i < 8:
            target += np.array([rng.uniform(8, 15), rng.uniform(-14, -8), rng.uniform(7, 12)])
        rows.append({'id': f'P{i + 1:03d}', 'source': list(map(float, x)), 'target': list(map(float, target))})
    return rows


def _dataset(points, id='ds-test'):
    return {'id': id, 'name': 'n', 'source': 's', 'points': points}


def _frame(dataset_id='ds-test'):
    return {'id': 'f', 'dataset_id': dataset_id, 'name': 'f', 'source_frame': 'A', 'target_frame': 'B', 'unit': 'mm', 'axes': 'right-handed xyz'}


def test_partition_required_and_covers_all_ids():
    points = _make_points(5)
    with pytest.raises(ValueError):
        resolve_partition(points, ['P001', 'P002'], ['P003'])
    with pytest.raises(ValueError, match='至少需要3组'):
        resolve_partition(points, ['P001', 'P002'], ['P003', 'P004', 'P005'])
    with pytest.raises(ValueError, match='重叠'):
        resolve_partition(points, ['P001', 'P002', 'P003'], ['P001', 'P004', 'P005'])
    with pytest.raises(ValueError, match='来自该数据集'):
        resolve_partition(points, ['P001', 'P002', 'PXXX'], ['P004', 'P005'])
    assert resolve_partition(points, ['P001', 'P002', 'P003'], ['P004', 'P005']) == (['P001', 'P002', 'P003'], ['P004', 'P005'])
    assert resolve_partition(points, ['P003', 'P001', 'P002'], ['P005', 'P004']) == (['P001', 'P002', 'P003'], ['P004', 'P005'])
    with pytest.raises(ValueError, match='覆盖全部点对'):
        resolve_partition(points, ['P001', 'P002', 'P003'], [])
    # omitted check_ids means derive as the remaining IDs
    assert resolve_partition(points, ['P001', 'P002', 'P003'], None) == (['P001', 'P002', 'P003'], ['P004', 'P005'])
    # omitted fit_ids means derive as the complement
    assert resolve_partition(points, None, ['P004', 'P005']) == (['P001', 'P002', 'P003'], ['P004', 'P005'])


def test_fit_points_collinear_fails_at_lock_and_analysis(monkeypatch):
    points = [{'id': f'C{i:03d}', 'source': [float(i), 0., 0.], 'target': [float(i), 0., 0.]} for i in range(3, 6)]
    points += [{'id': 'C006', 'source': [0., 1., 2.], 'target': [0., 1., 2.]}]
    dataset, frame = _dataset(points), _frame()
    monkeypatch.setattr(study_service.repo, 'get', lambda table, id: {'datasets': dataset, 'frames': frame}[table])
    monkeypatch.setattr(study_service.repo, 'put', lambda table, item, insert_only=False: item)
    request = type('D', (), {'name': '研究', 'dataset_id': 'ds-test', 'frame_id': 'f', 'threshold_mm': .5,
                             'iterations': 400, 'seed': 2405, 'fit_ids': ['C003', 'C004', 'C005'], 'check_ids': ['C006']})()
    with pytest.raises(ValueError, match='共线'):
        study_service.create(request)
    snapshot, checksum = lock_snapshot(dataset, frame, .5, 400, 2405, ['C003', 'C004', 'C005'], ['C006'])
    with pytest.raises(ValueError, match='共线'):
        analyze(snapshot, checksum)


def test_fit_only_transform_and_independent_check_metrics():
    points = _make_points()
    fit = [p['id'] for p in points if p['id'] <= 'P040']
    check = [p['id'] for p in points if p['id'] > 'P040']
    snapshot, checksum = lock_snapshot(_dataset(points), _frame(), .5, 400, 2405, fit, check)
    result = analyze(snapshot, checksum)
    assert result['partition']['fit_ids'] == fit
    assert result['partition']['check_ids'] == check
    assert result['partition']['check_status'] == 'verified'
    rows = {r['id']: r for r in result['rows']}
    assert all(r['role'] == 'fit' for i, r in rows.items() if i in fit)
    assert all(r['role'] == 'check' for i, r in rows.items() if i in check)
    assert all(r['inlier'] is None for i, r in rows.items() if i in check)
    assert all(r['check_threshold_exceeded'] is not None for i, r in rows.items() if i in check)
    assert result['fit_metrics']['robust']['point_count'] == len(fit)
    assert result['fit_metrics']['robust']['inlier_count'] == sum(1 for r in rows.values() if r['role'] == 'fit' and r['inlier'])
    assert result['check_metrics']['robust']['point_count'] == len(check)
    # check-point residuals come from the same final robust R/t
    model = result['robust']
    X = np.array([rows[i]['source'] for i in check]); Y = np.array([rows[i]['target'] for i in check])
    errs = np.linalg.norm(X @ np.array(model['R']).T + np.array(model['t']) - Y, axis=1)
    assert np.allclose([rows[i]['robust_residual'] for i in check], errs)
    assert result['check_metrics']['robust']['rmse'] == pytest.approx(float(np.sqrt(np.mean(errs ** 2))), rel=1e-12)


def test_check_points_do_not_influence_transform():
    points = _make_points()
    fit = [p['id'] for p in points if p['id'] <= 'P040']
    snapshot, checksum = lock_snapshot(_dataset(points), _frame(), .5, 400, 2405, fit, [p['id'] for p in points if p['id'] > 'P040'])
    base = analyze(snapshot, checksum)
    tampered = [dict(p) for p in points]
    for p in tampered:
        if p['id'] > 'P040':
            p['target'] = [v + 500.0 for v in p['target']]
    snapshot2, checksum2 = lock_snapshot(_dataset(tampered), _frame(), .5, 400, 2405, fit, [p['id'] for p in tampered if p['id'] > 'P040'])
    other = analyze(snapshot2, checksum2)
    assert base['full']['R'] == other['full']['R'] and base['full']['t'] == other['full']['t']
    assert base['robust']['R'] == other['robust']['R'] and base['robust']['t'] == other['robust']['t']
    assert other['check_metrics']['robust']['threshold_exceeded_count'] == len(tampered) - 40


def test_no_check_points_reports_unverified():
    points = _make_points(10)
    ids = [p['id'] for p in points]
    snapshot, checksum = lock_snapshot(_dataset(points), _frame(), .5, 400, 2405, ids, [])
    result = analyze(snapshot, checksum)
    assert result['partition']['check_status'] == 'unverified'
    assert result['check_metrics']['status'] == 'unverified'
    assert result['check_metrics']['full'] is None and result['check_metrics']['robust'] is None
    assert all(r['inlier'] is not None for r in result['rows'])


@pytest.fixture()
def clean_db():
    repo.init_db()
    ids = {t: [r['id'] for r in repo.all_rows(t)] for t in repo.TABLES}
    yield
    for t, rows in ids.items():
        for rid in [r['id'] for r in repo.all_rows(t) if r['id'] not in rows]:
            conn, q = repo.connect()
            try:
                conn.execute(f'DELETE FROM {t} WHERE id={q}', (rid,))
                conn.commit()
            finally:
                conn.close()


def test_report_splits_fit_and_check_metrics(clean_db):
    points = _make_points()
    fit = [p['id'] for p in points if p['id'] <= 'P040']
    check = [p['id'] for p in points if p['id'] > 'P040']
    repo.put('datasets', _dataset(points))
    repo.put('frames', _frame())
    snapshot, checksum = lock_snapshot(_dataset(points), _frame(), .5, 400, 2405, fit, check)
    repo.put('studies', {'id': 'study-t', 'name': 'n', 'dataset_id': 'ds-test', 'frame_id': 'f', 'threshold_mm': .5,
                         'iterations': 400, 'seed': 2405, 'snapshot': snapshot, 'checksum': checksum, 'created_at': 't'})
    repo.put('runs', {'id': 'run-t', 'study_id': 'study-t', 'status': 'completed', 'result': analyze(snapshot, checksum), 'error': '', 'created_at': 't'})
    repo.put('reviews', {'id': 'rev-t', 'run_id': 'run-t', 'comment': 'ok test', 'status': 'approved', 'reviewer': 'admin@haochuan.test', 'created_at': 't'})
    repo.put('reports', {'id': 'rpt-t', 'run_id': 'run-t', 'review_id': 'rev-t', 'title': 'report', 'created_at': 't'})
    text = report_service.download('rpt-t')
    assert 'FIT / 仅拟合点求解的变换' in text and 'CHECK / 检查点独立误差' in text
    assert 'check_status,verified' in text
    assert 'id,role' in text
    assert ',fit,' in text and ',check,' in text
    # legacy run still downloads with the pre-upgrade column layout
    legacy_snapshot, legacy_checksum = lock_snapshot(_dataset(points), _frame(), .5, 400, 2405)
    repo.put('studies', {'id': 'study-old', 'name': 'old', 'dataset_id': 'ds-test', 'frame_id': 'f', 'threshold_mm': .5,
                         'iterations': 400, 'seed': 2405, 'snapshot': legacy_snapshot, 'checksum': legacy_checksum, 'created_at': 't'})
    legacy = analyze(legacy_snapshot, legacy_checksum)
    repo.put('runs', {'id': 'run-old', 'study_id': 'study-old', 'status': 'completed', 'result': legacy, 'error': '', 'created_at': 't'})
    repo.put('reviews', {'id': 'rev-old', 'run_id': 'run-old', 'comment': 'ok old', 'status': 'approved', 'reviewer': 'admin@haochuan.test', 'created_at': 't'})
    repo.put('reports', {'id': 'rpt-old', 'run_id': 'run-old', 'review_id': 'rev-old', 'title': 'old', 'created_at': 't'})
    old_text = report_service.download('rpt-old')
    assert 'id,sx_mm,sy_mm,sz_mm,tx_mm,ty_mm,tz_mm,full_residual_mm,robust_residual_mm,final_inlier' in old_text
    assert 'FIT /' not in old_text and 'validation_mode' not in old_text
