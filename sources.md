# Data Sources and Indicator Definitions

## Primary source

World Bank, World Development Indicators (WDI).

- Main portal: https://data.worldbank.org/
- API documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- Country/indicator API documentation:
  https://datahelpdesk.worldbank.org/knowledgebase/articles/898590
- API format: JSON
- API base URL: https://api.worldbank.org/v2

The app requests annual observations for the selected country and indicator.
The requested period is the current calendar year minus 70 through the
previous calendar year, inclusive.

API pattern:

    https://api.worldbank.org/v2/country/MX/indicator/SP.DYN.LE00.IN?date=1956:2025&format=json

The years in this example illustrate the URL format, not a claim that every
year is available. The application calculates the actual period at runtime.

Country codes:
- Mexico: MX
- Brazil: BR
- Argentina: AR
- Colombia: CO
- Chile: CL
- Peru: PE
- Venezuela: VE
- Ecuador: EC
- Uruguay: UY

## Indicator catalog

Indicator metadata and series identifiers are provided by the World Bank.
Use each series page and its metadata to confirm its definition and coverage.

| Indicator | World Bank code | Unit / interpretation |
|---|---|---|
| Life expectancy at birth | SP.DYN.LE00.IN | Years |
| Unemployment, national estimate | SL.UEM.TOTL.NE.ZS | Percentage of total labor force |
| GDP per capita | NY.GDP.PCAP.CD | Current US dollars per person |
| Crude birth rate | SP.DYN.CBRT.IN | Births per 1,000 people per year |
| Net migration | SM.POP.NETM | Net number of migrants |
| Intentional homicide rate | VC.IHR.PSRC.P5 | Rate per 100,000 people |
| Consumer price inflation | FP.CPI.TOTL.ZG | Annual percentage change |
| Central government debt | GC.DOD.TOTL.GD.ZS | Percentage of GDP |
| Total reserves including gold | FI.RES.TOTL.CD | Current US dollars |
| External balance on goods and services | NE.RSB.GNFS.ZS | Percentage of GDP |

## Direct series links

- Life expectancy:
  https://data.worldbank.org/indicator/SP.DYN.LE00.IN
- National-estimate unemployment:
  https://data.worldbank.org/indicator/SL.UEM.TOTL.NE.ZS
- GDP per capita:
  https://data.worldbank.org/indicator/NY.GDP.PCAP.CD
- Crude birth rate:
  https://data.worldbank.org/indicator/SP.DYN.CBRT.IN
- Net migration:
  https://data.worldbank.org/indicator/SM.POP.NETM
- Intentional homicide rate:
  https://data.worldbank.org/indicator/VC.IHR.PSRC.P5
- Consumer price inflation:
  https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG
- Central government debt:
  https://data.worldbank.org/indicator/GC.DOD.TOTL.GD.ZS
- Total reserves including gold:
  https://data.worldbank.org/indicator/FI.RES.TOTL.CD
- External balance on goods and services:
  https://data.worldbank.org/indicator/NE.RSB.GNFS.ZS

## Interpretation cautions

GDP per capita is GDP divided by midyear population. It is not average
household wealth, median income, or household income.

Crude birth rate is a population rate, not a count of births.

Net migration describes a net migration measure. It is not a count of
people who emigrated.

Consumer price inflation is an annual percentage change in the consumer
price index, not the price level itself.

A percentage of GDP, such as government debt or the external balance, is
not a dollar amount.

Series definitions, methodology, historical coverage, and country
availability may change. Read the metadata for the exact series being
used, especially before interpreting unusual observations.

## Missing data and reproducibility

The API can return null values or no observations for a particular year.
The application omits null observations from the fitting table; it does
not replace missing observations with zero, interpolate them, or generate
random data.

Record the country, indicator code, retrieval date, actual coverage,
observation count, and whether the working data were edited. The editable
working table must be treated as a separate scenario when its values differ
from the retrieved observations.

## Mathematical references

The app uses NumPy polynomial fitting and SymPy symbolic differentiation.

- NumPy polynomial documentation:
  https://numpy.org/doc/stable/reference/routines.polynomials.html
- scikit-learn regression metrics:
  https://scikit-learn.org/stable/modules/model_evaluation.html
- SymPy calculus documentation:
  https://docs.sympy.org/latest/tutorials/intro-tutorial/calculus.html
- Streamlit documentation:
  https://docs.streamlit.io/
- ReportLab documentation:
  https://docs.reportlab.com/
- XlsxWriter documentation:
  https://xlsxwriter.readthedocs.io/
