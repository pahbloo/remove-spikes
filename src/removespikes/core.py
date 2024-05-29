import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Polygon

GeometryType = LineString | Polygon
Coord = tuple[float, float]


class RemoveSpikes:
    @staticmethod
    def _calculate_angle(a: Coord, b: Coord, c: Coord) -> float:
        """Calculate the angle between three points (in degrees)."""

        # Convert points to numpy arrays
        A = np.array(a)
        B = np.array(b)
        C = np.array(c)

        # Create vectors BA and BC
        BA = A - B
        BC = C - B

        # Calculate the dot product and magnitudes of BA and BC
        dot_product = np.dot(BA, BC)
        magnitude_BA = np.linalg.norm(BA)
        magnitude_BC = np.linalg.norm(BC)

        # Raise error if the magnitudes product is zero
        mag_product = magnitude_BA * magnitude_BC
        if mag_product == 0:
            raise ZeroDivisionError()

        # Calculate the cosine of the angle
        cos_angle = dot_product / (magnitude_BA * magnitude_BC)

        # Clip cos_angle to avoid numerical issues outside the range [-1, 1]
        cos_angle = np.clip(cos_angle, -1.0, 1.0)

        # Calculate the angle in radians
        angle_rad = np.arccos(cos_angle)

        # Convert the angle to degrees
        angle_deg = np.degrees(angle_rad)

        return float(angle_deg)

    @staticmethod
    def _remove_spikes_from_geometry(
        geometry: GeometryType,
        angle_threshold: float = 1.0,
        min_distance: float = 0.0,
    ) -> GeometryType:
        """
        Remove spikes from a single LineString or Polygon geometry.

        Args:
            geometry: The LineString or Polygon to remove spikes from.
            angle_threshold: Angle threshold in degrees. Vertices with an
                angle smaller than this threshold will be considered spikes.
            min_distance:  Minimum distance between a vertex and its neighbors
                for it to be considered a spike.

        Returns:
            The geometry with spikes removed.
        """
        pass

    @staticmethod
    def from_file(
        filename: str,
        geometry_column: str | None = None,
        angle: float = 1,
        min_distance: float = 0.0,
        **kwargs,
    ) -> gpd.GeoDataFrame:
        """
        Remove spikes from LineStrings or Polygons in a file.

        Args:
            filename: Path to the file.
            geometry_column: The name of the geometry column. Defaults to None.
            angle: Angle threshold in degrees. Vertices with an angle smaller
                than this threshold will be considered spikes. Defaults to 1.0.
            min_distance: Minimum distance between a vertex and its neighbors
                for it to be considered a spike. Defaults to 0.0.
            **kwargs: These arguments are passed to fiona.open, and can be used
                to access multi-layer data, data stored within archives (zip
                files), etc.

        Returns:
            A GeoDataFrame with the modified geometries.
        """
        pass

    @staticmethod
    def from_geodataframe(
        gdf: gpd.GeoDataFrame,
        geometry_column: str | None = None,
        angle: float = 1,
        min_distance: float = 0.0,
    ) -> gpd.GeoDataFrame:
        """
        Remove spikes from LineStrings or Polygons in a GeoDataFrame.

        Args:
            gdf: The input GeoDataFrame.
            geometry_column: The name of the geometry column. By default, it
                uses the name retrieved from gpd.geometry.name.
            angle: Angle threshold in degrees. Vertices with an angle smaller
                than this threshold will be considered spikes. Defaults to 1.0.
            min_distance: Minimum distance between a vertex and its neighbors
                for it to be considered a spike. Defaults to 0.0.

        Returns:
            A new GeoDataFrame with the modified geometries.
        """
        pass
