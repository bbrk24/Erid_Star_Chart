# Erid Star Chart

This repository contains a spreadsheet (EridStarChart.ods) which calculates the positions of stars as seen from the 40 Eridani system, and a Python script and HTML template which can be used to generate the map. The generated map is a standalone HTML file with no JavaScript or external links.

## Generating the star map

### Converting the spreadsheet to CSV

The Python script assumes the relevant columns have the values as numbers, not formulas.

1. Open EridStarChart.ods in LibreOffice Calc.
2. In the menu at the top of the window, go to File > Save a Copy...
3. In the window that pops up, change the File type to Text CSV (.csv), then click Save.
4. In the following pop-up window, adjust the settings if necessary:
   - Character set: Unicode (UTF-8)
   - Field delimiter: ,
   - String delimiter: "
   - Uncheck "Save cell formulas instead of calculated values"
   - Uncheck "Fixed column width"

### Generating the HTML from the CSV

Run the Python script generate_html.py.
