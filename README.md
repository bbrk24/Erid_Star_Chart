# Erid Star Chart

This repository contains a spreadsheet (EridStarChart.ods) which calculates the positions of stars as seen from the 40 Eridani system, and a Python script and HTML template which can be used to generate the map. The generated map is a standalone HTML file with no JavaScript or external links.

## Generating the star map

### Converting the spreadsheet to CSV

The Python script assumes the relevant columns have the values as numbers, not formulas.

#### Using the GUI

1. Open EridStarChart.ods in LibreOffice Calc.
2. In the menu at the top of the window, go to File > Save a Copy...
3. In the window that pops up, change the File type to Text CSV (.csv), then click Save.
4. In the following pop-up window, adjust the settings if necessary:
   - Character set: Unicode (UTF-8)
   - Field delimiter: ,
   - String delimiter: "
   - Uncheck "Save cell formulas instead of calculated values"
   - Uncheck "Fixed column width"
5. Click "OK" to write the CSV.

#### Using the CLI

```sh
soffice --headless --convert-to csv EridStarChart.ods
```

### Generating the HTML from the CSV

Run the Python script generate_html.py.

## Constellation JSON format

The Python script has no intrinsic knowledge of constellations. Instead, it generates the detail views and table of contents based on [constellations.json](./constellations.json). The JSON file is an array of objects, where each object follows this format:

- `id`: HTML id of the `<section>`, used for linking from the table of contents.
- `name`: The name of the constellation, as shown in the webpage. HTML entities (e.g. `&ouml;`) may be used.
- `declination`: A pair of integers representing the declination (in degrees) of the top-center and bottom-center points of the detail view. Each number must be between -90 and 90 (inclusive).
- `longitude`: A pair of integers representing the right ascension of the right-center and left-center points of the detail view. Each number must be between -359 and 360 (inclusive), but negative numbers should only be used for constellations that straddle the prime meridian.
- `description` (optional): A paragraph shown below the detail view. Full HTML may be used.

Because the lines of declination and right ascension are curved on the detail view, the corners may have declination or RA values outside the specified range, or may not cover the entire specified range of declination or RA.

If the declination is of the form `[-90, x]` or `[x, 90]`, the detail view is handled specially, and instead portrays a zoomed-in image of the center of the appropriate hemisphere map.
