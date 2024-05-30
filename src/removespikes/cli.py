import argparse

import geopandas as gpd

from . import RemoveSpikes


def main() -> None:
    """
    Command-line interface for removing spikes from geospatial data.
    """

    parser = argparse.ArgumentParser(
        description="Remove spikes from lines and polygons in geospatial data "
        "files. Supports formats like GeoPackage, Shapefile, etc."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Path to the input file (GeoPackage, Shapefile, etc.).",
    )
    parser.add_argument(
        "--layer",
        "-l",
        type=str,
        default=None,
        help="Name of the specific layer/table in the input file (only for "
        "multi-layer files like GeoPackage).",
    )
    parser.add_argument(
        "--geometry-column",
        "-g",
        type=str,
        default=None,
        help="Name of the geometry column in the GeoDataFrame. Specify this "
        "if the table contains multiple geometry columns.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Path to the output file (GeoPackage, Shapefile, etc.).",
    )
    parser.add_argument(
        "--angle",
        "-a",
        type=float,
        default=1.0,
        help="Angle threshold in degrees. Vertices with an angle smaller than "
        "this threshold are considered spikes. Defaults to 1.0 degrees.",
    )
    parser.add_argument(
        "--min-distance",
        "-d",
        type=float,
        default=0.0,
        help="Minimum distance in units between a vertex and its neighbors "
        "for it to be considered a spike. Defaults to 0.0 units.",
    )

    args = parser.parse_args()

    try:
        if args.layer:
            gdf: gpd.GeoDataFrame = RemoveSpikes.from_file(
                args.input,
                angle=args.angle,
                min_distance=args.min_distance,
                geometry_column=args.geometry_column,
                layer=args.layer,
            )
        else:
            gdf: gpd.GeoDataFrame = RemoveSpikes.from_file(
                args.input,
                angle=args.angle,
                min_distance=args.min_distance,
                geometry_column=args.geometry_column,
            )
        gdf.to_file(args.output)
        print(f"Spikes removed successfully. Output saved to: {args.output}")
    except Exception as e:
        print(f"Error processing data: {e}")


if __name__ == "__main__":
    main()
