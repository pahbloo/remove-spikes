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
        cos_angle = dot_product / mag_product

        # Clip cos_angle to avoid numerical issues outside the range [-1, 1]
        cos_angle = np.clip(cos_angle, -1.0, 1.0)

        # Calculate the angle in radians
        angle_rad = np.arccos(cos_angle)

        # Convert the angle to degrees
        angle_deg = np.degrees(angle_rad)

        return float(angle_deg)

    @staticmethod
    def _is_spike(
        a: Coord,
        b: Coord,
        c: Coord,
        angle_threshold: float,
        min_distance: float,
    ) -> bool:
        """
        Check if a point is a spike based on angle and distance thresholds.
        """
        try:
            angle: float = RemoveSpikes._calculate_angle(a, b, c)
        except ZeroDivisionError:
            # Don't consider as spike if angle calculation fails
            return False

        d1: float = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        d2: float = ((b[0] - c[0]) ** 2 + (b[1] - c[1]) ** 2) ** 0.5

        return (
            angle < angle_threshold and d1 > min_distance and d2 > min_distance
        )

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
        if geometry.is_empty:
            return geometry

        def is_line() -> bool:
            return isinstance(geometry, LineString)

        def is_polygon() -> bool:
            return isinstance(geometry, Polygon)

        if not is_line() and not is_polygon:
            return geometry

        coords = (
            list(geometry.coords)
            if is_line()
            else list(geometry.exterior.coords)
        )
        new_coords: list[Coord] = [coords[0]]

        if isinstance(geometry, Polygon):
            # Handle the case where the first point is a spike in a Polygon
            if RemoveSpikes._is_spike(
                coords[-2], coords[0], coords[1], angle_threshold, min_distance
            ):
                # Start from the second point
                new_coords = []

        for i in range(1, len(coords) - 1):
            prev_pt = coords[i - 1]
            curr_pt = coords[i]
            next_pt = coords[i + 1]

            if not RemoveSpikes._is_spike(
                prev_pt, curr_pt, next_pt, angle_threshold, min_distance
            ):
                new_coords.append(curr_pt)

        # Don't add the last point to the new polygon. The first and last
        # coordinates of a polygon are the same. If we remove the first point,
        # we can't add it back as the last one. The simplest solution is to not
        # append it, since creating a Polygon(a, b, c) is the same as creating
        # a Polygon(a, b, c, a).
        if is_line():
            new_coords.append(coords[-1])

        if isinstance(geometry, LineString):
            return LineString(new_coords)
        elif isinstance(geometry, Polygon):
            return Polygon(new_coords)
        else:
            return geometry

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
        gdf: gpd.GeoDataFrame = gpd.read_file(filename, **kwargs)
        return RemoveSpikes.from_geodataframe(
            gdf, geometry_column, angle, min_distance
        )

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
        gdf = gdf.copy()  # type: ignore
        geometry_column = geometry_column or gdf.geometry.name
        gdf[geometry_column] = gdf[geometry_column].apply(
            lambda geom: RemoveSpikes._remove_spikes_from_geometry(
                geom, angle, min_distance
            )
        )
        return gdf
