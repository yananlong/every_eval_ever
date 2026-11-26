# OpenReview forum 7ChRYhe6kG: reviews, responses, meta-review and decision (verbatim)

Paper: Benchmark Prediction with Sparse and Unpaired Cached Responses (ICLR 2027 Conference Submission 26519)
Forum: https://openreview.net/forum?id=7ChRYhe6kG
Source: forum_notes.json (raw API response, same directory). Field values are copied as returned; no edits.
Times are shown in UTC from tcdate (creation) and mdate (last modification) in milliseconds.

## Official reviews (with threads)

### Review 1: Reviewer_dSNB
- note id: dLw67clZAX
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Review
- signature: ICLR.cc/2027/Conference/Submission26519/Reviewer_dSNB
- created (tcdate): 2026-10-08 09:57:22 UTC
- modified (mdate): 2026-11-19 05:37:18 UTC
- replyto: 7ChRYhe6kG

**paper_summary**:

```text
This paper proposes the Product Kernel Perspective Space (PKPS), a framework for predicting benchmark scores from sparse and unpaired cached model responses. The work aims to address the dependence of existing benchmark prediction methods on shared queries or aggregate scores. The authors first construct pairwise model affinities by weighting response similarity with query similarity. Then they embed the resulting model distances using multidimensional scaling and perform score prediction with nearest-neighbor regression. They further provide concentration and query-efficiency analyses for PKPS. Experiments on synthetic data, HELM-Lite, and Every Eval Ever demonstrate its effectiveness in query-efficient evaluation and score-matrix completion.
```

**presentation**:

```text
1
```

**informativeness**:

```text
1
```

**soundness**:

```text
2
```

**critical_strengths**:

```text
1. Although the core method is relatively simple, the authors provide extensive mathematical proof to establish a theoretical foundation for the paper.
2. The motivation of this work is inspiring, as sparse and unpaired evaluation records are common in practical model benchmarking.
```

**critical_weaknesses**:

```text
1. The manuscript structure need improvement. Placing Related Work in Section 1.1 is uncommon, a standalone section would improve the organization. Many key equations in Appendix D are unnumbered, making the proofs difficult to reference.
2. The theoretical analysis relies on seven assumptions (Assumptions 1-7) to establish guarantees for an idealized setting. These assumptions are not verified on the real benchmarks, and the guarded selector required by Theorem 2 is not clearly used in the experiments.
3. The presentation lacks a clear logical focus. The core method consists of product-kernel similarity, multidimensional scaling, and nearest-neighbor regression, but the extensive mathematical derivations obscure this relatively simple pipeline and make the paper difficult to follow for human.
4. The experimental validation is limited to synthetic data and two benchmark suites. More experiments on larger model collections and different embedding models are needed.
5. The paper lacks a clear overview diagram of the complete PKPS pipeline.
```

**questions_for_authors**:

```text
See weaknesses, if the authors can adequately address my concerns, I would consider raising my score.
```

**flag_for_ethics_review**:

```text
No
```

**rating**:

```text
2
```

**confidence**:

```text
3
```

### Author response (answers dLw67clZAX, depth 2)
- note id: kfHInn7ikf
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-11 20:03:20 UTC
- modified (mdate): 2026-11-11 20:03:20 UTC
- replyto: dLw67clZAX

**title**:

```text
Initial response (1/2)
```

**comment**:

```text
Thank you for taking the time to review our paper. We appreciate you noting that the motivation of our work is inspiring. We attempt to address your noted weaknesses / questions inline below:

> Placing Related Work in Section 1.1 is uncommon. Many key equations in Appendix D are unnumbered.

We will move the related works to their own section. We will also make sure that all referenced equations are numbered. 

> The theoretical analysis relies on seven assumptions.

Yes. Some of the assumptions are very standard across all analytical settings (e.g., Assumption 1 == the data is iid), for multi-dimensional scaling (e.g., Assumption 4 == eigengap in the dissimilarity matrix), or for proving query efficiency (e.g., Assumption 5 == the embeddings capture the score function well). 

Several hold by construction (e.g., Assumption 2 == bounded kernels and embeddings), and we checked others on our data using the $ m $-query samples ($ m \in \{2, 8\} $). The cross-model query-kernel mass (Assumption 3) is $ 0.58 > 0 $ on HELM and $ 0.88 > 0 $ on EEE. The 8th eigenvalue of the double-centered distance matrix (spectral identifiability) is 13–26% (HELM) and 3–7% (EEE) of the largest, separated from the 9th, with no negative eigenvalues (Assumption 4). Pairing deficiency approximately holds by construction: models share 2.7–11% (HELM) and 1.1–4.4% (EEE) of their queries (Assumption 7). The rest are standard idealizations in the analysis of nearest-neighbor methods.

Lastly, we introduced the guarded selector as a theoretical device and did not originally include it in the implementation of our method. We have re-run our analysis with the guarded selector with 95% confidence. The average absolute difference in MAE with and without the guarded selector is 0.001 (at most 0.004) across both suites and $ m \in \{1, 2, 8, 32\} $. We will note this in the main text.

> The presentation lacks a clear logical focus.

We have distilled the narrative flow to a few paragraphs:

Evaluation is expensive. Benchmark prediction attempts to mitigate this cost. There are two main types of benchmark prediction. We describe both problems as instances of a more general problem.

One new(er) way to tackle benchmark prediction is by using representations of the models and learning a simple regression function on them. Historically, these methods have required paired data to build the representations (DKPS). 

We are the first to describe DKPS-like methods as the product of a query kernel and a response kernel. With a strictly positive query kernel, we are able to use this family of representations for benchmark prediction in sparse and unpaired regimes. 

Theoretically, we first show that PKPS representations of the models behave well (i.e., concentrate / Theorem 1). We then show that regression using PKPS representations is never worse than using DKPS representations. Finally, we show that there exists a setting where regression using PKPS representations is better than using DKPS representations.

We then investigate if / when PKPS is an empirically competitive option for benchmark prediction. We include the synthetic data to be able to explore the trade-offs in highly controlled settings. We then include results on two of the largest public benchmark repositories with item-level response information before concluding.

We hope that this description / summary clears up any confusion about the logical focus of the paper. If it does, we will plan to add a similar description at the end of the introduction to better prepare readers.
```

### Author response (answers kfHInn7ikf, depth 3)
- note id: A1AaAgtk2N
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-11 20:03:48 UTC
- modified (mdate): 2026-11-11 20:03:48 UTC
- replyto: kfHInn7ikf

**title**:

```text
Initial response (2/2)
```

**comment**:

```text
> More experiments on larger model collections and different embedding models are needed.

>> Larger model collections

PKPS needs item-level responses, and most large public leaderboards only release aggregate benchmark scores. Evaluating PKPS also requires the full scores of every target model, so within each repository we use the largest fully evaluated block: 93 models × 18 tasks for HELM and 45 models × 16 tasks for EEE. EEE as a whole covers 165 models and 36 benchmarks, but only 15% of (model, benchmark) pairs have been evaluated, so a larger fully evaluated block is not available.

Several larger collections exist but are not suitable for our setting. Leaderboards such as Artificial Analysis (Artificial Analysis, 2026) report only aggregate scores. Arena-style platforms such as Chatbot Arena (Chiang et al., 2024) collect pairwise human preferences, so there is no per-model ground-truth score on a fixed task to predict.

We found one other “large” public benchmark suite: The Open LLM Leaderboard (v1; Beeching et al., 2023). It is not ideal in that the tasks it contains are either largely multiple choice or true / false. In any case, we considered 367 models from 150 families (a family is the organization of the root base model, with at most 5 fine-tunes per base model and near-duplicate models removed) and 16 tasks, with a pool of 100 queries per task and the full-task score as the target. As with HELM and EEE, we induce sparsity and unpairedness by subsampling each model's queries. Reported results are average MAE over 16 seeds using the “correctness” response kernel (see our response to Reviewer e8LY):

||m=1|2|8|
|-|-|-|-|
|Sample|.387|.265|.120|
|DKPS|.168|.092|.045|
|PKPS|.079|.061|.044|
|IRT (regularized Rasch)|.147|.134|.092|
|IRT + PKPS|.079|.061|.043|
|LRMC + sample|.102|.085|.062|
|LRMC + sample + PKPS|.079|.061|.043|

PKPS is the most accurate method at m = 1 and 2 and matches DKPS at m = 8. PKPS outperforms all other reported baselines. We will add these results to the appendix.

>> Different embedding models

We repeated the EEE query-efficiency experiment with four additional frontier embedding models, eight smaller open embedding models (8M to 600M parameters), and the "correctness" response kernel that needs no response embedding. For each embedding model, the response PCA dimension and the MDS dimension are selected by the same cross-validation used for the bandwidth (for both PKPS and DKPS). Reported results are average MAE over 16 seeds:

||m=1|2|8|
|-|-|-|-|
|Sample|.224|.164|.081|
|DKPS (gemini-embedding-001)|.114|.108|.068|
|PKPS: gemini-embedding-001|.068|.063|.060|
|PKPS: OpenAI text-embedding-3-large|.075|.065|.060|
|PKPS: Gemini-embedding-2|.074|.068|.060|
|PKPS: Cohere embed-5-pro|.079|.069|.064|
|PKPS: Voyage-4-large|.089|.074|.067|
|PKPS: potion-8M|.077|.069|.061|
|PKPS: all-MiniLM-L6 (23M)|.092|.075|.065|
|PKPS: bge-small (33M)|.084|.072|.063|
|PKPS: nomic-embed-v1.5 (137M)|.087|.070|.065|
|PKPS: jina-v5-nano (212M)|.098|.075|.064|
|PKPS: embeddinggemma-300M (303M)|.101|.078|.067|
|PKPS: Qwen3-Embedding-0.6B (596M)|.085|.065|.059|
|PKPS: jina-v5-small (596M)|.089|.069|.060|
|PKPS: correctness kernel|.071|.059|.044|

PKPS outperforms the sample score and DKPS (using the same embedding model) for every embedding model and budget. Performance varies with the embedding model at the smallest budget (.068 to .101 at m=1) and much less at m=8 (.059 to .067). The correctness kernel, which needs no response embedding, is competitive at m=1 and the most accurate at $ m \ge 2 $. We will add these results to the appendix.

> The paper lacks a clear overview diagram of the complete PKPS pipeline.

PKPS is a method to obtain low-dimensional representations of models. We describe the process relative to standard DKPS in Figure 1.

As you point out, given these representations we use a simple regression technique for benchmark prediction. This is described in the first paragraph of Section 3.2: "Inference using the PKPS is a two-step statistical problem: first embed the models, then train a decision function that uses the representations as proxies for the models."

We think that the combination of Figure 1 and the description of the process is sufficient but are happy to include a full diagram of the process if you think it is necessary!

---

Thank you again for taking the time to review our paper! Please let us know if we were able to address your questions / concerns.

References

Artificial Analysis. “AI Model & API Providers Analysis.” Artificial Analysis, 2026, artificialanalysis.ai. Accessed 11 Nov. 2026.

Beeching, Edward, et al. "Open LLM Leaderboard (2023-2024)." Hugging Face, 2023, huggingface.co/spaces/open-llm-leaderboard-old/open_llm_leaderboard.

Chiang, Wei-Lin, et al. "Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference." Proceedings of the 41st International Conference on Machine Learning, PMLR, vol. 235, 2024.
```

### Author response (answers dLw67clZAX, depth 2)
- note id: xsYNzRHndK
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-18 20:05:08 UTC
- modified (mdate): 2026-11-18 20:05:08 UTC
- replyto: dLw67clZAX

**title**:

```text
summary of initial response
```

**comment**:

```text
Unfortunately we did not get the chance to engage with you during the reviewer-author discussion period. We briefly summarize our response to each of your points above:

> Placing Related Work in Section 1.1 is uncommon. Many key equations in Appendix D are unnumbered.

We will move the related work to its own section and number all referenced equations.

> The theoretical analysis relies on seven assumptions.

We explained which assumptions are standard (iid data, an eigengap for MDS, embeddings that capture the score) or hold by construction, and checked others on our data. The population overlap is 0.58 (HELM) and 0.88 (EEE), there is a clear eigengap after the 8th eigenvalue with no negative eigenvalues, and models share only 2.7–11% (HELM) and 1.1–4.4% (EEE) of their queries. Adding the guarded selector to our implementation changes MAE by 0.001 on average (at most 0.004).

> The presentation lacks a clear logical focus.

We condensed the narrative (problem, unified framing, theory, experiments) to a few paragraphs and will add a similar summary at the end of the introduction.

> More experiments on larger model collections are needed.

We added the Open LLM Leaderboard (367 models from 150 families, 16 tasks) with the correctness response kernel. PKPS is the most accurate method at $m = 1$ and $2$ (e.g., $m = 1$: 0.079 vs. 0.102 for LRMC + sample) and competitive throughout.

> More experiments on different embedding models are needed.

We repeated the EEE experiment with four frontier and eight smaller open embedding models (8M to 600M parameters) and the correctness response kernel, with dimensions selected by cross-validation for each. PKPS outperforms the sample score and DKPS for every embedding model and budget. MAE ranges from 0.068 to 0.101 at $m = 1$ and from 0.059 to 0.067 at $m = 8$.

> The paper lacks a clear overview diagram of the complete PKPS pipeline.

We pointed to Figure 1 and the first paragraph of Section 3.2, which describe the two-step pipeline, and offered to add a full diagram if needed.

---
We believe we have adequately addressed your initial weaknesses and questions & we hope these summaries make it easier for you to assess our original response.
```

### Reviewer reply (answers xsYNzRHndK, depth 3)
- note id: 86iBE4plOr
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Reviewer_dSNB
- created (tcdate): 2026-11-19 04:32:31 UTC
- modified (mdate): 2026-11-19 04:32:31 UTC
- replyto: xsYNzRHndK

**comment**:

```text
Thank you for the response and additional experiments. The new results on larger model collections and different embedding models have addressed several of my concerns and strengthened the experimental validation.

However, some concerns remain regarding the methodological novelty and the reliance on artificially simulated sparsity rather than naturally incomplete evaluation data. The overall presentation could also be further improved.

I appreciate the authors' efforts in addressing my comments.
```

### Author response (answers 86iBE4plOr, depth 4)
- note id: uxGr4GA2Ct
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-19 05:27:42 UTC
- modified (mdate): 2026-11-19 05:29:48 UTC
- replyto: 86iBE4plOr

**comment**:

```text
We do not know of any other work that decomposes the pairwise distance between two models as related to the product of a query kernel and a response kernel.

Evaluating the effectiveness of a method in sparse and unpaired settings requires knowing the score from a full evaluation, hence the "artificial" sparsity. We note in our response to Reviewer VZXd that in arena-like settings (which is the dominant evaluation paradigm in production) that evaluations are natively unpaired and sparse.
```

### Review 2: Reviewer_VZXd
- note id: xONfQDy3sH
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Review
- signature: ICLR.cc/2027/Conference/Submission26519/Reviewer_VZXd
- created (tcdate): 2026-10-20 16:23:14 UTC
- modified (mdate): 2026-11-06 12:25:42 UTC
- replyto: 7ChRYhe6kG

**paper_summary**:

```text
PKPS is a follow-up study to DKPS(previous paper) extending the method to make it applicable to LLMs that have responded to different queries (in the unpaired setting). In fact, the only change from DKPS can be said to be simply replacing the identity query kernel with a different kernel (However, I don't view this simplicity negatively).
```

**presentation**:

```text
1
```

**informativeness**:

```text
2
```

**soundness**:

```text
2
```

**critical_strengths**:

```text
1. The authors addressed limitations of prior work with a simple method. 

2. The authors ran many experiments on different datasets and showed that their method works well.
```

**critical_weaknesses**:

```text
1. Figs in the paper seem to be AI-generated and of low quality (ex. Fig.6(d): misaligned, Fig. 7(c): the text after "m=" on the x-axis is cut off). Also, the proofs seem to be AI-generated, so they need to be improved (ex. the inequality in Line 971 extends beyond the page margin & too many artificial assumptions are made for the proofs)

2. The theory and experiments in this paper are not clear to me, and the paper is generally difficult to read. I will ask questions about this in the Questions section.
```

**questions_for_authors**:

```text
1. Could you explain how reasonable the assumptions in the theorems? For example, the paper reports that 26 of 33 tasks in EEE have $\rho > 0.99$, which seems quite different from Assumption 7 (Pairing deficiency). This is important because assumption7 is the core of Theorem 2. I'm concerned that assumption7 may put DKPS at an artificial disadvantage in Theorem 2, making the comparison between PKPS and DKPS in Thm 2 less convincing.

2. How much of the reported 8x/4x improvement actually comes from PKPS? Since DKPS also outperforms the sample baseline, could the authors compare PKPS with simpler baselines (ex. a task mean or bias-only predictor ... ) ?

3. The main idea is to compare similar queries rather than identical ones, but the experiments suggest that broader kernels work better. So, what happens when $\sigma \rightarrow \infty$ in the kernel $k_{\sigma}$ or when a constant kernel is used? Is query similarity really the cause of the improvement?
```

**flag_for_ethics_review**:

```text
No
```

**rating**:

```text
2
```

**confidence**:

```text
2
```

### Author response (answers xONfQDy3sH, depth 2)
- note id: flQGeCyN5F
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-11 19:59:08 UTC
- modified (mdate): 2026-11-11 19:59:08 UTC
- replyto: xONfQDy3sH

**title**:

```text
Initial response (1/2)
```

**comment**:

```text
Thank you for taking the time to review our submission. We think your summary provides a fair representation of our contributions and appreciate your recognition of both the simplicity and effectiveness of our method. We address your weaknesses and questions inline below:

> Figs in the paper seem to be AI-generated and low quality (ex. Fig.6(d): misaligned, Fig. 7(c): the text after "m=" on the x-axis is cut off).

Thank you for pointing these out. We used the same plotting code / styles for both the main text and the appendix and did not adjust things based on the appearance of figures in the appendix. We will fix this: we will break the title into two lines so that it is better aligned to fix Figure 6(d) and move the “m=2” information to the panel’s title to fix 7(c).

We will also fix the overflowing inequality at line 971 and number the equations in Appendix D.

> The theory and experiments in this paper are not clear to me.

Beyond answering the questions below, we also wanted to take the time to describe the paper in a few sentences to (hopefully) improve its legibility.

We are the first to describe DKPS-like methods as the product of a query kernel and a response kernel. This allows us to generalize the method and, in turn, apply the method to benchmark prediction in more realistic evaluation and observation settings (i.e., the sparse / unpaired regime).

There are two historically different problems that can be described as benchmark prediction: query-efficient evaluation and (model, task) score completion. Our experiments are designed to investigate when / if generalized DKPS outperforms baselines across the two tasks. The results point to it being an effective method for both tasks (especially at very small query budgets) on both synthetic and real data.

Theoretically, our goal was to show the PKPS is better than DKPS for benchmark prediction. We first show that the representations behave well (Theorem 1). Then, we show that PKPS is no worse than DKPS (Theorem 2). Finally, we show that there exists a setting (i.e. under Assumption 7) where PKPS is strictly better than DKPS. Assumption 7 is only required for showing strict improvement. 

We hope this helps clear things up!

> Could you explain how reasonable the assumptions are that are used in the theorems?

Yes. We use the label of each assumption provided in part D of the appendix.

>> Observation model

Benchmark scores are often the average of per-query scores.

The per-query scores are often bounded (i.e., correct / incorrect, BLEU, etc.).

Query observations being a uniform subsample from a task is not typically true but is a pretty standard assumption for theoretical analysis.

>> Boundedness (of kernels and embeddings)

This is true in practice.

>> Population overlap

This is true in practice for any strictly positive kernel (e.g., the RBF kernel we use) with a non-zero bandwidth.

>> Spectral identifiability

Typically true in practice (e.g., there is a clear gap after the 8th eigenvalue on both HELM and EEE).

>> Score regularity

This requires the embedding function to encode the score very well. This is only approximately true in practice. 

It is required to relate the learned model embeddings to the score function and is equivalent to Assumption 1 in the paper that proves query efficiency of DKPS relative to the sample score (Helm et al., 2026).

>> Model support / denseness

Likely not true in practice but is a standard assumption when analyzing the limiting behavior of inference with nearest neighbors (Cover & Hart, 1967; Biau & Devroye, 2015).

>> Pairing deficiency

In highly curated benchmarking settings (as HELM and EEE are), this is not true. We artificially create a pairing deficiency by subsampling responses. We note that using highly curated benchmarking settings such as HELM / EEE as examples is necessary for knowing ground truth scores and, thus, for evaluating the method.

In more modern evaluation settings such as arena and in-the-wild style evaluations (Chiang et al., 2024; Chi et al., 2025), paired responses are much less common. For example, in the 7 arena-style benchmarks in the EEE datastore, two models share only 45% of their queries on average.

As mentioned above, we only require the pairing deficiency assumption to prove strict improvement over DKPS. You can use PKPS instead of DKPS in all settings and expect an improvement when / if pairing is deficient.

We plan to add these comments on how realistic each assumption is to the appendix.
```

### Author response (answers flQGeCyN5F, depth 3)
- note id: EZwq1LrjP3
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-11 19:59:32 UTC
- modified (mdate): 2026-11-11 19:59:32 UTC
- replyto: flQGeCyN5F

**title**:

```text
Initial response (2/2)
```

**comment**:

```text
> How much of the reported improvement actually comes from PKPS?

Great question. Firstly, we've added a new baseline (the task mean == the average score of the other models on the task) and updated the IRT baseline based on Reviewer e8LY's suggestion. We have also included an ensemble of each baseline and both PKPS and DKPS to better understand how much PKPS "adds":

MAE over 16 seeds ("+ PKPS" / "+ DKPS" is the baseline above ensembled with PKPS / DKPS):

||HELM m=1|2|8|32|EEE m=1|2|8|32|
|-|-|-|-|-|-|-|-|-|
|DKPS|.171|.168|.111|.086|.116|.112|.077|.053|
|PKPS|.136|.125|.108|.086|.070|.065|.060|.053|
|Task mean|.155|.155|.155|.155|.117|.117|.117|.117|
|Sample|.292|.195|.092|.034|.224|.164|.081|.037|
|+ DKPS|.149|.130|.074|.033|.102|.091|.058|.032|
|+ PKPS|.126|.109|.073|.033|.068|.061|.050|.032|
|Task mean + sample|.138|.124|.081|.034|.102|.093|.066|.035|
|+ DKPS|.138|.124|.077|.033|.101|.092|.062|.033|
|+ PKPS|.130|.114|.076|.033|.070|.065|.053|.033|
|IRT|.137|.118|.071|.028|.113|.102|.069|.032|
|+ DKPS|.137|.118|.069|.028|.111|.102|.064|.031|
|+ PKPS|.127|.109|.068|.028|.070|.065|.054|.031|

Adding PKPS never hurts a baseline and helps most on EEE at small budgets. Adding DKPS helps much less at small budgets, since few queries are shared. At m=32, where many queries are shared, the two perform very similarly.

We plan to include the majority of this updated table in main text and the full table in the appendix.

> What happens when a constant kernel is used?

We included a bandwidth sensitivity analysis in appendix C (Figure 7c). We have extended this analysis to include larger bandwidths (including the constant kernel which, as you pointed out, corresponds to $ \sigma = \infty $).

We have summarized the results in a table provided in our response to Reviewer e8LY for two response kernels: i) the linear response kernel used throughout the paper and ii) a "correctness" kernel. In short, with the linear response kernel, the constant kernel is about as good as the best bandwidth at small budgets, while exact matching (DKPS) is best at m=32. With the correctness kernel, intermediate bandwidths beat both the constant kernel and DKPS at every budget. So how much query similarity helps depends on the response kernel.

We will add this analysis to part C of the appendix and comment on it in the main text.

---

Thank you again for taking the time to review our paper! Please let us know if we were able to address your questions / concerns.

References

Biau, Gérard, and Luc Devroye. Lectures on the Nearest Neighbor Method. Springer, 2015.

Chi, Wayne, et al. "Copilot Arena: A Platform for Code LLM Evaluation in the Wild." Proceedings of the 42nd International Conference on Machine Learning, PMLR, vol. 267, 2025, pp. 10354–10382.

Chiang, Wei-Lin, et al. "Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference." Proceedings of the 41st International Conference on Machine Learning, PMLR, vol. 235, 2024.

Cover, Thomas M., and Peter E. Hart. "Nearest Neighbor Pattern Classification." IEEE Transactions on Information Theory, vol. 13, no. 1, 1967, pp. 21–27.

Helm, Hayden, et al. "Query-Efficient Model Evaluation Using Cached Responses." Proceedings of the 43rd International Conference on Machine Learning, PMLR, 2026.
```

### Reviewer reply (answers EZwq1LrjP3, depth 4)
- note id: OYVPBOIBuW
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Reviewer_VZXd
- created (tcdate): 2026-11-18 09:23:41 UTC
- modified (mdate): 2026-11-18 09:23:41 UTC
- replyto: EZwq1LrjP3

**comment**:

```text
Thank you for the responses and experiments. However, I still have two concerns.

1. With linear response kernel in main experiments, the constant query kernel performs almost as PKPS so the benefit of query similarity unclear.
2. Adding PKPS to (strong LRMC + Sample baseline) provides only a small improvement on HELM.

For these reasons, I’ll maintain original rating.
```

### Author response (answers OYVPBOIBuW, depth 5)
- note id: aSnt2mSphk
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-19 06:37:41 UTC
- modified (mdate): 2026-11-19 06:37:41 UTC
- replyto: OYVPBOIBuW

**comment**:

```text
Thank you for your response.

> With linear response kernel in main experiments, the constant query kernel performs almost as PKPS so the benefit of query similarity unclear.

The constant query kernel is PKPS (with bandwidth $ \sigma = \infty $). Per the tables we provided, the constant query kernel loses to a non-constant query kernel for large $ m $, even for the linear response kernel. Choosing the bandwidth via cross-validation never loses to the constant query kernel and is able to adapt to a non-constant kernel when appropriate. We think this is quite clear.

Per the tables we provided, it is also very clear that a non-constant query kernel is beneficial for the correctness kernel for all $ m $. We think the second part of the result is as important as the first as it shows the effect is dependent on the choice of response kernel.  

> Adding PKPS to (strong LRMC + Sample baseline) provides only a small improvement on HELM.

It provides a small improvement on HELM and a non-trivial improvement (upwards of 10%) on EEE.
Per the table we provided:

||HELM m=1|2|8|32|EEE m=1|2|8|32|
|-|-|-|-|-|-|-|-|-|
|LRMC + sample|.107|.092|.065|.033|.073|.062|.049|.031|
|+ PKPS|.106|.092|.064|.033|.065|.057|.046|.030|
|Relative reduction|1.2%|-0.1%|1.6%|0.0%|10.6%|8.5%|7.1%|2.2%|
|Tasks improved|11/18|11/18|13/18|10/18|15/16|15/16|14/16|11/16|
|Wilcoxon $p$|.28|.73|.02|.44|<.001|<.001|<.001|.08|
```

### Review 3: Reviewer_e8LY
- note id: TGHNNWxBjW
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Review
- signature: ICLR.cc/2027/Conference/Submission26519/Reviewer_e8LY
- created (tcdate): 2026-10-22 03:24:29 UTC
- modified (mdate): 2026-11-19 07:46:30 UTC
- replyto: 7ChRYhe6kG

**paper_summary**:

```text
This paper proposes the Product Kernel Perspective Space (PKPS) for predicting benchmark scores from sparse and unpaired cached responses, which combines query and response kernels to construct model representations, then predicts scores through nearest-neighbor regression.
```

**presentation**:

```text
2
```

**informativeness**:

```text
2
```

**soundness**:

```text
2
```

**critical_strengths**:

```text
1.The paper studies a practical and interesting problem. PKPS that can reuse Cached evaluations could reduce the cost of evaluation. 

2. Supporting both low-query evaluation and missing-score completion within one framework is useful.
```

**critical_weaknesses**:

```text
1.The query-efficiency baselines do not adequately control for score-based prediction. IRT is fitted only on the largest fully observed model–item block, discarding sparse observations that a regularized Rasch fit could use when the observation graph is sufficiently connected. Besides,tThe contribution of query-dependent weighting is not isolated. With the linear response kernel used in the experiments, $k_Q\equiv1$ reduces Eq. (1) to inner products between mean response embeddings, and the resulting distances are simply Euclidean distances between those means.

2.The evaluation provides limited evidence for the structured missingness that motivates practical deployment. Both suites are constructed by randomly masking dense evaluation subsets, and many evaluated tasks are subdivisions of the same benchmark. A missing task may therefore retain closely related observations from sibling tasks. Although Section 5 acknowledges nonuniform missingness, the results do not separately establish performance when an entire benchmark is missing or query coverage systematically differs across models
```

**questions_for_authors**:

```text
1.How does PKPS compare with a cross-fitted score-only predictor, such as LRMC blended with the sample score, under matched supervision and validation? What justifies restricting IRT to a fully observed block instead of fitting all observed entries where identifiable?

2.How does PKPS compare with $k_Q\equiv1$ when response embeddings, representation dimension, family splits, regression, and validation are held fixed?

3.Do the completion gains remain when all subtasks of a parent benchmark are held out together for a target model, at a comparable observation budget? How sensitive are the results to model-dependent topic or difficulty coverage?

4.Please specify the reference labels, validation loss, and confidence threshold used for bandwidth selection, and clarify how the $K=8$ tuning predictor relates to the final distance-weighted $K=5$ predictor.
```

**flag_for_ethics_review**:

```text
No
```

**rating**:

```text
3
```

**confidence**:

```text
2
```

### Author response (answers TGHNNWxBjW, depth 2)
- note id: MQXm9aHPoq
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-11 19:55:58 UTC
- modified (mdate): 2026-11-11 19:55:58 UTC
- replyto: TGHNNWxBjW

**title**:

```text
Initial response (1/2)
```

**comment**:

```text
Thank you for taking the time to review our paper. We think the summary you provided of it is fair. We appreciate you noting the practical value of reusing cached evaluations and the value of unifying low query evaluation and score completion under the same framework. We address your noted weaknesses and questions inline below:

> W1.1. IRT is fitted only on ...

We have updated the IRT baseline used in our analysis to regularized Rasch. The new results are described in our response to Reviewer VZXd. It is much improved: on EEE it is still outperformed by PKPS for m $ \le $ 8, while on HELM the two are similar at the smallest budgets and IRT is better at larger ones.

Ensembling IRT with PKPS is typically better than either alone and is never worse than IRT. In general, we find that PKPS is complementary to methods that just use score information (see our response to Reviewer VZXd). We will replace the IRT baseline with your suggested regularized Rasch throughout the paper.

> W1.2. The contribution of query-dependent weighting is not isolated.

We included a small bandwidth sensitivity analysis in Figure 7c. We have extended this analysis to include more bandwidths (including the constant kernel) and more query budgets. 

We consider two response kernels: i) the linear response kernel used throughout the paper and ii) a "correctness" response kernel that represents each response only by its score. That is, we replace $ x_{ij} $ with $ c_{ij} = (s_{ij}, 1 - s_{ij}) / \| (s_{ij}, 1 - s_{ij}) \| $, where $ s_{ij} = s^{(t)}(f_i, \{q_j\}) \in [0, 1] $ is the score of model $ i $'s response to query $ q_j $, and use the same linear kernel $ k_R(c_{ij}, c_{i'l}) = \langle c_{ij}, c_{i'l} \rangle $. For binary scores this is $ \mathbb{1}[s_{ij} = s_{i'l}] $. We note that this is the same information that the other baselines have access to.

Reported results are average MAE over 16 seeds (bandwidth in multiples of the median query distance):

Linear response kernel

||0.01|0.3|1|3|constant|CV|
|-|-|-|-|-|-|-|
|HELM m=2|.168|.160|.134|.123|.125|.125|
|HELM m=8|.111|.125|.115|.109|.110|.108|
|HELM m=32|.086|.104|.105|.104|.104|.086|
|EEE m=2|.112|.081|.066|.064|.064|.065|
|EEE m=8|.077|.062|.059|.060|.060|.060|
|EEE m=32|.053|.055|.059|.059|.058|.053|

Correctness response kernel

||0.01|0.3|1|3|constant|CV|
|-|-|-|-|-|-|-|
|HELM m=2|.121|.110|.087|.086|.097|.087|
|HELM m=8|.085|.078|.068|.071|.084|.068|
|HELM m=32|.066|.062|.059|.065|.080|.059|
|EEE m=2|.098|.082|.059|.058|.060|.059|
|EEE m=8|.074|.057|.044|.044|.045|.044|
|EEE m=32|.054|.044|.038|.039|.040|.038|

With the linear response kernel, the constant kernel is about as good as the best bandwidth at small budgets, while exact matching (DKPS) is best at m=32. With the correctness kernel, intermediate bandwidths beat both the constant kernel and DKPS at every budget. So how much query similarity helps depends on the response kernel. In both cases, cross-validation picks a bandwidth close to the best one.

We will add this analysis to part C of the appendix and comment on it in the main text.
```

### Author response (answers MQXm9aHPoq, depth 3)
- note id: CjPsv3uqNp
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-11 19:56:20 UTC
- modified (mdate): 2026-11-11 19:56:20 UTC
- replyto: MQXm9aHPoq

**title**:

```text
Initial response (2/2)
```

**comment**:

```text
> W2. Structured missingness

We ran both settings you suggested: (i) all subtasks of a parent benchmark held out together for a target model (completion) and (ii) query coverage that depends on the model's topic or difficulty (query efficiency).

>> Whole benchmark held out

Each target model is missing every subtask of one parent benchmark (e.g., all MATH subjects), and we evaluate only on that block. The remaining cells are observed so that overall coverage matches the uniform setting. Reported results are average MAE over 16 seeds ("+ PKPS" is the row above ensembled with PKPS):

||20% coverage|35%|50%|
|-|-|-|-|
|HELM uniform: LRMC|.136|.116|.106|
|+ PKPS|.124|.109|.099|
|HELM benchmark held out: LRMC|.141|.133|.133|
|+ PKPS|.133|.125|.124|
|EEE uniform: LRMC|.101|.098|.090|
|+ PKPS|.085|.077|.068|
|EEE benchmark held out: LRMC|.101|.105|.095|
|+ PKPS|.090|.077|.073|

Both methods are worse when the whole benchmark is missing, but adding PKPS helps by about as much as in the uniform setting.

>> Model-dependent topic or difficulty coverage 

Each model draws its queries with probability biased toward hard or easy items (or toward one topic), with the direction of the bias differing across models. Reported results are average MAE over 16 seeds with difficulty-biased coverage ("+ PKPS" is the row above ensembled with PKPS):

||HELM m=2|8|EEE m=2|8|
|-|-|-|-|-|
|Sample|.273|.195|.241|.145|
|+ PKPS|.126|.107|.090|.063|
|IRT|.133|.090|.142|.094|
|+ PKPS|.121|.082|.091|.065|
|LRMC + sample|.184|.157|.128|.095|
|+ PKPS|.131|.111|.091|.066|

Biased query coverage hurts methods that estimate a model's level from its own observed scores. For example, LRMC + sample goes from .092 to .184 on HELM at m=2. PKPS is affected less (from .125 to .132 on HELM and from .065 to .090 on EEE at m=2) because it compares a model's responses with other models' responses to similar queries. IRT is also affected less on HELM because it models item difficulty. Adding PKPS to LRMC + sample recovers much of the loss (.184 to .131 on HELM and .128 to .091 on EEE at m=2).

Topic-biased coverage is milder: Sample + PKPS changes by at most .008 and LRMC + sample + PKPS by at most .003. We do not include the full table here for space considerations.

We will add all results to the appendix.

> LRMC blended with the sample score and other cross-fitted score-only predictors

We have added LRMC (following BenchPress; Zeng & Papailiopoulos, 2026), alone and blended with the sample score, under the same supervision and leave-one-family-out validation as PKPS. Other score-only baselines (task mean and IRT) are in our response to Reviewer VZXd. Reported results are average MAE over 16 seeds ("+ PKPS" is the row above ensembled with PKPS):

||HELM m=1|2|8|32|EEE m=1|2|8|32|
|-|-|-|-|-|-|-|-|-|
|PKPS|.136|.125|.108|.086|.070|.065|.060|.053|
|Sample|.292|.195|.092|.034|.224|.164|.081|.037|
|+ PKPS|.126|.109|.073|.033|.068|.061|.050|.032|
|LRMC|.115|.102|.088|.079|.076|.066|.059|.046|
|LRMC + sample|.107|.092|.065|.033|.073|.062|.049|.031|
|+ PKPS|.106|.092|.064|.033|.065|.057|.046|.030|

LRMC + sample is a strong baseline, especially on HELM. Adding PKPS to it never hurts and helps most on EEE at small budgets.

> Reference labels, validation loss, and confidence threshold used for bandwidth selection.

For bandwidth selection, the labels are the observed sample scores of every model (including the reference models) and the validation loss is the MAE of leave-one-model-out KNN regression.

We introduced the confidence threshold as a theoretical device and did not originally include it in our implementation. Re-running the analysis with a 95% confidence threshold yields observed MAEs with an average absolute difference of 0.001 (at most 0.004) across both suites and $ m \in \{1, 2, 8, 32\} $.

> Clarification of $ K $.

In our original analysis the bandwidth-selection predictor used $ K = 8 $. The final regressor used $ K = 5 $. This was not intentional. Re-running the analysis with $ K = 5 $ for both yields observed MAEs with an average absolute difference of 0.001 (at most 0.003) from the reported results.

---

Thank you again for taking the time to review our paper! Please let us know if we were able to address your questions / concerns.

References

Zeng, Yuchen, and Dimitris Papailiopoulos. "You Don't Need to Run Every Eval." arXiv, 2026, arXiv:2606.24020.
```

### Reviewer reply (answers CjPsv3uqNp, depth 4)
- note id: xy3Tw7KLVw
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Reviewer_e8LY
- created (tcdate): 2026-11-19 07:46:16 UTC
- modified (mdate): 2026-11-19 07:46:16 UTC
- replyto: CjPsv3uqNp

**comment**:

```text
Thank you for the detailed response and additional experiments. The stronger score-only baselines, structured-missingness experiments, and implementation clarifications address my original concerns. Although the benefit of query-dependent weighting remains limited with the original linear response kernel, the correctness-kernel results and gains under structured missingness strengthen the empirical support. I will therefore raise my rating from 2 to 3.
```

### Author response (answers TGHNNWxBjW, depth 2)
- note id: GPK8JMQ3hZ
- invitation: ICLR.cc/2027/Conference/Submission26519/-/Official_Comment
- signature: ICLR.cc/2027/Conference/Submission26519/Authors
- created (tcdate): 2026-11-18 20:02:52 UTC
- modified (mdate): 2026-11-18 20:02:52 UTC
- replyto: TGHNNWxBjW

**title**:

```text
summary of initial response
```

**comment**:

```text
Unfortunately we did not get the chance to engage with you during the reviewer-author discussion period. We briefly summarize our response to each of your points above:

> W1.1. IRT is fitted only on the dense block.

We replaced the IRT baseline with regularized Rasch fitted on all sparse observations. It is much improved: PKPS still outperforms it on EEE for $m \le 8$, the two are similar on HELM at the smallest budgets, and IRT is better on HELM at larger ones. IRT + PKPS is never worse than IRT.

> W1.2. The contribution of query-dependent weighting is not isolated.

We extended the bandwidth sweep to include the constant kernel and more budgets for two response kernels. With the linear response kernel, the constant kernel is about as good as the best bandwidth at small budgets while DKPS is best at $m = 32$. With the correctness response kernel, intermediate bandwidths beat both at every budget. Cross-validation picks a bandwidth close to the best in all cases.

> W2. Structured missingness.

With a whole parent benchmark held out, all methods degrade but adding PKPS to LRMC helps about as much as under uniform missingness (e.g., EEE at 50% coverage: 0.095 to 0.073). With difficulty-biased query coverage, LRMC + sample degrades sharply (HELM, $m = 2$: 0.092 to 0.184) while PKPS is affected much less, and adding PKPS recovers most of the loss (0.184 to 0.131). Topic-biased coverage has a much smaller effect.

> LRMC blended with the sample score and other cross-fitted score-only predictors.

We added LRMC, alone and blended with the sample score, under the same supervision and leave-one-family-out validation as PKPS. LRMC + sample is a strong baseline, especially on HELM. Adding PKPS never hurts and helps most on EEE at small budgets (e.g., $m = 1$: 0.073 to 0.065).

> Reference labels, validation loss, and confidence threshold used for bandwidth selection.

Bandwidth selection uses the observed sample scores of every model and the MAE of leave-one-model-out KNN regression. Adding the 95% confidence threshold changes MAE by 0.001 on average (at most 0.004).

> Clarification of $K$.

Bandwidth selection used $K = 8$ and the regressor $K = 5$. This was not intentional. Using $K = 5$ for both changes MAE by 0.001 on average (at most 0.003).

---
We believe we have adequately addressed your initial weaknesses and questions & we hope these summaries make it easier for you to assess our original response.
```

## Other notes in the forum (not under a review)

## Meta-review and decision

None present in the forum at retrieval time.
