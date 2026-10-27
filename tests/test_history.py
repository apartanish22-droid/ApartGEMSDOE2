import math

import numpy as np
import pytest
from scipy.ndimage import binary_dilation
from scipy.stats import spearmanr

from audit_history import binary_spearman, disk, lower_overlap_bound, require_self_contained
from fetch_audit_data import checked_entries


def test_radius_is_exact_euclidean_three_pixels():
    s = disk(3)
    assert s.shape == (7, 7)
    assert s[3, 0] and s[0, 3]
    assert not s[0, 0] and not s[0, 2]
    a = np.zeros((9, 9), bool); a[4, 4] = True
    got = binary_dilation(a, structure=s)
    assert got[4, 1] and got[2, 2] and not got[1, 3]


@pytest.mark.parametrize('uncovered,dots,expected', [
    (6649, 37654, (31005, 31005 / 37654)),
    (0, 10, (10, 1.0)), (11, 10, (0, 0.0)), (3, 10, (7, .7)),
])
def test_lower_bound(uncovered, dots, expected):
    assert lower_overlap_bound(uncovered, dots) == expected


@pytest.mark.parametrize('uncovered,dots', [(0, 0), (-1, 2), (False, 4), (2.5, 3), (1, -2)])
def test_invalid_bound_inputs(uncovered, dots):
    with pytest.raises(ValueError):
        lower_overlap_bound(uncovered, dots)


def test_binary_rank_correlation_with_ties():
    a = np.array([[1, 0, 1], [0, 1, 0]], dtype=bool)
    b = np.array([[1, 1, 0], [0, 1, 0]], dtype=bool)
    assert math.isclose(binary_spearman(a, b, 6), spearmanr(a.ravel(), b.ravel()).statistic)
    assert binary_spearman(np.zeros((2, 2), bool), np.ones((2, 2), bool), 4) is None


def test_manifest_rejects_unsafe_or_unpinned_inputs():
    e = {'id': 'ok', 'repo': 'owner/repo', 'ref': 'a' * 40, 'path': 'docs/a.tif', 'sha256': 'b' * 64}
    assert checked_entries({'inputs': [e]}) == [e]
    for bad in [dict(e, id='../file'), dict(e, path='../a'), dict(e, ref='main'), dict(e, sha256='bad')]:
        with pytest.raises(ValueError):
            checked_entries({'inputs': [bad]})
    with pytest.raises(ValueError):
        checked_entries({'inputs': [e, e]})


def test_forensic_audit_rejects_unpinned_sidecars(tmp_path):
    from types import SimpleNamespace
    path = tmp_path / 'sample.tif'
    require_self_contained(SimpleNamespace(name=str(path), files=[str(path)]))
    with pytest.raises(ValueError, match='sidecar'):
        require_self_contained(SimpleNamespace(name=str(path), files=[str(path), str(path) + '.msk']))
