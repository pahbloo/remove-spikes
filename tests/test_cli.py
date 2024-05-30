import pytest
import argparse
from unittest.mock import patch, MagicMock
import geopandas as gpd
from src.removespikes.cli import main


class TestRemoveSpikesMain:
    @patch("argparse.ArgumentParser.parse_args")
    @patch("src.removespikes.RemoveSpikes.from_file")
    def test_main_success(self, mock_from_file, mock_parse_args):
        # Setup mock arguments
        mock_parse_args.return_value = argparse.Namespace(
            input="input_file.gpkg",
            layer="layer_name",
            geometry_column="geometry",
            output="output_file.gpkg",
            angle=1.0,
            min_distance=0.0,
        )

        # Setup mock return values
        mock_gdf = MagicMock(spec=gpd.GeoDataFrame)
        mock_from_file.return_value = mock_gdf

        # Call the main function
        with patch("builtins.print") as mock_print:
            main()

        # Assertions
        mock_from_file.assert_called_once_with(
            "input_file.gpkg",
            angle=1.0,
            min_distance=0.0,
            geometry_column="geometry",
            layer="layer_name",
        )
        mock_gdf.to_file.assert_called_once_with("output_file.gpkg")
        mock_print.assert_called_with(
            "Spikes removed successfully. Output saved to: output_file.gpkg"
        )

    @patch("argparse.ArgumentParser.parse_args")
    @patch("src.removespikes.RemoveSpikes.from_file")
    def test_main_success_no_layer(self, mock_from_file, mock_parse_args):
        # Setup mock arguments
        mock_parse_args.return_value = argparse.Namespace(
            input="input_file.gpkg",
            layer=None,
            geometry_column="geometry",
            output="output_file.gpkg",
            angle=1.0,
            min_distance=0.0,
        )

        # Setup mock return values
        mock_gdf = MagicMock(spec=gpd.GeoDataFrame)
        mock_from_file.return_value = mock_gdf

        # Call the main function
        with patch("builtins.print") as mock_print:
            main()

        # Assertions
        mock_from_file.assert_called_once_with(
            "input_file.gpkg",
            angle=1.0,
            min_distance=0.0,
            geometry_column="geometry",
        )
        mock_gdf.to_file.assert_called_once_with("output_file.gpkg")
        mock_print.assert_called_with(
            "Spikes removed successfully. Output saved to: output_file.gpkg"
        )

    @patch("argparse.ArgumentParser.parse_args")
    @patch("src.removespikes.RemoveSpikes.from_file")
    def test_main_exception(self, mock_from_file, mock_parse_args):
        # Setup mock arguments
        mock_parse_args.return_value = argparse.Namespace(
            input="input_file.gpkg",
            layer="layer_name",
            geometry_column="geometry",
            output="output_file.gpkg",
            angle=1.0,
            min_distance=0.0,
        )

        # Setup mock exception
        mock_from_file.side_effect = Exception("Test exception")

        # Call the main function
        with patch("builtins.print") as mock_print:
            main()

        # Assertions
        mock_from_file.assert_called_once_with(
            "input_file.gpkg",
            angle=1.0,
            min_distance=0.0,
            geometry_column="geometry",
            layer="layer_name",
        )
        mock_print.assert_called_with("Error processing data: Test exception")


if __name__ == "__main__":
    pytest.main()
