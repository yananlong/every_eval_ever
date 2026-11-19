# Composite construction and specification sensitivity

Read and checked on 2026-10-07. This lane supplies foundational methods for SACI and the weighting diagnostics, with implications for EEE stated as design inferences. Numerical examples come from the sources' own applications, with no EEE results inferred from those applications.

## CO01 — Saisana, Saltelli and Tarantola (2005)

**Publication:** *Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators*, JRSS A 168(2), 307–323. [Canonical institutional publication record](https://publications.jrc.ec.europa.eu/repository/handle/JRC31318). [Author-hosted full text](https://www.andreasaltelli.eu/file/repository/JRSS_2005.pdf). Entire 17-page article read, all four figures visually inspected using locally rendered PDF pages 9, 11, 12 and 14.

The application combines eight technology indicators for 72 countries, sampling two normalizations, two weighting schemes and expert-derived weights through 11,264 model evaluations, with Sobol' first-order and total-effect indices locating influential choices (§§2–3). The weight distributions come from pilot surveys of 20 institute colleagues who had no stakeholder role, and raw indicator values are treated as error-free (§3), making the distribution conditional on elicitation and construction assumptions.

The Netherlands moves from sixth to ninth and Singapore from tenth to sixth, with Singapore ahead in approximately 65% of simulated comparisons (§4.1–4.2, Fig. 3). Table 3 attributes 52% of pairwise-difference variance to first-order effects and the remainder to interactions. Figures 1–4 show elicitation-dependent weights, overlapping construction ranges, a signed pairwise-difference distribution, and weight regions associated with reversals. These are construction-sensitivity results, providing a direct precedent for SACI while leaving measurement-error calibration and future-update prediction to separate tests.

## CO02 — Steegen, Tuerlinckx, Gelman and Vanpaemel (2016)

**Publication:** *Increasing Transparency Through a Multiverse Analysis*, Perspectives on Psychological Science 11(5), 702–712. [Canonical DOI](https://doi.org/10.1177/1745691616658637). [Author-hosted article](https://sites.stat.columbia.edu/gelman/research/published/multiverse_published.pdf), [supplement](https://sites.stat.columbia.edu/gelman/research/published/multiverse_sup.pdf). Entire article and nine-page supplement read, main Figures 1 and 2 visually inspected on PDF pages 5 and 7.

The reanalysis starts with studies enrolling 275 and 502 women, varying fertility coding, cycle estimation, relationship classification and exclusions while retaining the original ANOVA/logistic analyses. Removing inconsistent combinations leaves 120 and 210 constructed datasets (pp. 703–706), and the supplement documents previously recoded responses, reconstructed variables, missing data and discrepancies between stated and applied exclusions.

Only 7/120 constructions yield a significant Study 1 religiosity interaction, whereas 88/210 (42%) do so in Study 2 (p. 707). Figure 1 shows broad variation across outcomes and Figure 2 locates sensitivity in relationship and fertility coding, making the exact printed counts preferable to estimating histogram mass. The discussion explicitly treats multiverse analysis as transparency and diagnosis, without a single evidential score or robustness threshold (p. 710). SACI can disclose construction dependence even if H4 fails, while the choice set and its enumeration require an explicit rationale.

## CO03 — Simonsohn, Simmons and Nelson (2020)

**Publication:** *Specification curve analysis*, Nature Human Behaviour 4, 1208–1214. [Canonical DOI](https://doi.org/10.1038/s41562-020-0912-z), [publisher correction](https://doi.org/10.1038/s41562-020-00974-w). [Author-hosted full text](https://faculty.wharton.upenn.edu/wp-content/uploads/2016/11/33-Simonsohn-Simmons-Nelson-2020.pdf), [publisher supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41562-020-0912-z/MediaObjects/41562_2020_912_MOESM1_ESM.pdf). Entire main article, reporting summary and 25-page supplement read. Main Figures 1–3 and supplementary Figures 5–8 visually inspected. The correction restores missing notation arrows, and no claim relies on the malformed extracted notation.

The method selects justified, valid, nonredundant specifications, displays their results and performs joint inference with shared null resamples, accounting for dependence across specifications. The hurricane example evaluates 1,728 constructions, with 37 significant results yielding a joint P value of .850 under 500 shuffled datasets (Table 2), while 85/90 discrimination specifications are significant with joint P < .002. Figure 2 displays a subset of constructions, and Figure 3 contrasts ordered observations with null curves. Supplementary Figure 7 prints power of 58%, 71% and 75% for three joint tests in its simulation.

These conditional resampling results require valid null construction, while equal specification weighting is acknowledged as a limitation. For SACI, specification shares need declared weights and deduplication, with inference separated from the descriptive specification range.

## CO04 — Paruolo, Saisana and Saltelli (2013)

**Publication:** *Ratings and rankings: voodoo or science?*, JRSS A 176(3), 609–634. [Canonical DOI](https://doi.org/10.1111/j.1467-985X.2012.01059.x). [Full text read](https://arxiv.org/pdf/1104.3009), a 28-page author manuscript carrying a 2018 typesetting date. Entire manuscript and mathematical appendix read, Figures 1–5 visually inspected on its pages 9, 11–13 and 21. Publisher metadata describes six applications, matching this manuscript, although older indexed abstracts describe five. Locators and numbers below belong to the accessed manuscript.

Pearson's correlation ratio measures variance-based association between each component and the index, estimated with local-linear kernels using cross-validation and direct plug-in bandwidths, with an inverse-weight problem analysed under a linear approximation (§3). Six applications include 142 complete-case countries for 2009 HDI and 169 for 2010 HDI. Table 5 reports cross-validation maximum discrepancies of .63 and .07 respectively, with .91 for SSI. Figures 1–4 expose bandwidth dependence and Figure 5 distinguishes nominal weights from normalized main effects, whose sensitivity bounds are not sampling confidence intervals.

The manuscript contains conflicting SSI and summary discrepancy values, so Table 5 supplies the reported comparison. Association-based main effects can overlap under dependence, and complete-case analysis limits transfer to selected EEE coverage. Family-equal coefficients therefore require an empirical influence audit before being described as equal information or importance.

## Search and screening log

All searches occurred on 2026-10-07, using public web search followed by primary publisher, institutional or author full texts. Exact queries were:

- `OECD JRC Handbook Constructing Composite Indicators 2008 pdf uncertainty sensitivity analysis`
- `Steegen Tuerlinckx Gelman Vanpaemel 2016 Increasing Transparency Through a Multiverse Analysis pdf`
- `Simonsohn Simmons Nelson 2020 Specification curve analysis pdf`
- `Saisana Saltelli Tarantola 2005 uncertainty sensitivity composite indicators pdf`
- `Steegen 2016 multiverse Gelman pdf stat columbia`
- `Paruolo Saltelli Saisana 2013 Ratings rankings voodoo science published pdf`
- `"Publisher Correction" "Specification curve analysis" 2020 figure`

The four included works cover construction uncertainty, transparent choice enumeration, dependence-aware joint inference and effective influence, with backward expansion from Saisana to weighting diagnostics and publisher correction checks for Simonsohn. OECD/JRC's 2008 handbook was located but excluded from the included reading corpus because the primary papers provide the narrower methods required here, and the handbook was not fully read. Search results also identified *Modeling the Machine Learning Multiverse* (2022), *Specification analysis for technology use and teenager well-being* (2022), and *Making Uncertainty Visible* (2026), which remain screened candidates requiring full-text review before any substantive claim is drawn from them. No withheld recall test, exhaustive venue census or corpus-wide forward citation search was performed.

## Revision implications

SACI should define a versioned, nonredundant set of index specifications and a declared measure over that set, reporting a share of specifications that support a stated comparison or top-k membership. A sampling or posterior probability requires a separate model and calibration target, and a specification range retains descriptive value even when future-update stability cannot be predicted. Weight audits should compare nominal family coefficients with observed influence because normalization, dispersion and covariance can shift the aggregate's effective emphasis, with sample/population choices kept visible throughout the audit.
