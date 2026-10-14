# Hispanic Heritage Historical Data Explorer

A Streamlit classroom application for exploring World Bank historical data,
polynomial regression, mathematical functions, and introductory calculus.

## Requirements

- Python 3.10 or newer
- Internet access for World Bank API retrieval
- The dependencies listed in `requirements.txt`

## Run locally

Create and activate a virtual environment if desired.

Install dependencies:

    pip install -r requirements.txt

Start the application:

    python -m streamlit run app.py

Open the local URL printed by Streamlit, usually http://localhost:8501.

## Research setup

The app begins with Mexico and life expectancy as defaults. Change the
research question, country, indicator, degree, sample increment, prediction
horizon, comparison countries, and mathematics pathway in the sidebar.

The requested historical period is the current calendar year minus 70
through the previous calendar year, inclusive. The API may return fewer
than 70 non-null annual observations. Missing values are not fabricated.

Brazil is included as a Latin American comparison. Brazil's official
language is Portuguese; it is not a Spanish-speaking country.

## Editing data

The working table is separate from the original source observations.
Correct invalid years and values before fitting the model. Duplicate years,
non-integer years, non-numeric values, and indicator-bound violations
prevent a fit.

Use Reset to source data to restore the downloaded observations.

Edited values are a user-modified scenario, not World Bank observations.
Keep a record of changes for research reproducibility.

## Model interpretation

The polynomial is fitted using centered time:

    t = year - base year

The degree must be between 3 and 8 and requires at least degree + 1
distinct observations. R-squared and MAE describe the in-sample fit.
A chronological holdout score, when available, is a separate measure.

Polynomial extrapolation can be unstable. The model does not establish
causation, and its predictions should not be treated as official forecasts.
The application does not claim a validated 95% prediction interval.

## Function & Calculus Lab

The lab supports polynomial, rational, exponential, logarithmic, and
trigonometric expressions through a restricted parser. Supported functions
include sin, cos, tan, exp, log, sqrt, and abs. Use ** for powers.

Examples:

    x**2 - 3*x + 1
    (x + 1)/(x - 2)
    exp(-0.3*x)
    log(x)
    sin(x)

Course modes are Honors Algebra 2, Precalculus, and Calculus. Calculus mode
emphasizes first and second derivatives, critical-point candidates,
extrema, and concavity.

Numerical root-finding and sign tests are approximations. They may miss
roots, and they do not provide a complete proof of domain, continuity, or
all extrema for arbitrary functions.

The simulation indicators are illustrative. They are not validated
medical, biomechanical, weather, engineering, or economic simulators.

## GitHub setup

1. Create a GitHub repository.
2. Upload `app.py`, `requirements.txt`, `README.md`, and `sources.md`
   to the repository root.
3. Commit the files to the default branch.
4. Do not commit passwords, API keys, or other credentials. The World Bank
   API endpoints used here do not require an API key.

## Deploy on Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud using your GitHub account.
2. Select **Create app**.
3. Choose the repository and branch.
4. Set the main file path to `app.py`.
5. Deploy the application.
6. Review the application logs if installation or startup fails.

Keep `requirements.txt` in the repository root. After committing changes,
use the Cloud dashboard to check deployment logs and restart the app if
needed.

## Deploy on Render

Create a **Python Web Service** connected to the GitHub repository.

Build command:

    pip install -r requirements.txt

Start command (one line):

    python -m streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT

The service must listen on Render's assigned port. Inspect the Render
build and runtime logs if the deployment fails.

## Verification checklist

- [ ] Check the World Bank API response against the official indicator series.
- [ ] Verify retrieval dates, year coverage, units, and null handling.
- [ ] Confirm that Reset to source data restores the downloaded observations.
- [ ] Try duplicate years, decimal years, non-numeric values, and impossible
      indicator values.
- [ ] Try a degree that exceeds the number of available distinct years.
- [ ] Confirm the displayed polynomial equation uses centered time.
- [ ] Compare R-squared and MAE with independently calculated values.
- [ ] Check the chronological holdout score separately from in-sample metrics.
- [ ] Compare a single-year estimate with the same year in batch estimates.
- [ ] Try malformed custom years and invalid function expressions.
- [ ] Test rational-function singularities and logarithm domain restrictions.
- [ ] Confirm each selector, slider, graph toggle, and comparison option changes
      the intended output.
- [ ] Open the CSV, Excel workbook, and PDF; verify their file types and content.
- [ ] Deploy from GitHub and inspect the hosted app's logs.

## Troubleshooting

### World Bank data is missing

Check the API URL, network connection, HTTP response, indicator code, country
code, and whether that series has observations for the requested years.
A null observation is not equivalent to zero.

### Dependency installation fails

Check the Python version and the complete build log. Install dependencies
in a clean virtual environment before deploying.

### The polynomial fit fails

Check for duplicate or insufficient years, non-finite values, or a degree
that is too high for the number of observations.

### A custom function fails

Use only supported mathematical syntax. Check parentheses, denominators,
logarithm arguments, and the analysis interval.

### The app crashes after editing

Inspect the Streamlit traceback. Verify that the working table contains
both `year` and `value`, with unique integer years and finite numeric values.

### Export errors

Check the traceback, dependency installation, and whether the export buffers
were created successfully. Open the downloaded workbook in spreadsheet
software and the PDF in a PDF reader.

## Academic integrity and limitations

Cite the original World Bank indicator series in your research. Distinguish
historical observations from fitted values and extrapolations. Do not invent
historical causes from a correlation or a polynomial curve.

Before claiming all requested functionality has been verified, complete the
checklist and test the app in a local environment and the deployed environment.
