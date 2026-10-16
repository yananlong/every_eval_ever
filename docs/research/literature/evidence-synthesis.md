# Evidence synthesis: dependence, heterogeneity, intervals and missingness

This reading ledger supports the [consolidated evidence index proposal](../consolidated-evidence-index.md).
Read date and search cutoff: 2026-10-07. Scope: foundations for dependent reports, heterogeneity, interval targets, missingness, and their transfer limits in EEE. This is a targeted foundational continuation, not an exhaustive systematic review or a claim that no later literature exists.

## Primary sources and reading status

| ID | Canonical publication | Exact version read | Full text / visual status |
|---|---|---|---|
| ES01 | Higgins, Thompson, Deeks & Altman, *Measuring inconsistency in meta-analyses*. BMJ 2003;327:557–560. DOI https://doi.org/10.1136/bmj.327.7414.557 | Published BMJ article, print issue 6 September 2003. Publisher page records online 4 September. | All four PDF pages read, including tables and references. Figures 1–3 visually inspected as rendered page images. No article appendix. |
| ES02 | IntHout, Ioannidis, Rovers & Goeman, *Plea for routinely presenting prediction intervals in meta-analysis*. BMJ Open 2016;6:e010247. DOI https://doi.org/10.1136/bmjopen-2015-010247 | Published article, 12 July 2016, six-page PDF plus primary EuropePMC XML. | Main article and three-page supplementary appendix read in full, including Formulas 1–4, with Figure 1 and all appendix pages visually inspected. Supplementary table W1 not retrieved, and no W1-only numerical claim is used. |
| ES03 | Tipton & Pustejovsky, *Small-Sample Adjustments for Tests of Moderators and Model Fit Using Robust Variance Estimation in Meta-Regression*. JEBS 2015;40(6):604–634. DOI https://doi.org/10.3102/1076998615606099 | Author-hosted 42-page manuscript dated 28 May 2015, https://jepusto.com/files/Tipton-Pustejovsky-F-tests-with-RVE-May-2015.pdf. Published status verified against author publication page and SAGE record. This manuscript is not represented as the final typeset version. | Full manuscript read, including Appendices A–B and data-generating-model note. Figures 1–4 and Table 1 visually inspected, equations in Appendices A–B inspected as page images. Separate online simulation files not retrieved. |
| ES04 | Sterne, White, Carlin, Spratt, Royston, Kenward, Wood & Carpenter, *Multiple imputation for missing data in epidemiological and clinical research: potential and pitfalls*. BMJ 2009;338:b2393. DOI https://doi.org/10.1136/bmj.b2393 | Complete primary EuropePMC XML, plus four-page BMJ print version dated 18 July 2009. Online publication 29 June 2009. Print PDF reproduced at https://qn-scd0.yuketang.cn/pub_notice/1684130121060/sterne2009.pdf?attname=sterne2009.pdf. | Full online text read, including reporting survey and Box 3 that print omits. All print pages visually inspected. Complete XML contains zero `fig` and zero `graphic` elements, so there are no plots to inspect. |

### ES01 — extraction and plot audit

Method: Cochran Q with inverse-variance-style study weights, $I^2=\max(0,(Q-df)/Q)$, illustrated with clinical meta-analyses and 509 Cochrane dichotomous-outcome analyses selected from the first subgroup/analysis with at least two trials having events. This presumes comparable effect scales and meaningful study sampling variances.

Printed numerical anchors: Table 1, p. 558, amantadine: eight studies, Q=12.44, df=7, p=.09, I²=44%, uncertainty interval 0–75%. Antidepressant discontinuation: 135 trials, p=.005 but I²=26% (7–40%). Figure 1, p. 557: pooled OR=.34 (.22–.53), visibly dispersed study estimates. Figure 2, p. 558: histogram has a broken vertical axis and printed 250 at zero, making the tall zero bar unsuitable for estimating relative frequency from height. Figure 3, p. 559: high-quality OR=1.15 (.85–1.55), low-quality OR=1.72 (1.01–2.93). These are printed values, not digitized estimates.

Limitation: proposed 25/50/75% adjectives were tentative, contextual guidance. EEE lacks clinical trial sampling assumptions, and undocumented report noise cannot be decomposed by inserting report count into Q. Text says high-quality I²=15% while Table 2 prints 17%, so avoid that discrepant example.

### ES02 — extraction and plot audit

Method: first eligible meta-analysis per Cochrane intervention review, 2009–2013, at least two studies, 2,009 dichotomous and 1,254 continuous outcomes, HKSJ random effects with empirical-Bayes τ². Target is a future *true study effect* under exchangeability and approximately normal random effects, not a new noisy observation.

Printed anchors: Results/Table 2, pp. 3–4: among 479 significant analyses with I²>0, 347/479=72.4% prediction intervals crossed the null and 97/479=20.3% included the opposite pooled effect. Denominator is selected significant heterogeneous meta-analyses, not all 3,263. Assuming I²=20% in 441 significant zero-estimate analyses was a sensitivity analysis, not newly observed heterogeneity.

Figure 1, p. 4: pooled SMD −.51, CI [−.96,−.07], red prediction bar [−1.60,.58], I²=73.9%, τ²=.1477 printed on plot. Main text rounds τ²=.148 and reports SE=.227, multiplier 2.45 with six df. Visually, the diamond stays below zero while the red bar crosses zero and.51. All endpoint numbers are printed, not visual estimates.

Transfer limit: EEE must define future reporter/setup population and include new-report observation noise when validating against observed scores. Few reports and nonexchangeable new setups weaken predictive coverage. Appendix Formula 1 treats τ² as known and approximates SE from CI width/3.92. Appendix Formula 2 prints 13.6% for the nasal-polyps tail, differing from main-text 14.7%, so that probability is excluded from synthesis.

### ES03 — extraction and plot audit

Method: cluster-robust meta-regression, bias-reduced residual adjustment, five multi-contrast test approximations. Independent study clusters permit within-cluster dependence. Simulation: 6,120 conditions, 10,000 replications each, 10–100 independent studies, correlations 0/.5/.8, I² 0/.33/.5/.75/.9, one–ten effects/study. Appendices describe working covariances/approximate weights and normal quadratic-form moments.

Printed anchors: p. 29/Figure 4, AHZ df span 1.5–10.7 with 20 studies and 13.8–60.5 with 100. p. 35: maximum AHZ Type-I error.0594 at nominal.05 under strong misspecification. Table 1, p. 33: evaluator-independence test with 152 studies changes p=.029 to.073, adjusted df=16.8. These are manuscript values.

Visual audit: Figure 1, p. 25, q=5/α=.05 panel has medians approximately.20 at 10–20 studies and.07 at 100, showing substantial inflation. These medians are visual estimates. Figure 2, p. 27, AH tests become conservative as q grows. Figure 3, p. 28, AHZ points generally lie above diagonal relative to AHB. Figure 4 confirms broad df spread.

Limits: simulations test Type-I error under SMD nulls, not EEE predictive calibration or power. Cluster independence and identifiable regressors remain requirements. Manuscript prose says adjusted p-values are smaller although Table 1 shows larger, so cite the table.

### ES04 — extraction and visual audit

Method: missingness tutorial plus full-text phrase search for “multiple imputation” in NEJM, Lancet, BMJ and JAMA, 2002–2007, identifying 59 original-research articles. Multiple imputation samples plausible completed datasets and combines within/between-imputation uncertainty. MAR is conditional on included observed information, and observed data alone cannot distinguish MAR from MNAR.

Printed anchors: online reporting-survey table: five papers listed imputation variables, 22 reported imputation counts, seven tabulated both complete-case and imputed results. “Practical implications,” print p. 159: QRISK HDL values were 70% missing, with omitted outcome information and extreme imputed cholesterol ratios implicated in the erroneous null association. Online Box 3: costs observed for 115 patients but complete for 82, incremental cost £2,804 (CI £1,236–£4,290) in complete cases versus £2,384 (£833–£3,954) with imputation. This is an illustrative case, not a quantified general correction factor.

Visual status: print pp. 157–160 inspected, including Boxes 1–2, with no plots present. Online XML adds the survey table and Box 3.

Transfer limit: EEE contains structural absence, access limitations and selected nonpublication as well as missing values. Imputation assumptions require a declared eligible cell population, and descriptive missingness predictors do not prove MAR or recover undisclosed scores.

## Implications for the proposal

These are design deductions for EEE, rather than empirical results reported in the four sources. The existing measurement model is useful as a hypothesis, but a connected report graph alone does not identify every coefficient, because a source that always uses one setup makes the source and setup columns collinear even when benchmark cells are shared. Define the target score and reference constraints, inspect the design matrix rank, examine the overlap for each contrast, and show sensitivity to removing a bridge source before claiming separate source or setup effects. When the target is a declared population of reporting setups, the source distribution and weighting rule form part of the estimand, and convenience sampling of published reports can shift that target.

Distinct reporting organizations should be reported as provenance counts, while independent evidence clusters require evidence about original runs, shared predictions, common evaluation harnesses and upstream copying. A resampled organization can still share a run with another organization, and many scores from one run still represent one clustered measurement process. Cluster-robust inference provides a candidate for dependence within defensible independent groups, but crossed dependence across reporters and benchmark families requires its own model or resampling design, and corrected standard errors do not resolve source selection or a rank-deficient design.

An interval for the mean consolidated score, an interval predicting a future latent reporter/setup mean, and an interval predicting a future *observed report* answer different questions. Under a deliberately simplified independent random-intercept model, a future observed-report variance contains the uncertainty of the estimated mean plus reporter/setup heterogeneity plus new-report residual or sampling variance, whereas a mean interval contains only uncertainty about the mean parameter. Correlations and conditioning on a known reporter can change this decomposition, so the production contract should name the prediction target and fitted assumptions rather than copy a clinical formula. This is a proposed EEE decomposition, not a result measured on EEE.

Heterogeneity should first be displayed in the score's interpretable units within genuinely comparable cells, with the number and provenance of reports visible. A robust spread can be useful when sampling variances are absent, although spread is descriptive disagreement rather than an identified partition into noise and true effects. A zero variance estimate from sparse repeats should not produce an independence or consistency label, and tentative clinical I² cutoffs should not determine EEE labels. Documentation support remains a separate property of the evidence, since an unknown setup limits interpretation without establishing the direction of measurement error.

## Search and access ledger

All searches below were run on 2026-10-07, without a lower date bound. Engine 2 was used for discovery and engine 1 for source/access verification. Exact queries, grouped in call order:

1. `Higgins Thompson Deeks Altman Measuring inconsistency meta analyses 2003 full text PMC`
2. `IntHout Ioannidis Rovers Goeman Plea routinely presenting prediction intervals meta analysis 2016 PMC`
3. `Tipton 2015 small sample adjustments robust variance estimation meta regression pdf`
4. `Sterne White Carlin Spratt Royston Kenward Wood Carpenter 2009 multiple imputation missing data epidemiological clinical research potential pitfalls PMC`
5. Engine 1: `"Tipton" "met0000011" pdf small sample adjustments`
6. Engine 1: `"Measuring inconsistency" pdf 2003 Higgins`
7. `"Tipton" "Small sample adjustments" pdf site:columbia.edu`
8. `"Tipton" "Small sample adjustments" pdf site:northwestern.edu`
9. `"Tipton" "Small sample adjustments" pdf site:jepusto.com`
10. `"Tipton" "Small sample adjustments" pdf site:osf.io`
11. `"Plea for routinely presenting prediction intervals" pdf repository`
12. `"Multiple imputation for missing data" "b2393" pdf Bristol`
13. `"Measuring inconsistency" "557" pdf site:ox.ac.uk`
14. `"Multiple imputation" "pitfalls" "Figure" "Sterne" 2009`
15. `"Sterne" "b2393" site:bristol.ac.uk`
16. `"IntHout" "e010247" site:repository.ubn.ru.nl`
17. `"Higgins" "Measuring inconsistency" site:ora.ox.ac.uk/files`
18. `"Measuring inconsistency" pdf site:cam.ac.uk`
19. `"bmjopen-2015-010247supp_appendix.pdf"`
20. `"bmjopen-2015-010247" "Appendix" "Formula"`
21. `"Small-sample adjustments" "1076998615606099" correction erratum`
22. `"Measuring inconsistency in meta-analyses" correction 17 15`

Selected sources above were primary authored papers, with publication status checked against publisher, PubMed or author publication records. Tipton's single-author *Psychological Methods* article DOI 10.1037/met0000011 was identified but not included because a full-text author copy was not retrieved, while the closely related multi-contrast article was available in full with visualizable plots and appendices. Jackson/Riley/White multivariate meta-analysis and later missing-data-framework papers remain useful future candidates, not full-read included sources. ERIC ED562265 is a conference abstract and was excluded as a substitute for the journal paper. Search-result summaries, ResearchGate request pages, autogenerated publication sites, Sci-Hub-linked sites and third-party commentaries were not treated as methodological evidence.

PMC and BMJ HTML opens repeatedly returned reCAPTCHA or 403. A readable cached IntHout HTML page existed at the legacy NCBI URL, while local downloads of EuropePMC `?pdf=render` succeeded for ES01 and ES02. `web.screenshot` returned only a text placeholder with no image content during this review, so these calls were not counted as image inspection. Successful inspection used actual local PNGs generated by PyMuPDF and inspected as actual images. Direct PMC PDF/supplement paths often returned HTML, and checking `%PDF`/opening as a true PDF is necessary because PyMuPDF can also render HTML as a one-page document. Several EuropePMC supplementary ZIP downloads timed out, while a longer retry supplied a complete first ZIP member containing the three-page appendix, recovered by raw DEFLATE extraction with stream EOF confirmed. The recovered PDF opens without repair. The complete appendix was then read and visually inspected. The ZIP also contains image material before supplementary table W1, whose transfer remained incomplete. The ES04 print reproduction was cross-checked against complete primary XML, revealing abbreviated print content rather than assuming the four print pages were the entire online article.
