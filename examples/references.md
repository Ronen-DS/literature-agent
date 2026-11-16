# The references: all 51, and the citation check

The reference list the pipeline produced for the worked example, in Vancouver
order of first appearance. Every entry was built by `number_refs.py` from the
retrieved PubMed records — the model never typed a reference.

**Citation check: PASS** — 51 references, every one with a PMID present in
`2026-11-06_immunopep-neoantigen-combined_screened.csv` with decision `include`.

```
Citation check: results/2026-11-06_neoantigen-presentation-modulation_references.json
Screened CSV: results/2026-11-06_immunopep-neoantigen-combined_screened.csv (355 papers)
References checked: 51

PASS - every reference has a PMID that is in the CSV with decision 'include'.
```

The check is enforced by a `PostToolUse` hook, so it runs whenever a reference
list is written, whether or not anyone remembers to ask for it. The same check
run against a deliberately corrupted copy — one fabricated PMID added as
reference 52 — blocked the write and reported:

```
FAIL - 1 problem(s):
  - Reference 52: PMID 99999999 is NOT in the screened CSV.
    It may be an invented paper - remove it.
```

## References

1. Yang K, et al. Antigen presentation in cancer — mechanisms and clinical implications for immunotherapy. *Nature Reviews Clinical Oncology*. 2023. PMID: [37328642](https://pubmed.ncbi.nlm.nih.gov/37328642/)
2. Kallingal A, et al. Cancer immune escape: the role of antigen presentation machinery. *Journal of Cancer Research and Clinical Oncology*. 2023. PMID: [37031434](https://pubmed.ncbi.nlm.nih.gov/37031434/)
3. Grizzi F, et al. Cancer Immune Responsiveness and MHC Class I Antigen Presentation: Mechanisms of Immune Escape and Immunotherapy Resistance in Gastrointestinal Cancers. *Cells*. 2026. PMID: [42738808](https://pubmed.ncbi.nlm.nih.gov/42738808/)
4. Zaghla BKQ, et al. Systematic evaluation of neoepitope predictions challenges clinically observed T-cell responses and their impact on immune evasion. *Journal for ImmunoTherapy of Cancer*. 2026. PMID: [41506790](https://pubmed.ncbi.nlm.nih.gov/41506790/)
5. Alghoul WII, et al. The Antigen-Presentation Bottleneck in Pediatric Solid Tumors: Developmental Antigens, MHC-I Suppression, and Therapeutic Restoration of Tumor Immune Recognition. *Biomolecules*. 2026. PMID: [42939702](https://pubmed.ncbi.nlm.nih.gov/42939702/)
6. Haratani K, et al. Cancers modulate processing and presentation of p53 neoantigens to evade T cell detection. *Immunity*. 2026. PMID: [42753739](https://pubmed.ncbi.nlm.nih.gov/42753739/)
7. Demel UM, et al. Aberrant SUMOylation Restricts the Targetable Cancer Immunopeptidome. *Advanced Science*. 2026. PMID: [41566667](https://pubmed.ncbi.nlm.nih.gov/41566667/)
8. Canel M, et al. FAK suppresses antigen processing and presentation to promote immune evasion in pancreatic cancer. *Gut*. 2023. PMID: [36977556](https://pubmed.ncbi.nlm.nih.gov/36977556/)
9. Miyauchi S, et al. Human papillomavirus E5 suppresses immunity via inhibition of the immunoproteasome and STING pathway. *Cell Reports*. 2023. PMID: [37171962](https://pubmed.ncbi.nlm.nih.gov/37171962/)
10. Smith MG, et al. Hypoxic stress granules trigger immunogenic dormancy in lung cancer. *bioRxiv*. 2026. PMID: [41756967](https://pubmed.ncbi.nlm.nih.gov/41756967/)
11. Estephan H, et al. Immunopeptidomics Workflow for Isolation and LC-MS/MS Analysis of MHC Class I-Bound Peptides Under Hypoxic Conditions. *Bio-protocol*. 2025. PMID: [41306581](https://pubmed.ncbi.nlm.nih.gov/41306581/)
12. Zapata L, et al. Immune selection determines tumor antigenicity and influences response to checkpoint inhibitors. *Nature Genetics*. 2023. PMID: [36894710](https://pubmed.ncbi.nlm.nih.gov/36894710/)
13. Vendramin R, et al. Nonsense-mediated mRNA decay inhibition reshapes the cancer immunopeptidome. *Immunity*. 2026. PMID: [41956098](https://pubmed.ncbi.nlm.nih.gov/41956098/)
14. Torres-Fernández LA, et al. A targetable dependency on nonsense-mediated decay for cellular homeostasis and immune control in small cell lung cancer. *Molecular Cancer*. 2026. PMID: [42711693](https://pubmed.ncbi.nlm.nih.gov/42711693/)
15. Goyal A, et al. DNMT and HDAC inhibition induces immunogenic neoantigens from human endogenous retroviral element-derived transcripts. *Nature Communications*. 2023. PMID: [37872136](https://pubmed.ncbi.nlm.nih.gov/37872136/)
16. Burbage M, et al. Epigenetically controlled tumor antigens derived from splice junctions between exons and transposable elements. *Science Immunology*. 2023. PMID: [36735776](https://pubmed.ncbi.nlm.nih.gov/36735776/)
17. Fisher RJ, et al. CoREST complex inhibition alters RNA splicing to promote neoantigen expression and enhance tumor immunity. *JCI Insight*. 2026. PMID: [41364533](https://pubmed.ncbi.nlm.nih.gov/41364533/)
18. Recho A, et al. Combination epigenetic-targeted therapy increases the immunogenicity of poorly immunogenic sarcomas. *bioRxiv*. 2026. PMID: [42368028](https://pubmed.ncbi.nlm.nih.gov/42368028/)
19. Melief J, et al. Pleiotropic effects of BET inhibition broadly boost tumor immunogenicity to CD8+ T cells. *OncoImmunology*. 2026. PMID: [42057381](https://pubmed.ncbi.nlm.nih.gov/42057381/)
20. Jiang Q, et al. HIF regulates multiple translated endogenous retroviruses: Implications for cancer immunotherapy. *Cell*. 2025. PMID: [40023154](https://pubmed.ncbi.nlm.nih.gov/40023154/)
21. Wang J, et al. Targeting non-canonical antigens unlocks functional T-cell responses in renal cell carcinoma. *Journal for ImmunoTherapy of Cancer*. 2026. PMID: [42342407](https://pubmed.ncbi.nlm.nih.gov/42342407/)
22. Kehl N, et al. Latent effector T cells mediate immunotherapy responses in the bone marrow microenvironment. *Cancer Cell*. 2026. PMID: [42575099](https://pubmed.ncbi.nlm.nih.gov/42575099/)
23. Gragera P, et al. Moonlighting ERAP Aminopeptidases in Cancer: Beyond Antigen Processing. *Cells*. 2026. PMID: [42738902](https://pubmed.ncbi.nlm.nih.gov/42738902/)
24. Tinworth CP, et al. Discovery of an Orally Available Potent ER Aminopeptidase 1 (ERAP1) Inhibitor That Enhances Antitumor Responses and Limits Inflammatory Autoimmunity In Vivo. *Journal of Medicinal Chemistry*. 2026. PMID: [42324823](https://pubmed.ncbi.nlm.nih.gov/42324823/)
25. Yari H, et al. Inhibition of cellular NEDDylation partially alters the MHC class I immunopeptidome. *Journal of Immunology*. 2026. PMID: [42858555](https://pubmed.ncbi.nlm.nih.gov/42858555/)
26. Aranha R, et al. Cytokine-Mediated Plasticity in the Molecular Requirements for Peptide-Loading Complex Formation and Antigen Presentation. *Cells*. 2026. PMID: [42929886](https://pubmed.ncbi.nlm.nih.gov/42929886/)
27. Monti M, et al. Integrating interferon gamma receptor pathways, antigenicity, and immune contexture as predictors of immunotherapeutic strategies for mucosal melanomas. *Journal for ImmunoTherapy of Cancer*. 2026. PMID: [41791790](https://pubmed.ncbi.nlm.nih.gov/41791790/)
28. Hwang D, et al. HLA-Shuttle: A system for enhancing antigen presentation in immunologically cold tumors. *Science Advances*. 2026. PMID: [41477871](https://pubmed.ncbi.nlm.nih.gov/41477871/)
29. Yuzhalin AE, et al. Re-expression of MHC-I to treat CNS cancers. *Oncotarget*. 2026. PMID: [42708880](https://pubmed.ncbi.nlm.nih.gov/42708880/)
30. Beck JD, et al. Long-lasting mRNA-encoded interleukin-2 restores CD8+ T cell neoantigen immunity in MHC class I-deficient cancers. *Cancer Cell*. 2024. PMID: [38490213](https://pubmed.ncbi.nlm.nih.gov/38490213/)
31. Barajas Molina A, et al. Stable β2-Microglobulin-HLA Class I Association Reshapes the Antigenic Landscape and TCR Recognition of Cancer-Associated Epitopes. *European Journal of Immunology*. 2026. PMID: [42204932](https://pubmed.ncbi.nlm.nih.gov/42204932/)
32. Maso L, et al. Engineered antibodies that stabilize drug-modified KRAS G12C neoantigens enable selective and potent cross-HLA immunotherapy. *Nature Communications*. 2025. PMID: [41408054](https://pubmed.ncbi.nlm.nih.gov/41408054/)
33. Sagie S, et al. Lymphodepleting chemotherapy potentiates neoantigen-directed T cell therapy by enhancing antigen presentation. *Cell Reports Medicine*. 2025. PMID: [41406943](https://pubmed.ncbi.nlm.nih.gov/41406943/)
34. Matsumi Y, et al. Antigen Remodeling in Colorectal Cancer: How Radiotherapy and Chemotherapy Enhance Immunotherapy Responsiveness. *Cancers*. 2026. PMID: [41749968](https://pubmed.ncbi.nlm.nih.gov/41749968/)
35. Minati R, et al. CDK4/6 inhibition reprograms the breast cancer immunopeptidome via Rb-dependent chromatin and transcriptomic remodeling. *Cell Reports*. 2025. PMID: [41391145](https://pubmed.ncbi.nlm.nih.gov/41391145/)
36. Venafra V, et al. Kinase inhibition rewires the HLA-I immunopeptidome in chronic myeloid leukemia. *iScience*. 2026. PMID: [42181250](https://pubmed.ncbi.nlm.nih.gov/42181250/)
37. Khairkhah N, et al. Identification of molecularly targeted therapy-induced immunopeptidome in diffuse midline glioma (DMG). *Neoplasia*. 2026. PMID: [41643293](https://pubmed.ncbi.nlm.nih.gov/41643293/)
38. Shamekhi T, et al. H3K27M Mutation Modulates the Antigenic Landscape in Diffuse Midline Glioma. *Cancers*. 2026. PMID: [42882837](https://pubmed.ncbi.nlm.nih.gov/42882837/)
39. Cui Y, et al. Quantitative Cell Type-Specific Immunopeptidome Analysis of Macrophage and Tumor Coevolution Reveals Therapeutic MHC-I Peptides in Glioblastoma. *Cancer Research*. 2025. PMID: [40966317](https://pubmed.ncbi.nlm.nih.gov/40966317/)
40. Marine JC, et al. Mapping intratumor heterogeneity across layers for advancing immunotherapy. *Cell*. 2026. PMID: [41997129](https://pubmed.ncbi.nlm.nih.gov/41997129/)
41. Kacen A, et al. Post-translational modifications reshape the antigenic landscape of the MHC I immunopeptidome in tumors. *Nature Biotechnology*. 2023. PMID: [36203013](https://pubmed.ncbi.nlm.nih.gov/36203013/)
42. Kelly JJ, et al. Non-Enzymatic Structural Modifications Reshape Peptide Presentation and Antigen Recognition. *bioRxiv*. 2025. PMID: [41279913](https://pubmed.ncbi.nlm.nih.gov/41279913/)
43. Hardy MP, et al. Optimized Epitope-Flanking Sequences Enhance Antigen Presentation and T-Cell Responses Following mRNA Vaccination. *Cells*. 2026. PMID: [42882451](https://pubmed.ncbi.nlm.nih.gov/42882451/)
44. Shen KY, et al. Oncolytic adenovirus delivery of neoantigens sensitizes low-mutation tumors to anti-PD-1 therapy and prevents metastasis. *Signal Transduction and Targeted Therapy*. 2025. PMID: [41429778](https://pubmed.ncbi.nlm.nih.gov/41429778/)
45. Kiel K, et al. Oncolytic Virus-Engineered Extracellular Vesicles Rewire Glioblastoma Immunity. *Journal of Extracellular Vesicles*. 2026. PMID: [42908192](https://pubmed.ncbi.nlm.nih.gov/42908192/)
46. Zheng X, et al. XIAP inhibition augments personalized neoantigen vaccine-driven antitumor immunity in orthotopic hepatocellular carcinoma. *Journal for ImmunoTherapy of Cancer*. 2026. PMID: [42855228](https://pubmed.ncbi.nlm.nih.gov/42855228/)
47. Lázaro G, et al. HLA-DRB1 Allelic Combinations Differentially Shape Dendritic Cell Antigen Presentation Enhanced by Tumour Cell Line Lysate-Pulsing. *HLA*. 2026. PMID: [41607090](https://pubmed.ncbi.nlm.nih.gov/41607090/)
48. Struckman NE, et al. A T-cell receptor targeting RUNX1 frameshift mutations in acute myeloid leukemia. *Leukemia*. 2026. PMID: [41388195](https://pubmed.ncbi.nlm.nih.gov/41388195/)
49. Schmitt TM, et al. Dysregulated expression of the tumor suppressor p14ARF in cancer provides an effective target for TCR-T cell therapeutics. *Journal for ImmunoTherapy of Cancer*. 2026. PMID: [41638872](https://pubmed.ncbi.nlm.nih.gov/41638872/)
50. Kehm H, et al. Dissection of the T cell infiltrate in mouse pancreatic tumors reveals an extensive and diverse tumor-reactive T cell repertoire. *Science Advances*. 2026. PMID: [41961941](https://pubmed.ncbi.nlm.nih.gov/41961941/)
51. Zeng Y, et al. Structural basis for TCR recognition of a Rac1 neoantigen arising from anchor residue mutation. *Journal of Structural Biology*. 2026. PMID: [42190883](https://pubmed.ncbi.nlm.nih.gov/42190883/)

---

Journal names are given in their common form here for readability; the pipeline
stores and checks the full MEDLINE journal title as PubMed returns it. Titles,
PMIDs, journals and years are bibliographic facts reproduced for verification —
no abstract text from any of these papers appears in this repository.
