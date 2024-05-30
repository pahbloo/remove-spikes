from math import isclose
from tempfile import TemporaryDirectory

import fiona
import fiona.errors
import geopandas as gpd
import pytest
from shapely.geometry import LineString, Polygon

from src.removespikes import RemoveSpikes


class TestCalculateAngle:
    @pytest.mark.parametrize(
        "a, b, c, expected_angle",
        [
            ((0, 0), (1, 0), (2, 0), 180.0),  # Straight horizontal line
            ((0, 0), (0, 1), (0, 2), 180.0),  # Straight vertical line
            ((0, 0), (1, 1), (2, 2), 180.0),  # Straight diagonal line
            ((0, 0), (1, 1), (0, 2), 90.0),  # Right angle
            ((0, 0), (1, 0), (1, 1), 90.0),  # Right angle
            ((0, 0), (1, 0), (1, -1), 90.0),  # Right angle
            ((0, 0), (0.1, 0.1), (0.2, 0), 90.0),  # Right angle
            ((0, 0), (1, 0), (0.5, 0.5), 45.0),  # 45 degree angle
            ((0, 0), (0, 1), (-1, 0), 45.0),  # 45 degree angle
            ((0, 0), (1, 1), (2, 1), 135.0),  # 135 degree angle
            ((0, 0), (1, 0), (2, 1), 135.0),  # 135 degree angle
        ],
    )
    def test_calculate_angle(self, a, b, c, expected_angle):
        angle = RemoveSpikes._calculate_angle(a, b, c)
        assert isclose(
            angle, expected_angle, abs_tol=2e-6
        ), f"Expected {expected_angle}, got {angle}"

    @pytest.mark.parametrize(
        "a, b, c",
        [
            ((0, 0), (1, 1), (1, 1)),  # Duplicate points
            ((1, 1), (1, 1), (2, 2)),  # Duplicate points
            ((1, 1), (0, 0), (0, 0)),  # Duplicate points
        ],
    )
    def test_calculate_angle_zero_division(self, a, b, c):
        with pytest.raises(ZeroDivisionError):
            RemoveSpikes._calculate_angle(a, b, c)


class TestIsSpike:
    @pytest.mark.parametrize(
        "prev_pt, curr_pt, next_pt, angle_threshold, min_distance, expected",
        [
            # Test with acute angle, below threshold
            ((0, 0), (1, 1), (0.5, 0), 45, 1, True),
            # Test with obtuse angle, above threshold
            ((0, 0), (1, 1), (2, 1.5), 135, 1, False),
            # Test with right angle, below threshold
            ((0, 0), (1, 1), (1, 0), 90, 0.5, True),
            # Test with right angle, above threshold
            ((0, 0), (1, 1), (1, 2), 90, 1.5, False),
            # Test with small distance, below threshold
            ((0, 0), (0.1, 0.1), (0.2, 0), 91, 0, True),
            # Test with small distance, below threshold
            ((0, 0), (0.1, 0.9), (0.1, 0), 5, 1, False),
            # Test with large distance, above threshold
            ((0, 0), (10, 10), (20, 0), 45, 15, False),
            # Test with exactly collinear points
            ((0, 0), (1, 0), (2, 0), 0, 1, False),
            # Test with negative coordinates
            ((-1, -1), (0, 0), (1, -1), 91, 1, True),
            # Test with zero distance
            ((0, 0), (0, 0), (0, 0), 45, 1, False),
        ],
    )
    def test_is_spike(
        self,
        prev_pt,
        curr_pt,
        next_pt,
        angle_threshold,
        min_distance,
        expected,
    ):
        assert (
            RemoveSpikes._is_spike(
                prev_pt, curr_pt, next_pt, angle_threshold, min_distance
            )
            == expected
        )


class TestRemoveSpikesFromGeometry:
    def test_remove_spikes_from_linestring_no_spikes(self):
        linestring = LineString([(0, 0), (1, 1), (2, 2)])
        result = RemoveSpikes._remove_spikes_from_geometry(linestring)
        assert result.equals(
            linestring
        ), "Expected no change for a LineString with no spikes"

    def test_remove_spikes_from_linestring_with_spike(self):
        linestring = LineString([(0, 0), (1, 100), (2, 0)])
        expected = LineString([(0, 0), (2, 0)])
        result = RemoveSpikes._remove_spikes_from_geometry(
            linestring, angle_threshold=5
        )
        assert result.equals(
            expected
        ), "Expected spike to be removed from LineString"

    def test_remove_spikes_from_polygon_no_spikes(self):
        polygon = Polygon([(0, 0), (1, 1), (2, 0), (1, -1), (0, 0)])
        result = RemoveSpikes._remove_spikes_from_geometry(polygon)
        assert result.equals(
            polygon
        ), "Expected no change for a Polygon with no spikes"

    def test_remove_spikes_from_polygon_with_spike(self):
        polygon = Polygon(
            [(0, 0), (1, 1), (2, 100), (3, 1), (4, 0), (2, -2), (0, 0)]
        )
        expected = Polygon([(0, 0), (1, 1), (3, 1), (4, 0), (2, -2), (0, 0)])
        result = RemoveSpikes._remove_spikes_from_geometry(
            polygon, angle_threshold=5
        )
        assert result.equals(
            expected
        ), "Expected spike to be removed from Polygon"

    def test_remove_spikes_with_high_angle_threshold(self):
        linestring = LineString([(0, 0), (1, 0), (2, 0)])
        result = RemoveSpikes._remove_spikes_from_geometry(
            linestring, angle_threshold=180
        )
        assert result.equals(
            linestring
        ), "Expected no spikes to be removed with high angle threshold"

    def test_remove_spikes_with_low_min_distance(self):
        linestring = LineString([(0, 0), (1, 0), (1, 0.1), (1.001, 0), (2, 0)])
        expected = LineString([(0, 0), (1, 0), (1.001, 0), (2, 0)])
        result = RemoveSpikes._remove_spikes_from_geometry(
            linestring, angle_threshold=5, min_distance=0
        )
        assert result.equals(
            expected
        ), "Expected spike to be removed with low minimum distance"

    def test_remove_spikes_handles_zero_division_error(self):
        linestring = LineString([(0, 0), (1, 0), (1, 0)])
        result = RemoveSpikes._remove_spikes_from_geometry(linestring)
        assert result.equals(
            linestring
        ), "Expected no change for LineString with overlapping points"

    def test_remove_spikes_from_complex_polygon(self):
        polygon = Polygon(
            [
                (0, 0),
                (1, 3),
                (3, 4),
                (5, 3),
                (6, 1),
                (4, 100),
                (3, 0),
                (1, 0),
                (0, 0),
            ]
        )
        expected = Polygon(
            [(0, 0), (1, 3), (3, 4), (5, 3), (6, 1), (3, 0), (1, 0), (0, 0)]
        )
        result = RemoveSpikes._remove_spikes_from_geometry(
            polygon, angle_threshold=5
        )
        assert result.equals(
            expected
        ), "Expected complex polygon to have spikes removed"

    def test_remove_spikes_with_min_distance(self):
        polygon = Polygon(
            [
                (0, 0),
                (0.1, 0.9),
                (0.1, 0),
                (1, 3),
                (3, 4),
                (5, 3),
                (6, 1),
                (4, 100),
                (3, 0),
                (1, 0),
                (0, 0),
            ]
        )
        expected = Polygon(
            [
                (0, 0),
                (0.1, 0.9),
                (0.1, 0),
                (1, 3),
                (3, 4),
                (5, 3),
                (6, 1),
                (3, 0),
                (1, 0),
                (0, 0),
            ]
        )
        result = RemoveSpikes._remove_spikes_from_geometry(
            polygon, angle_threshold=5, min_distance=1
        )
        assert result.equals(
            expected
        ), "Expected polygon to have only spikes with min distance removed"


class TestRemoveSpikesFromGeoDataFrame:
    @pytest.fixture
    def simple_gdf(self) -> gpd.GeoDataFrame:
        data = {
            "geometry": [
                LineString([(0, 0), (1, 1), (2, 2), (3, 1), (4, 0)]),
                Polygon([(0, 0), (1, 1), (2, 2), (1, 0), (0, 0)]),
            ]
        }
        return gpd.GeoDataFrame(data)

    @pytest.fixture
    def gdf_with_custom_column(self) -> gpd.GeoDataFrame:
        data = {
            "custom_geom": [
                LineString([(0, 0), (1, 1), (2, 2), (3, 1), (4, 0)]),
                Polygon([(0, 0), (1, 1), (2, 2), (1, 0), (0, 0)]),
            ]
        }
        return gpd.GeoDataFrame(data)

    @pytest.fixture
    def empty_gdf(self) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(columns=["geometry"])

    def test_basic_functionality(self, simple_gdf):
        result_gdf = RemoveSpikes.from_geodataframe(simple_gdf)
        assert not result_gdf.empty
        assert len(result_gdf) == len(simple_gdf)

    def test_return_new_geodataframe(self, simple_gdf):
        result_gdf = RemoveSpikes.from_geodataframe(simple_gdf)
        assert not result_gdf.empty
        assert result_gdf is not simple_gdf

    def test_custom_geometry_column(self, gdf_with_custom_column):
        result_gdf = RemoveSpikes.from_geodataframe(
            gdf_with_custom_column, geometry_column="custom_geom"
        )
        assert not result_gdf.empty
        assert len(result_gdf) == len(gdf_with_custom_column)

    def test_empty_geodataframe(self, empty_gdf):
        result_gdf = RemoveSpikes.from_geodataframe(empty_gdf)
        assert result_gdf.empty

    def test_angle_threshold(self, simple_gdf):
        result_gdf = RemoveSpikes.from_geodataframe(simple_gdf, angle=10)
        assert not result_gdf.empty
        assert len(result_gdf) == len(simple_gdf)

    def test_min_distance(self, simple_gdf):
        result_gdf = RemoveSpikes.from_geodataframe(
            simple_gdf, min_distance=0.5
        )
        assert not result_gdf.empty
        assert len(result_gdf) == len(simple_gdf)


class TestRemoveSpikesFromFile:
    @pytest.fixture
    def sample_gdf(self):
        # Create a sample GeoDataFrame with LineString and Polygon
        data = {
            "geometry": [
                LineString([(0, 0), (1, 2), (2, 1), (3, 3)]),
                Polygon([(0, 0), (1, 2), (2, 1), (0, 0)]),
            ]
        }
        return gpd.GeoDataFrame(data)

    @pytest.fixture
    def temp_file(self, sample_gdf):
        with TemporaryDirectory() as tmpdirname:
            temp_file = f"{tmpdirname}/temp_file.geojson"
            sample_gdf.to_file(temp_file)
            yield temp_file

    def test_from_file_removes_spikes(self, temp_file):
        result = RemoveSpikes.from_file(temp_file, angle=1.0, min_distance=0.0)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2

        line_geom = result.iloc[0].geometry
        poly_geom = result.iloc[1].geometry

        assert isinstance(line_geom, LineString)
        assert isinstance(poly_geom, Polygon)

    def test_from_file_default_geometry_column(self, temp_file):
        result = RemoveSpikes.from_file(temp_file, angle=1.0, min_distance=0.0)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2

    def test_from_file_custom_geometry_column(self, temp_file):
        result = RemoveSpikes.from_file(
            temp_file, geometry_column="geometry", angle=1.0, min_distance=0.0
        )

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2

    def test_from_file_invalid_file(self):
        with pytest.raises(fiona.errors.DriverError):
            RemoveSpikes.from_file("invalid_file.gpkg")

    def test_from_file_empty_gdf(self, temp_file):
        empty_gdf = gpd.GeoDataFrame({"geometry": []})
        with TemporaryDirectory() as tmpdirname:
            temp_file = f"{tmpdirname}/temp_file.geojson"
            empty_gdf.to_file(temp_file)
            result = RemoveSpikes.from_file(
                temp_file, angle=1.0, min_distance=0.0
            )

        assert isinstance(result, gpd.GeoDataFrame)
        assert result.empty


if __name__ == "__main__":
    pytest.main()
