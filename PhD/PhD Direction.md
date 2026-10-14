---
title: PhD Direction
aliases: [PhD чиглэл, Судалгааны чиглэл, 博士方向]
tags: [phd, research, direction, catalysis, machine-learning, dft]
advisor: Li Fengyu (Inner Mongolia University, Hohhot)
status: deciding
created: 2026-10-14
---

# PhD Direction

> [!summary] TL;DR
> I haven't chosen yet. Of my six possible paths, the three **catalysis** ones (**B, D, F**) lead, and they are too close to pick just one.
> **Plan:** combine them. The thesis *goal* comes from **F** (green hydrogen & CO₂), the *methods* from **D** (few-shot ML potentials with uncertainty), and the *first paper* from **B** (Li Fengyu's double-atom catalyst line).
> **Step 0:** ask Li Fengyu what his 2026–2029 NSFC grant covers. If it clearly points at one line, that beats every score in this note.

> [!quote] Монголоор товчхон
> Би одоохондоо чиглэлээ сонгоогүй байна. Зургаан замаас катализын гурав (**B, D, F**) тэргүүлж байгаа ч хоорондоо маш ойрхон.
> **Төлөвлөгөө:** гурвыг нийлүүлэх. Зорилго нь **F** (ногоон устөрөгч ба CO₂), арга нь **D** (цөөн өгөгдлөөр сургадаг MLIP + тодорхойгүй байдлын үнэлгээ), анхны нийтлэл нь **B** (багшийн хос атомт катализаторын чиглэл).
> **Эхний алхам:** Li Fengyu багшаас 2026–2029 оны NSFC төсөл юуг хамардгийг асуух.

## Where I am now

| | |
| --- | --- |
| **PhD** | Inner Mongolia University (Hohhot), advisor **Li Fengyu** |
| **Background** | Electrical engineering; now building DFT and ML skills |
| **Want** | Pick a direction soon · keep the option of working in Mongolia · earn well afterwards |

**Li Fengyu's research lines** (from my PhD Topic Layers board):

- Single- and double-atom catalysts (SAC / DAC)
- High-throughput discovery of new 2D materials
- Polar and magnetic 2D materials
- Boron and cluster materials
- DFT + machine learning

## The six paths

| | Path | Mongolia | Money | In one line |
| --- | --- | :---: | :---: | --- |
| **A** | Moiré excitons × ML | 1/5 | 2/5 | My biggest head start, but no use at home and heavy on compute |
| **B** | Double-atom catalysts × ML | 3/5 | 3/5 | Li Fengyu's core line; fastest first paper |
| **C** | 2D ferroelectrics | 1/5 | 3/5 | Best fit for an EE identity, but pays mainly abroad |
| **D** | Few-shot MLIP screening | 2/5 | 5/5 | Best-paid skill set (AI for materials); can be remote |
| **E** | 2D discovery × ML | 1/5 | 3/5 | Li Fengyu's own line; safe academic path (teach at NUM or MUST) |
| **F** | Green-hydrogen & CO₂ catalysts × ML | 4/5 | 3/5 | Strongest link to Mongolia |

![[phd-paths-map.svg]]

**What my Direction simulator says:** F 69 · B 68 · D 66. That's too close to call.
- With a strong Mongolia weight, F leads by only one point.
- With "earn well", D and F tie at the top.
- Either way, the catalysis cluster (B, D, F) clearly beats A, C and E.

> [!note] These scores are estimates
> The Mongolia and money scores are my own 1–5 guesses, and F was first scored too high and then lowered. Change them if I see a path differently.

## The plan: combine B + D + F

![[phd-combine.svg]]

| Piece | Comes from | What it gives me |
| --- | --- | --- |
| **Data & first paper** | **B**: double-atom catalysts | Advisor fit. It's the group's core line, with existing know-how and workflows |
| **Methods** | **D**: few-shot MLIPs + uncertainty | The skill that pays: AI-for-materials work I can sell remotely or to mining and finance companies |
| **Goal** | **F**: green H₂ & CO₂ | The Mongolia link: electrolysis catalysts and CO₂ conversion for the Gobi and Inner Mongolia |

**Working title (draft):** *Machine-learning-accelerated design of double-atom catalysts for green hydrogen and CO₂ conversion*
*Машин сургалтаар хурдасгасан хос атомт катализаторын загварчлал: ногоон устөрөгч ба CO₂ хувиргалт*

## What the thesis actually computes

Catalysts for hydrogen work best when hydrogen sticks to them **neither too strongly nor too weakly**. DFT can measure that for a few candidates, but slowly. An ML potential can check thousands quickly, so I only spend DFT time on the best ones.

![[phd-volcano.svg]]

| Term | Plain meaning | Why it matters to me |
| --- | --- | --- |
| **DFT** | Quantum-mechanics calculation of a material's energy from its electrons. Accurate but slow (hours per structure) | Gives the "true" numbers that everything else learns from |
| **MLIP** | Machine-learning interatomic potential: a neural network trained on DFT energies and forces. Close to DFT accuracy, thousands of times faster | Lets me screen many candidates and run long MD |
| **Few-shot fine-tuning** | Start from a pre-trained universal MLIP (MACE-MP-0, CHGNet) and adapt it with a small number of DFT calculations | Saves months of DFT; this is what's new in path D |
| **Uncertainty (ensembles)** | Train several models; where they disagree, the prediction can't be trusted, so run DFT there | Tells me which DFT calculations are worth doing (active learning) |
| **SAC / DAC** | Single- / double-atom catalyst: one isolated metal atom, or a pair, anchored on a support such as graphene or a 2D material | Uses almost no precious metal; a pair can do chemistry a single atom can't |
| **HER** | Hydrogen evolution reaction, 2H⁺ + 2e⁻ → H₂: the hydrogen-making half of water electrolysis | The reaction behind green hydrogen |
| **ΔG<sub>H*</sub>** | Free energy of one H atom bound to the catalyst | One number that predicts HER activity: best near 0 |
| **Volcano plot** | Activity vs. binding strength. Too strong or too weak is bad; the top is best | Shows what my screening is aiming at |
| **CO₂RR** | CO₂ reduction reaction: turning CO₂ into CO, formic acid, methanol and so on, using electricity | The link to coal-region CO₂ |
| **NSFC** | National Natural Science Foundation of China grant | Decides what the group is funded to do |

## A 3-year plan: one paper a year

![[phd-3-year-plan.svg]]

| Year | Paper | Path | What | Why it's doable |
| :---: | --- | :---: | --- | --- |
| 1 | Paper 1 | **B** | DFT dataset of double-atom catalysts on one 2D support; screen for HER by ΔG<sub>H*</sub> with a simple ML model | Builds on the group's existing line and workflow |
| 2 | Paper 2 | **D** | Fine-tune a universal MLIP with few DFT points + ensemble uncertainty, in an active-learning loop | Paper 1's data becomes the benchmark |
| 3 | Paper 3 | **F** | Use the MLIP to screen catalysts for CO₂ reduction (or HER under real conditions) → thesis | Method and data already exist by then |

## Is it useful in Mongolia? Will it pay?

**Mongolia:**
- The OECD (2025) wrote a renewable-hydrogen strategy report for Mongolia at the request of its Ministry of Economy and Development. It says the solar and wind potential is high. Early projects need *domestic* buyers, because export infrastructure will take years, and water use is an issue.
- Elixir Energy has proposed a green-hydrogen pilot in the Gobi to sell to steelmakers in northern China, such as Baotou. So far these are plans, not a running export business.
- Next door, Sinopec started building a ~30,000 t/year green-hydrogen plant in **Ordos, Inner Mongolia** in 2023. It feeds a coal-to-chemicals plant. This is the industry that needs better electrolysis and CO₂ catalysts, right next to Hohhot.

**Money:**
- Academic pay inside Mongolia is low. An earlier rough estimate put Ulaanbaatar lecturers at about **$450–1,000 a month**; I couldn't re-check that source.
- So the money mostly comes from **D's ML skills**: training and fine-tuning ML potentials, uncertainty, Python. They work for AI-for-materials jobs abroad or remotely, and as data/ML work for mining companies and banks at home.

## Risks

> [!warning] Things that could go wrong
> - **Too broad.** "B + D + F" can sprawl. Each paper should use one support, one family of metal pairs and one reaction.
> - **Crowded field.** There are many DAC × ML papers. My novelty has to come from the method (few-shot + uncertainty) or from a new 2D support.
> - **Compute.** Training MLIPs needs a GPU. I have to ask what the group has.
> - **Mongolia's hydrogen is still plans, not plants.** F's Mongolia score is a bet. D's ML skills are the hedge.
> - **Learning curve.** I don't have HER notes yet, so there's catching up to do before Paper 1.
> - **The scores are mine.** The NSFC grant and Li Fengyu's view outrank them.

## Questions for Li Fengyu

1. What does your 2026–2029 NSFC grant cover, and which part could become my thesis?
2. Does the group already have SAC/DAC DFT data or workflows that my first paper can build on?
3. Are you open to ML-potential (MLIP) work, and what GPU or cluster access can I use?
4. HER or CO₂ reduction: which does the group prefer, and do we have experimental collaborators?
5. What do I need to graduate (number of papers, journal level), and by when?

> [!note]- 中文版 (to show Li Fengyu)
> 1. 您2026–2029年的国家自然科学基金项目主要研究什么？哪一部分可以作为我的博士课题？
> 2. 课题组是否已有单原子/双原子催化剂的DFT数据或计算流程，可以作为我第一篇文章的基础？
> 3. 您是否支持我做机器学习势（MLIP）方向？课题组有哪些GPU或超算资源可以使用？
> 4. 析氢反应（HER）和CO₂还原，课题组更倾向哪一个？有没有做实验的合作者？
> 5. 毕业要求是什么（文章数量、期刊级别）？时间安排如何？

## Next steps

**Next 2 weeks**
- [ ] Book a meeting with Li Fengyu and ask the 5 questions
- [ ] Read Nørskov et al. 2005 (the HER volcano) and one recent review on double-atom catalysts
- [ ] Reproduce one ΔG<sub>H*</sub> calculation (H on Pt(111)) with DFT
- [ ] Install MACE or CHGNet and run the pre-trained model on one structure

**Next 90 days**
- [ ] Fix Paper 1's scope: one 2D support, a set of metal pairs, HER
- [ ] Run the first DFT batch (~100 structures)
- [ ] Train a first ML model on ΔG<sub>H*</sub> and make the volcano figure
- [ ] Write Paper 1's outline and show it to Li Fengyu

## First reading

- Nørskov et al., *Trends in the Exchange Current for Hydrogen Evolution*, J. Electrochem. Soc. (2005): the HER volcano and the ΔG<sub>H*</sub> ≈ 0 rule
- Qiao et al., *Single-atom catalysis of CO oxidation using Pt₁/FeOx*, Nature Chemistry (2011): where single-atom catalysis started
- Chanussot et al., *Open Catalyst 2020 (OC20) Dataset and Community Challenges*, ACS Catalysis (2021): the big ML-for-catalysis dataset
- Deng et al., *CHGNet as a pretrained universal neural network potential for charge-informed atomistic modelling*, Nature Machine Intelligence (2023)
- Batatia et al., *A foundation model for atomistic materials chemistry* (MACE-MP-0), arXiv (2023)

## Sources

- [OECD: Towards a renewable hydrogen strategy for Mongolia](https://www.oecd.org/en/publications/towards-a-renewable-hydrogen-strategy-for-mongolia_15122489-en.html)
- [Mongolia Weekly: Can Mongolia become a hydrogen exporter?](https://www.mongoliaweekly.org/post/can-mongolia-become-a-hydrogen-exporter)
- [China Daily: World's largest green hydrogen plant breaks ground in Ordos](https://innermongolia.chinadaily.com.cn/2023-02/17/c_859588.htm)
- [Energy Intelligence: Sinopec's Ordos H₂ project](https://www.energyintel.com/00000186-77cb-d1cb-a3ee-f7ff1b3d0000)

## Related

- [[PhD — ойлгох ёстой бүх зүйл]]
- [[MLIPs]]
