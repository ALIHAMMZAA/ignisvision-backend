import math

import rasterio


WORLDCOVER_BUCKET = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
)

WORLDCOVER_VERSION = "v200"
WORLDCOVER_YEAR = "2021"


WORLDCOVER_CLASSES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}


# Cache open WorldCover datasets by tile URL.
# This prevents reopening/downloading the same tile for every anomaly.
_DATASET_CACHE = {}


def get_worldcover_tile(latitude: float, longitude: float) -> str:
    """Return the ESA WorldCover 2021 v200 tile URL containing the point."""

    lat_tile = math.floor(latitude / 3) * 3
    lon_tile = math.floor(longitude / 3) * 3

    lat_prefix = "N" if lat_tile >= 0 else "S"
    lon_prefix = "E" if lon_tile >= 0 else "W"

    tile = (
        f"{lat_prefix}{abs(lat_tile):02d}"
        f"{lon_prefix}{abs(lon_tile):03d}"
    )

    return (
        f"{WORLDCOVER_BUCKET}/"
        f"{WORLDCOVER_VERSION}/"
        f"{WORLDCOVER_YEAR}/"
        f"map/"
        f"ESA_WorldCover_10m_{WORLDCOVER_YEAR}_"
        f"v200_{tile}_Map.tif"
    )


def get_worldcover_dataset(tile_url: str):
    """Open a WorldCover dataset once and reuse it from the cache."""

    if tile_url not in _DATASET_CACHE:
        _DATASET_CACHE[tile_url] = rasterio.open(tile_url)

    return _DATASET_CACHE[tile_url]


def get_worldcover_context(latitude: float, longitude: float) -> dict:
    """Sample the WorldCover class at one latitude/longitude."""

    tile_url = get_worldcover_tile(latitude, longitude)
    dataset = get_worldcover_dataset(tile_url)

    value = next(
        dataset.sample([(longitude, latitude)])
    )[0]

    class_value = int(value)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "worldcover_value": class_value,
        "land_cover_label": WORLDCOVER_CLASSES.get(
            class_value,
            "Unknown",
        ),
        "source": "ESA WorldCover 2021 v200",
        "tile_url": tile_url,
    }