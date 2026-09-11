#!/usr/bin/env python3

import csv
from dataclasses import dataclass
from math import pi, sin, cos, tan, acos, atan2


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
    """Takes degrees (0..360, 0..90) and returns cartesian coordinates -1..1"""
    phi = pi * (90.0 + latitude) / 180.0
    theta = pi * longitude / 180.0
    radius = 1.0 / tan(phi / 2.0)
    return (radius * cos(theta), radius * sin(theta))


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
    orion_html = ""

    orion_limit_x, orion_limit_y = get_coordinates(
        90.0 - 20.22992832414391, 180.0 * atan2(31, 26) / pi
    )

    for star in sorted(get_stars(), key=lambda s: -s.magnitude):
        opacity = magnitude_to_opacity(star.magnitude)

        if star.declination >= 0.0:
            x, y = get_coordinates(star.declination, star.longitude)
            star_html = f'<div class="star" title="{star.name}" style="left: {(x + 1.0) * 50.0}%; top: {(y + 1.0) * 50.0}%; opacity: {opacity};"></div>'
            north_hemisphere_html += star_html

        if star.declination <= 0.0:
            x, y = get_coordinates(-star.declination, -star.longitude)
            star_html = f'<div class="star" title="{star.name}" style="left: {(x + 1.0) * 50.0}%; top: {(y + 1.0) * 50.0}%; opacity: {opacity};"></div>'
            south_hemisphere_html += star_html

        # center RA on +90, so that changing declination is an X-axis rotation
        orion_phi = pi * (star.longitude + 3.0) / 180.0
        # center declination on 90
        orion_theta = pi * (90.0 - star.declination) / 180.0
        orion_alpha = pi * 101.5 / 180.0
        # https://stackoverflow.com/a/5279478/6253337
        orion_theta_prime = acos(
            sin(orion_theta) * sin(orion_phi) * sin(orion_alpha)
            + cos(orion_theta) * cos(orion_alpha)
        )
        if orion_theta_prime <= pi / 2.0:
            orion_y_prime = sin(orion_theta) * sin(orion_phi) * cos(orion_alpha) - cos(
                orion_theta
            ) * sin(orion_alpha)
            orion_x_prime = sin(orion_theta) * cos(orion_phi)
            orion_phi_prime = atan2(orion_y_prime, orion_x_prime)
            x, y = get_coordinates(
                90.0 - 180.0 * orion_theta_prime / pi, 180.0 * orion_phi_prime / pi
            )

            if abs(x) <= abs(orion_limit_x) and abs(y) <= abs(orion_limit_y):
                html_left = (x / abs(orion_limit_x) + 1.0) * 50.0
                html_top = (y / abs(orion_limit_y) + 1.0) * 50.0
                orion_html += f'<div class="star" title="{star.name}" style="left: {html_left}%; top: {html_top}%; opacity: {opacity};"></div>'

    template = ""
    with open("template.html", "r") as templatefile:
        template = templatefile.read()

    full_html = (
        template.replace("{{NorthHemisphere}}", north_hemisphere_html)
        .replace("{{SouthHemisphere}}", south_hemisphere_html)
        .replace("{{Orion}}", orion_html)
    )

    with open("map.html", "w") as output:
        output.write(full_html)


if __name__ == "__main__":
    main()
