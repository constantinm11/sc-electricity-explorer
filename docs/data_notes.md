# Interpretation Notes

- **PLL** means Potential Large Load. Santee’s PLL series is a source-published forecast category, not a list of public project announcements.
- **Annual energy** measures electricity over a year (MWh/GWh). **Peak demand** measures the maximum power requirement at a point in time (MW). They are not interchangeable.
- Historical values and forecasts may overlap in calendar year but retain separate source status, vintage, and assumptions.
- Provider and planning-system totals remain at their reported geography. The county layer supplies provider/service context only; no utility total is divided among counties.
- Santee direct residential and commercial are combined because the primary source combines them.
- Processed 2018, 2019, and 2022 Santee category data applies provisional rule `SANTEE_HIST_001`; the raw values are retained and Central non-coincident peak is untouched.
- Wholesale, cooperative, municipal, and retail records can refer to the same underlying load. They must not be summed without a supported de-duplication method.
- Missing public facts display as **Not publicly disclosed**, never as an estimated value or zero.

See `methodology.md` and `workbook_audit.md` for the complete release rules.
