import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from scripts.validate_tif import validate


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.sample = Path(self.tmp.name) / 'sample.tif'
        self.pred = Path(self.tmp.name) / 'pred.tif'
        self.profile = dict(driver='GTiff', height=2, width=2, count=1, dtype='float32',
                            crs='EPSG:32611', transform=from_origin(100, 200, 10, 10), nodata=None)
        self.write(self.sample, np.ones((2, 2), dtype='float32'))

    def write(self, path, data, **changes):
        with rasterio.open(path, 'w', **(self.profile | changes)) as dst:
            dst.write(data, 1)

    def test_valid_format_not_authorization(self):
        self.write(self.pred, np.full((2, 2), 0.5, dtype='float32'))
        result = validate(self.sample, self.pred)
        self.assertTrue(result['format_valid'])
        self.assertFalse(result['submission_authorized'])

    def test_rejects_nan_and_out_of_range_even_without_nodata(self):
        for value in (float('nan'), -0.01, 1.01, float('inf')):
            with self.subTest(value=value):
                self.write(self.pred, np.array([[value, 0], [0, 0]], dtype='float32'))
                self.assertFalse(validate(self.sample, self.pred)['format_valid'])

    def test_rejects_mismatched_grid(self):
        self.write(self.pred, np.ones((2, 2), dtype='float32'),
                   transform=from_origin(110, 200, 10, 10))
        self.assertFalse(validate(self.sample, self.pred)['format_valid'])


if __name__ == '__main__':
    unittest.main()
