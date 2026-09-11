#!/usr/bin/env python3

import csv
import json
from dataclasses import dataclass
from math import acos, atan2, cos, hypot, pi, sin, tan
from typing import Any, Literal


@dataclass
class StarData:
    name: str
    longitude: float
    declination: float
    distance: float
    magnitude: float


@dataclass
class ConstellationInfo:
    id: str
    name: str
    declination: tuple[float, float]
    longitude: tuple[float, float]
    shape: Literal["rectangle"]
    description: str | None

    @classmethod
    def from_dict(cls, d: Any):
        if not isinstance(d, dict):
            raise TypeError()

        id = d["id"]
        name = d["name"]
        declination = d["declination"]
        longitude = d["longitude"]
        shape = d["shape"]

        if (
            not isinstance(id, str)
            or not isinstance(name, str)
            or not isinstance(declination, list)
            or not isinstance(longitude, list)
        ):
            raise TypeError()

        description = None
        if "description" in d:
            description = d["description"]
            if not isinstance(description, str):
                raise TypeError()

        if (
            len(longitude) != 2
            or longitude[0] <= -360.0
            or longitude[1] > 360.0
            or longitude[0] >= longitude[1]
            or longitude[1] - longitude[0] > 360.0
        ):
            raise ValueError("Invalid longitude")

        if (
            len(declination) != 2
            or declination[0] < -90.0
            or declination[1] > 90.0
            or declination[0] >= declination[1]
        ):
            raise ValueError("Invalid declination")

        if shape not in ("rectangle",):
            raise ValueError("Invalid shape")

        return cls(id, name, tuple(declination), tuple(longitude), shape, description)

    # FIXME: Something about this doesn't handle Ursa Major quite correctly
    def limit_coordinates(self):
        match self.shape:
            case "rectangle":
                declination_range = self.declination[1] - self.declination[0]
                longitude_range = self.longitude[1] - self.longitude[0]

                if self.declination[1] >= 0.0 and self.declination[0] <= 0.0:
                    min_declination = 0.0
                elif self.declination[1] < 0.0:
                    min_declination = -self.declination[1]
                else:
                    min_declination = self.declination[0]

                longitude_range *= cos(pi * min_declination / 180.0)

                limit_x, limit_y = get_coordinates(
                    90.0 - hypot(declination_range / 2.0, longitude_range / 2.0),
                    180.0 * atan2(declination_range, longitude_range) / pi,
                )

                return (abs(limit_x), abs(limit_y))
        raise ValueError()

    def element_style(self):
        match self.shape:
            case "rectangle":
                declination_range = self.declination[1] - self.declination[0]
                longitude_range = self.longitude[1] - self.longitude[0]

                if self.declination[1] >= 0.0 and self.declination[0] <= 0.0:
                    min_declination = 0.0
                elif self.declination[1] < 0.0:
                    min_declination = -self.declination[1]
                else:
                    min_declination = self.declination[0]

                return f"width: {longitude_range * cos(pi * min_declination / 180.0)}em; height: {declination_range}em;"
        raise ValueError()

    def contains_point(self, x: float, y: float):
        match self.shape:
            case "rectangle":
                limit_x, limit_y = self.limit_coordinates()
                return abs(x) <= limit_x and abs(y) <= limit_y
        raise ValueError()

    def longitude_offset(self):
        return (self.longitude[0] + self.longitude[1]) / 2.0 - 90.0

    def alpha_degrees(self):
        match self.shape:
            case "rectangle":
                return 90.0 - (self.declination[0] + self.declination[1]) / 2.0
        raise ValueError()

    def description_html(self):
        if self.description is None:
            return ""
        return f"<p>{self.description}</p>"

    def classnames(self) -> str:
        match self.shape:
            case "rectangle":
                return "region"
        raise ValueError()


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
                    limit_x, limit_y = constellation.limit_coordinates()
                    html_left = (x / limit_x + 1.0) * 50.0
                    html_top = (y / limit_y + 1.0) * 50.0
                    constellations_inner_htmls[
                        constellation.id
                    ] += f'<div class="star" title="{star.name}" style="left: {html_left}%; top: {html_top}%; opacity: {opacity};"></div>'

    constellations_html = "".join(
        f'<section id="{c.id}"><h2>{c.name}</h2><div class="{c.classnames()}" style="{c.element_style()}">{constellations_inner_htmls[c.id]}</div>{c.description_html()}</section>'
        for c in constellations
    )

    template = ""
    with open("template.html", "r") as templatefile:
        template = templatefile.read()

    full_html = (
        template.replace("{{NorthHemisphere}}", north_hemisphere_html)
        .replace("{{SouthHemisphere}}", south_hemisphere_html)
        .replace("{{Constellations}}", constellations_html)
    )

    with open("map.html", "w") as output:
        output.write(full_html)


if __name__ == "__main__":
    main()
