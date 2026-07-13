"""Regression tests for the national hillshade builder."""

import unittest

import numpy as np
from rasterio.transform import from_bounds

from scripts.build_paraguay_hillshade_v3 import (
    compute_hillshade_chunked,
    meters_per_cell,
)


class HillshadeChunkingTests(unittest.TestCase):
    def test_preserves_non_square_dem_shape_across_chunks(self):
        """Horn's 3x3 window must not discard the first/last DEM columns."""
        dem = np.arange(35, dtype=np.float32).reshape(5, 7)
        transform = from_bounds(-60.0, -25.0, -59.0, -24.0, 7, 5)

        hillshade = compute_hillshade_chunked(dem, transform, chunk_rows=2)

        self.assertEqual(hillshade.shape, dem.shape)
        self.assertEqual(hillshade.dtype, np.uint8)
        self.assertGreater(np.count_nonzero(hillshade[:, 0]), 0)
        self.assertGreater(np.count_nonzero(hillshade[:, -1]), 0)

    def test_meter_cell_size_uses_geographic_center_latitude(self):
        """North-up transforms must derive latitude from transform.f - height*dy/2."""
        transform = from_bounds(-62.5, -27.5, -58.5, -23.5, 400, 400)

        cellsize_x, cellsize_y = meters_per_cell(transform, height=400)

        expected_lat = -25.5
        expected_x = abs(transform.a) * 111_320 * np.cos(np.radians(expected_lat))
        expected_y = abs(transform.e) * 111_320
        self.assertAlmostEqual(expected_x, cellsize_x, places=6)
        self.assertAlmostEqual(expected_y, cellsize_y, places=6)
        self.assertGreater(cellsize_x, 900)
        self.assertLess(cellsize_x, 1_100)

    def test_chunk_size_does_not_change_result(self):
        """Chunk boundaries must be invisible in the computed hillshade."""
        rng = np.random.default_rng(42)
        dem = rng.normal(loc=200.0, scale=30.0, size=(11, 13)).astype(np.float32)
        transform = from_bounds(-60.0, -25.0, -59.0, -24.0, 13, 11)

        one_chunk = compute_hillshade_chunked(dem, transform, chunk_rows=11)
        many_chunks = compute_hillshade_chunked(dem, transform, chunk_rows=3)

        np.testing.assert_array_equal(many_chunks, one_chunk)


if __name__ == "__main__":
    unittest.main()
