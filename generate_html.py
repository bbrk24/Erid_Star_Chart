#!/usr/bin/env python3

import csv
import json
from dataclasses import dataclass
from math import acos, atan2, cos, pi, sin, tan
from typing import Any


MAX_VISIBLE_MAGNITUDE = 6.5


@dataclass
class StarData:
    name: str
    longitude: float
    declination: float
    distance: float
    magnitude: float


def cast_or_error(obj: Any, t: type, msg: str):
    if isinstance(obj, t):
        return obj
    else:
        raise TypeError(msg)


@dataclass
class ConstellationInfo:
    id: str
    name: str
    declination: tuple[int, int]
    longitude: tuple[int, int]
    description: str | None

    @classmethod
    def from_dict(cls, d: Any):
        if not isinstance(d, dict):
            raise TypeError("constellation must be an object")

        id: str = cast_or_error(d["id"], str, "'id must be a string")
        name: str = cast_or_error(d["name"], str, f"'name' must be a string")
        declination: list = cast_or_error(
            d["declination"], list, "'declination' must be an array"
        )
        longitude: list = cast_or_error(
            d["longitude"], list, "'longitude' must be an array"
        )

        description: str | None = None
        if "description" in d:
            description = d["description"]
        if description is not None and not isinstance(description, str):
            raise TypeError("'description' must be null or string")

        if (
            len(longitude) != 2
            or not isinstance(longitude[0], int)
            or not isinstance(longitude[1], int)
            or longitude[0] <= -360
            or longitude[1] > 360
            or longitude[0] >= longitude[1]
            or longitude[1] - longitude[0] > 360
        ):
            raise ValueError(
                "Invalid longitude (must be a pair of integers within 360 of each other)"
            )

        if (
            len(declination) != 2
            or not isinstance(declination[0], int)
            or not isinstance(declination[1], int)
            or declination[0] < -90
            or declination[1] > 90
            or declination[0] >= declination[1]
        ):
            raise ValueError(
                "Invalid declination (must be a pair of integers between -90 and 90)"
            )

        return cls(id, name, tuple(declination), tuple(longitude), description)

    def limit_coordinates(self):
        if self.declination[1] == 90:
            limit_x, _ = get_coordinates(self.declination[0], 0.0)
            return (abs(limit_x), abs(limit_x))
        if self.declination[0] == -90:
            limit_x, _ = get_coordinates(-self.declination[1], 0.0)
            return (abs(limit_x), abs(limit_x))

        declination_range = self.declination[1] - self.declination[0]
        longitude_range = float(self.longitude[1] - self.longitude[0])

        if self.declination[1] >= 0 and self.declination[0] <= 0:
            min_declination = 0
        elif self.declination[1] < 0:
            min_declination = -self.declination[1]
        else:
            min_declination = self.declination[0]

        longitude_range *= cos(pi * min_declination / 180.0)

        limit_x, _ = get_coordinates(90.0 - longitude_range / 2.0, 0.0)
        _, limit_y = get_coordinates(90.0 - declination_range / 2.0, 90.0)

        return (abs(limit_x), abs(limit_y))

    def element_style(self):
        if self.declination[1] == 90:
            size = 2 * (90 - self.declination[0])
            return (
                f"width: calc(var(--deg) * {size}); height: calc(var(--deg) * {size});"
            )
        if self.declination[0] == -90:
            size = 2 * (90 + self.declination[1])
            return (
                f"width: calc(var(--deg) * {size}); height: calc(var(--deg) * {size});"
            )

        declination_range = self.declination[1] - self.declination[0]
        longitude_range = float(self.longitude[1] - self.longitude[0])

        if self.declination[1] >= 0 and self.declination[0] <= 0:
            min_declination = 0
        elif self.declination[1] < 0:
            min_declination = -self.declination[1]
        else:
            min_declination = self.declination[0]

        longitude_range *= cos(pi * min_declination / 180.0)

        return f"width: calc(var(--deg) * {longitude_range}); height: calc(var(--deg) * {declination_range});"

    def contains_point(self, x: float, y: float):
        limit_x, limit_y = self.limit_coordinates()
        return abs(x) <= limit_x and abs(y) <= limit_y

    def longitude_offset(self):
        if self.declination[0] == -90 or self.declination[1] == 90:
            return 0.0
        return (self.longitude[0] + self.longitude[1]) / 2.0 - 90.0

    def alpha_degrees(self):
        if self.declination[1] == 90:
            return 0.0
        if self.declination[0] == -90:
            return 180.0

        return 90.0 - (self.declination[0] + self.declination[1]) / 2.0

    def description_html(self):
        if self.description is None:
            return ""
        return f"<p>{self.description}</p>"


def magnitude_to_opacity(magnitude: float) -> float:
    OPAQUE_MAGNITUDE = 0.5
    MAGNITUDE_RANGE = MAX_VISIBLE_MAGNITUDE - OPAQUE_MAGNITUDE
    MIN_VISIBLE_OPACITY = 0x10 / 0xFF

    if magnitude <= OPAQUE_MAGNITUDE:
        return 1.0
    return MIN_VISIBLE_OPACITY ** ((magnitude - OPAQUE_MAGNITUDE) / MAGNITUDE_RANGE)


def get_coordinates(latitude: float, longitude: float):
    """Takes degrees (0..360, 0..90) and returns cartesian coordinates -1..1"""
    phi = pi * (90.0 + latitude) / 180.0
    theta = pi * longitude / 180.0
    radius = 1.0 / tan(phi / 2.0)
    return (radius * cos(theta), radius * sin(theta))


def get_stars():
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
                star = StarData(
                    name,
                    longitude=float(row[21]),
                    declination=float(row[22]),
                    distance=float(row[23]),
                    magnitude=float(row[24]),
                )
            except ValueError:
                continue

            yield star


def main():
    north_hemisphere_html = ""
    south_hemisphere_html = ""

    with open("constellations.json", "r") as jsonfile:
        raw_json = json.loads(jsonfile.read())
        constellations = [ConstellationInfo.from_dict(d) for d in raw_json]

    constellations_inner_htmls = {c.id: "" for c in constellations}

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

        is_in_constellation = False
        for constellation in constellations:
            # center RA on +90, so that changing declination is an X-axis rotation
            phi = pi * (star.longitude - constellation.longitude_offset()) / 180.0
            # center declination on 90
            theta = pi * (90.0 - star.declination) / 180.0
            alpha = pi * constellation.alpha_degrees() / 180.0
            # https://stackoverflow.com/a/5279478/6253337
            theta_prime = acos(
                sin(theta) * sin(phi) * sin(alpha) + cos(theta) * cos(alpha)
            )
            if theta_prime < pi / 2.0:
                y_prime = sin(theta) * sin(phi) * cos(alpha) - cos(theta) * sin(alpha)
                x_prime = sin(theta) * cos(phi)
                phi_prime = atan2(y_prime, x_prime)
                x, y = get_coordinates(
                    90.0 - 180.0 * theta_prime / pi, 180.0 * phi_prime / pi
                )
                if constellation.contains_point(x, y):
                    is_in_constellation = True
                    limit_x, limit_y = constellation.limit_coordinates()
                    html_left = (x / limit_x + 1.0) * 50.0
                    html_top = (y / limit_y + 1.0) * 50.0
                    constellations_inner_htmls[
                        constellation.id
                    ] += f'<div class="star" title="{star.name}" style="left: {html_left}%; top: {html_top}%; opacity: {opacity};"></div>'

        if not is_in_constellation and star.magnitude <= MAX_VISIBLE_MAGNITUDE:
            print(star.name, "is not in any constellations")

    constellations_html = "".join(
        f'<section id="{c.id}"><h2>{c.name}</h2><div class="scroll-container"><div class="region" style="{c.element_style()}">{constellations_inner_htmls[c.id]}</div></div>{c.description_html()}</section>'
        for c in constellations
    )

    contents_html = "".join(
        f'<li><a href="#{c.id}">{c.name}</a></li>' for c in constellations
    )

    legend_html = "".join(
        [
            "<tr>",
            *(
                f'<td><div class="star" style="opacity: {magnitude_to_opacity(m)};"></div></td>'
                for m in range(0, 7)
            ),
            "</tr><tr>",
            *(f"<td>{i}</td>" for i in range(0, 7)),
            "</tr>",
        ]
    )

    template = ""
    with open("template.html", "r") as templatefile:
        template = templatefile.read()

    full_html = (
        template.replace("{{Contents}}", contents_html)
        .replace("{{NorthHemisphere}}", north_hemisphere_html)
        .replace("{{SouthHemisphere}}", south_hemisphere_html)
        .replace("{{Constellations}}", constellations_html)
        .replace("{{Legend}}", legend_html)
    )

    with open("map.html", "w") as output:
        output.write(full_html)


if __name__ == "__main__":
    main()
