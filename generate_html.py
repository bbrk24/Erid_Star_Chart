#!/usr/bin/env python3

import csv
from dataclasses import dataclass
import math


@dataclass
class StarData:
    name: str
    longitude: float
    declination: float
    distance: float
    magnitude: float


def magnitude_to_opacity(magnitude: float) -> float:
    if magnitude <= -1.0:
        return 1.0
    return (0x10 / 0xFF) ** ((magnitude + 1.0) / 7.5)


def get_coordinates(latitude: float, longitude: float):
    """Takes degrees (0-360, 0-90) and returns cartesian coordinates 0-1"""
    phi = math.pi * (90.0 + latitude) / 180.0
    theta = math.pi * longitude / 180.0
    radius = 1.0 / math.tan(phi / 2.0)
    x = radius * math.cos(theta)
    y = radius * math.sin(theta)
    return ((x + 1.0) / 2.0, (y + 1.0) / 2.0)


def get_stars():
    stars: list[StarData] = []

    with open("EridStarChart.csv", "r") as csvfile:
        reader = csv.reader(csvfile)

        # skip first three lines
        next(reader)
        next(reader)
        next(reader)

        for row in reader:
            name = row[0]
            if name.startswith("40 Eridani"):
                continue

            try:
                stars.append(
                    StarData(
                        name,
                        longitude=float(row[21]),
                        declination=float(row[22]),
                        distance=float(row[23]),
                        magnitude=float(row[24]),
                    )
                )
            except ValueError:
                continue

    return stars


def main():
    north_hemisphere_html = ""
    south_hemisphere_html = ""

    for star in sorted(get_stars(), key=lambda s: -s.magnitude):
        opacity = magnitude_to_opacity(star.magnitude)

        if star.declination >= 0.0:
            x, y = get_coordinates(star.declination, star.longitude)
            star_html = f'<div class="star" title="{star.name}" style="left: {x * 100.0}%; top: {y * 100.0}%; opacity: {opacity};"></div>'
            north_hemisphere_html += star_html

        if star.declination <= 0.0:
            x, y = get_coordinates(-star.declination, -star.longitude)
            star_html = f'<div class="star" title="{star.name}" style="left: {x * 100.0}%; top: {y * 100.0}%; opacity: {opacity};"></div>'
            south_hemisphere_html += star_html

    template = ""
    with open("template.html", "r") as templatefile:
        template = templatefile.read()

    full_html = template.replace("{{NorthHemisphere}}", north_hemisphere_html).replace(
        "{{SouthHemisphere}}", south_hemisphere_html
    )

    with open("map.html", "w") as output:
        output.write(full_html)


if __name__ == "__main__":
    main()
