# UAE Climate Financial Risk Intelligence Platform

## Full product concept

**A UAE-native, Arabic and English platform that helps banks, insurers, investors and regulators understand how physical climate hazards could affect assets, borrowers and financial portfolios, and decide where to act.**

The platform connects financial records to asset locations, climate hazards and building characteristics. It translates those connections into transparent estimates of physical damage, business interruption and financial exposure. It then supports portfolio stress testing, adaptation planning, monitoring and evidence-backed reporting.

The ambition follows the broad physical-risk intelligence model demonstrated by Jupiter Intelligence. The implementation would be independently built, with appropriately licensed scientific data and models, UAE-specific workflows and bilingual access. No Jupiter affiliation, proprietary technology access or equivalent predictive performance is implied.

This is a proposed product specification. Features below describe the intended platform, not capabilities already built or validated. The first prototype is defined separately near the end.

## 1 The problem we solve

A bank can know a borrower's financial statements, outstanding loan and collateral valuation without knowing how a flood, extreme heat or coastal hazard could affect the physical assets supporting repayment.

Financial and physical records are disconnected. Loan systems identify companies; property documents describe buildings; hazard datasets describe places. These records must be linked before a risk officer can see a useful financial picture.

The problem is especially consequential when the same event affects both a borrower's operating income and the collateral securing its debt. Several apparently unrelated borrowers may also depend on the same exposed industrial area, access route or utility asset.

The supplied TDRA UAE Hackathon 2026 CBUAE challenge explicitly asks for mapping, quantifying and monitoring these exposures across collateral and asset portfolios. It also highlights fragmented records, inconsistent definitions and missing climate information in financial workflows. [1]

The product would make that assessment repeatable. Its purpose is to help institutions investigate and manage risk; it would not automatically approve loans, change insurance terms or certify compliance.

## 2 The central product promise

**Bring your portfolio. Understand which assets and financial relationships are exposed, what the consequences could be, and which actions deserve attention first.**

The platform should answer five connected questions:

1. Where are the physical assets behind our financial exposures?
2. Which hazards could affect them, over which time horizons?
3. What damage and interruption could result under specified scenarios?
4. Where could losses accumulate across borrowers, sectors or institutions?
5. Which additional information or protective investment would improve the decision?

## 3 Who uses and buys it

| User | Decision supported | Intended output |
|---|---|---|
| Bank credit and portfolio-risk teams | Which borrowers and collateral require deeper review? | Exposure analysis, scenario comparisons and credit-review briefs |
| Insurance and takaful teams | Where might claims accumulate, and what property information is missing? | Location assessments and policy-aware loss scenarios |
| Property investors and asset managers | Which assets require due diligence or resilience investment? | Asset briefs, cash-flow sensitivities and adaptation comparisons |
| Corporate and infrastructure operators | Which facilities or dependencies could disrupt operations? | Site assessments and continuity-planning inputs |
| Financial regulators | Where are shared physical vulnerabilities emerging? | Authorised, consistently defined institution and system-level views |

The proposed first commercial customer is a bank risk team with a property-backed corporate or SME portfolio and an internal sponsor willing to run a controlled pilot. An insurer or property manager could also be a design partner, but the initial workflow should serve one buyer well.

Regulator use is a later deployment path requiring formal authority, data-sharing arrangements and institutional participation. The hackathon statement establishes problem relevance, not procurement commitment.

## 4 The full capability set

### Asset and financial record integration

Accept portfolio spreadsheets, collateral registers, valuation reports, insurance schedules and authorised system exports. Extract company names, property descriptions, asset identifiers, values, policy terms and relevant dates from Arabic and English documents.

Build a relationship model linking institution, facility or loan, borrower, guarantor where applicable, physical asset and insurance arrangement. Represent many-to-many relationships: several facilities may secure one loan, and one asset may secure several exposures. Record allocation rules to avoid double-counting.

For uncertain links, ask a targeted question and preserve the original evidence. Never silently use a company headquarters address as the location of its warehouse or factory.

### Location intelligence

Resolve bilingual addresses, plot references and facility names into coordinates and, where available, building footprints. Store match confidence, source, date and the spatial precision of the result.

Distinguish a verified building footprint from a street-level estimate or district centroid. A location that is too uncertain for meaningful analysis remains unresolved, rather than receiving a falsely precise risk score.

### Multiple physical hazards

The long-term platform would support the following hazard families where appropriate data and validated methods are available:

| Hazard | Relevant assessment |
|---|---|
| Rainfall and surface-water flooding | Water depth, duration, ingress and access disruption |
| River or wadi flooding | Flow-path exposure and inundation scenarios |
| Coastal flooding, storm surge and sea-level rise | Coastal asset and infrastructure exposure |
| Extreme heat and humidity | Cooling demand, equipment limits and operational interruption |
| Wind and severe storms | Building and equipment damage |
| Drought and water stress | Operational dependence on constrained water supplies |
| Hail, wildfire, extreme cold and subsidence | Asset-specific or overseas portfolio assessments where material |

Dust and sandstorm impacts could be a UAE-focused research extension for relevant assets. This would require its own evidence and validation, rather than being introduced as an unsupported risk score.

Initial priorities are flood and heat. Supporting global hazards later would also allow UAE institutions to assess overseas holdings.

### Climate scenarios and time horizons

Allow users to compare a historical baseline with future periods such as 2030, 2050 and later horizons supported by the chosen datasets. Offer clearly identified climate pathways and explain their assumptions.

Match the analysis to the decision: a short loan, a long-lived building and an infrastructure investment need different horizons. Display the spread across models and assumptions where available.

Keep long-term climate projections separate from operational weather alerts. A near-term alert module would require its own forecast feeds, skill testing and service expectations; it is not a substitute for climate-scenario analysis.

### Building vulnerability and operational dependence

Combine hazard intensity with the characteristics that determine damage: construction, floor elevation, basements, equipment placement, building use, protective measures and maintenance condition.

Capture operational dependencies such as critical access routes, utilities and important suppliers when supported by evidence. Mark missing information and show which missing detail could most affect the result.

A useful question might be: “Are the electrical switchboards in the basement or above ground level?” The answer can change the assessment without changing the hazard map.

### Financial impact modelling

Translate physical scenarios into distinct financial outputs:

- Potential repair or replacement costs for buildings, equipment and stock.
- Business interruption and recovery costs, with stated operational assumptions.
- Changes to operating expenses, such as cooling costs, where models support them.
- Potential insured losses after relevant coverage, limits and deductibles.
- Collateral-value sensitivities and possible implications for borrower repayment capacity.
- Expected annual physical loss and event-loss distributions only where a suitable probabilistic model exists.

Financial categories remain separate. Replacement value is different from market value. Physical damage is different from an insurance payout, and both are different from a lender's credit loss.

Changes in probability of default or loss given default require institution-specific credit-model calibration and validation. An early pilot can provide scenario inputs to the institution's existing models instead of claiming to replace them.

### Portfolio stress testing and concentration

Aggregate exposures by borrower, emirate, sector, asset type, hazard, loan maturity and shared dependency. Explore scenarios in which one event affects many assets simultaneously.

Show whether an apparently diversified portfolio has a concentrated physical vulnerability. Account for the dependence between assets and hazards: separately calculated worst cases cannot simply be added as though they happen together.

Allow users to compare a baseline, a stress scenario and a scenario with protective measures. Record the scenario definition and every material assumption so the analysis can be reproduced.

### Adaptation planning and investment

Compare possible measures such as flood barriers, drainage improvements, raised equipment, cooling upgrades and operational continuity measures.

For each measure, show the estimated implementation and maintenance costs, assumed effectiveness, remaining risk and avoided loss over a defined horizon. Calculate net present value or payback only when the necessary inputs are available and disclose sensitivity to those inputs.

The output supports prioritisation and engineering review. It does not certify structural safety, guarantee loss reduction or promise an insurance discount.

### Monitoring and case management

Reassess affected records when collateral values, loan balances, facility characteristics, model versions or hazard datasets change. Show what changed and distinguish a data correction from a new risk signal.

Create review cases with an owner, evidence request, deadline, decision and audit history. Support review checkpoints during lending, renewal, portfolio reviews and capital planning. Users approve consequential decisions.

### Reporting and model governance

Generate Arabic and English asset briefs, portfolio reviews, scenario reports and model documentation. Include definitions, sources, methods, coverage gaps and uncertainty.

Maintain a reviewed mapping between product outputs and applicable institutional or regulatory requirements. Version that mapping by jurisdiction and date. Existing CBUAE climate-risk principles and a climate-related financial-risk regulation must be considered; the product should not be pitched as entering a regulatory vacuum. Exact applicability and reporting obligations require current review. [5]

Provide role-based views for analysts, credit committees, model validators, auditors and authorised supervisors. Do not call an export an official submission or claim CBUAE approval without an established process.

## 5 Arabic integrated throughout

Arabic is a first-class working language throughout the evidence and decision process.

**Document intake:** Read Arabic and English valuation reports, property records, policy schedules and scanned documents. Handle mixed scripts, Arabic-Indic digits, dates, currencies and units while preserving the source image and extracted field.

**Identity and addresses:** Match Arabic names and English transliterations using identifiers and evidence. Ambiguous matches require confirmation. Language similarity alone is insufficient to merge borrowers or properties.

**Interface:** Offer complete right-to-left layouts with correct handling of mixed-language names, coordinates, numerical tables and charts. The same calculation should produce identical numbers in either language.

**Conversation:** Allow questions in English, Modern Standard Arabic and, where tested, Gulf Arabic. A user might ask:

> ما العقارات الأكثر عرضة للفيضانات في محفظتنا، وما حجم التعرض المالي المرتبط بها؟
>
> Which properties in our portfolio are most exposed to flooding, and what financial exposure is associated with them?

The assistant should return the relevant assets, the basis of the assessment, uncertainty and links to supporting records. Voice access can be added after text accuracy is demonstrated.

**Reports:** Produce formal Arabic and English outputs from the same structured results. Maintain an expert-reviewed glossary for concepts such as physical risk, collateral, expected annual loss and scenario analysis.

**Quality control:** Evaluate Arabic extraction, entity matching, numerical consistency and explanation quality separately. Preserve a distinction between conversational language and the formal Arabic used in financial reporting.

## 6 What makes it UAE native

The product would use UAE administrative geography, bilingual location conventions, AED reporting and local institutional workflows. It would support the asset and exposure structures used by conventional banks, Islamic financial institutions, insurers and takaful operators, with institution-specific validation of ownership and financial treatment.

Local hazard, terrain, drainage and property information would be incorporated through appropriate licences and partnerships. Potential counterparties include meteorological, geospatial, municipal and disaster-management bodies. These are proposed data relationships, not existing access rights.

Deployment options would include a UAE-hosted managed environment, a customer-controlled private environment and, where commercially viable, on-premises deployment. Local hosting alone is insufficient: model inference, backups, logs, monitoring and support access must fit the agreed data-handling requirements.

The platform would support climate resilience and financial stability. It should not describe improved risk measurement as a direct reduction in carbon emissions. Carbon accounting and transition-risk assessment are separate potential modules, not substitutes for physical-risk analysis.

## 7 The experience that makes it feel effortless

The opening action is “Upload your portfolio” or “Connect your existing records.” The system identifies missing information and guides the user through only the important unresolved items.

The main review screen shows:

- Which locations and records are confirmed or unresolved.
- Where material exposure is concentrated.
- Which findings changed since the previous run.
- What evidence supports a result.
- Which unanswered questions could materially change the decision.
- Which cases need human review.

Use transparent coverage measures such as “42 of 50 asset locations confirmed.” Avoid a single readiness percentage that mixes document completeness, model confidence and legal compliance.

The proposed distinctive experience is an investigation that progresses from a scattered portfolio to a defensible review case. Arabic and UAE hosting support adoption; the commercial hypothesis is that institutions will value reduced investigation effort and better decisions.

## 8 The signature demonstration

Use a clearly labelled fictional portfolio with a manufacturer, a distributor and a warehouse operator. Their loans appear in different sector categories, but their critical facilities lie within the same illustrative flood-event footprint.

The platform links each facility to its borrower and collateral, identifies the shared exposure and explains how the event could affect both operations and secured assets. One building's equipment location is unknown. The user supplies that detail, and the scenario updates.

The user then compares a protective measure and exports a bilingual review brief. The brief keeps outstanding credit exposure, physical damage estimates and any modelled lender losses in separate columns.

The memorable discovery is that several financial exposures share one physical vulnerability. This is a demonstration of the proposed workflow, not a claim that existing providers cannot analyse concentration.

## 9 Scientific data and calculation design

Four layers must be supported independently: hazard, exposure, vulnerability and financial consequences. A language model may help navigate evidence, but cannot replace any missing scientific layer.

| Layer | Data or method needed | Main validation question |
|---|---|---|
| Hazard | Historical observations, projections, terrain and suitable hazard models | Is the dataset appropriate to this hazard, place, period and spatial scale? |
| Exposure | Asset locations, footprints, values and financial links | Are these the correct assets and relationships? |
| Vulnerability | Damage functions, building attributes and operational assumptions | Are the functions appropriate to the local asset type? |
| Financial consequences | Coverage terms, costs, financial statements and institution models | Are physical impacts translated without double-counting or unsupported credit assumptions? |

Potential inputs include appropriately licensed national data, satellite observations, global climate projections, commercial hazard products, customer records and local engineering evidence. Availability, coverage and permitted commercial use must be checked before choosing a dependency.

For example, NASA's NEX-GDDP-CMIP6 provides climate projections at approximately 25 km resolution. It may inform regional climate analysis; it does not by itself establish building-level flood depth or drainage performance. [6]

Begin by licensing or integrating suitable scientific datasets and models. Independently developed UAE hazard or vulnerability models can become a later research programme with specialist partners.

A simplified physical damage calculation is replacement value multiplied by a damage fraction associated with hazard intensity and asset vulnerability. Event loss is conditional on that event. Expected annual loss requires integration over an appropriate annual event-probability model; it cannot be inferred from one selected scenario.

For every result retain dataset version, spatial resolution, model version, scenario, horizon, source records, assumptions, uncertainty and approval status. Missing coverage must display as unknown, not low risk.

## 10 System architecture and AI responsibilities

The core architecture comprises:

1. Secure ingestion and document extraction.
2. A geospatial asset register and relationship model.
3. Versioned hazard and vulnerability data services.
4. Deterministic financial and aggregation calculations.
5. An Arabic and English assistant grounded in those records and tools.
6. Review workflows, reporting, APIs and audit history.

A practical implementation could use a bilingual web application, a spatial database, object storage for source evidence and separate calculation services. Specific vendors should be selected after checking deployment, licensing, cost and institutional access requirements.

AI can classify documents, extract fields, propose record matches, identify inconsistent evidence, formulate clarifying questions and explain computed results. Approved tools perform numerical calculations. AI must not invent coordinates, hazard probabilities, loss figures, source citations or regulatory approval.

Deploying a UAE-developed model is an option to evaluate, not a guarantee of accuracy or sovereignty. Benchmark candidate models on the actual bilingual tasks and verify where processing occurs.

## 11 Security and responsible decisions

Apply tenant isolation, encryption, least-privilege access, audit logging, retention controls and institution-approved model access. Treat source documents as untrusted input and prevent their embedded instructions from authorising actions or changing analytical rules.

Keep identifiable institution records within the authorised environment. Cross-bank supervisory aggregation requires a lawful purpose, approved sharing arrangements and controls against disclosure or re-identification; it cannot be created simply by combining customer databases.

Users must be able to inspect and correct asset matches and assumptions. Route low-confidence locations or unsupported models to manual review. A coarse map should not automatically cause a borrower to be rejected or a community to lose access to finance.

## 12 Business model and defensibility

The proposed model is an annual institutional subscription, potentially with usage tiers for assets, scenarios or API calls. Charge separately for substantial implementation work, specialist analysis and third-party data costs where necessary. Pilot pricing should be based on customer interviews and delivery costs, not unverified enterprise contract benchmarks.

Begin with a paid, scoped assessment alongside one risk team. Compare the process with its existing workflow and involve a model validator early. Expand to repeat portfolio monitoring and additional hazards after demonstrating value.

Potential defensibility comes from validated local asset matching, licensed data partnerships, locally evaluated vulnerability methods, reliable bilingual workflows and integration into recurring institutional reviews. Customer data remains governed by its agreed rights; it must not be reused to train shared models without permission.

Jupiter already offers broad physical-risk analytics, financial translation, adaptation tools and enterprise delivery. The proposed company must therefore prove an advantage in a defined UAE customer workflow rather than claim that global providers cannot serve the region. [2–4]

## 13 Delivery roadmap

| Stage | Scope | Evidence required to advance |
|---|---|---|
| Hackathon prototype | Synthetic portfolio, Arabic and English interface, one flood scenario, linked exposures and one review brief | Correct links and calculations; clear separation of real and illustrative inputs |
| Design-partner pilot | One institution, one portfolio segment, permitted data, selected hazard and manual validation | Useful findings, acceptable data quality and measurable workflow improvement |
| Production foundation | Access controls, monitored pipelines, validated methods, repeatable reporting and API integration | Security and model review; stable operation; customer adoption |
| Broader platform | Heat and other validated hazards, adaptation modelling, richer insurance and credit integration | Sufficient local validation and demonstrated customer demand |
| Supervisory deployment | Authorised multi-institution reporting and concentration views | Formal data agreements, approved definitions and supervisory sponsorship |

For the hackathon, mock unavailable connectors and use explicitly labelled scenarios where suitable scientific inputs are unavailable. Do not present the prototype as an operational climate prediction engine. Preserve the broad product ambition while demonstrating one complete workflow.

## 14 Success measures and critical tests

Measure location-match accuracy, unresolved-record rates, document extraction accuracy in both languages, reproducibility of calculations, evidence traceability and time required to produce a reviewed assessment.

Assess hazard and damage-model performance against suitable observed events and losses, using independent validation where possible. Track whether predicted uncertainty is meaningful, not just whether a map looks plausible.

The first commercial tests are whether a risk team will provide a redacted sample, whether suitable data can legally and economically cover those assets, whether the result changes a real review decision, and whether the customer will pay for recurring use.

If local data cannot support building-level analysis, offer a clearly scoped screening service and identify where detailed studies are required. If customers already have adequate hazard models, the initial product can focus on connecting those models to fragmented financial and Arabic document workflows.

## 15 Positioning

The company would provide UAE-native climate financial risk intelligence, connecting physical assets to the financial decisions that depend on them.

Its complete vision includes multiple hazards, asset and entity analysis, financial consequences, concentration, stress testing, adaptation, monitoring and governance. Arabic and English are integrated throughout. The initial product earns trust by making one specific financial-risk investigation accurate, transparent and easier to complete.

## Sources and evidence boundaries

Prepared 25 September 2026. Product capabilities, buyer selection and business model are proposals. Sources establish the precedent and problem context; they do not establish product performance or customer demand.

1. User-supplied **Challenge Profile 1 — CBUAE, Climate Financial Risk Intelligence**, TDRA UAE Hackathon 2026, pages 1–2. Primary basis for the challenge mapping. Its root-cause framing should not be treated as a current legal determination.
2. [Jupiter product overview](https://www.jupiterintel.com/products) — physical-risk workflow, delivery options and module scope.
3. [Jupiter real estate and REITs](https://www.jupiterintel.com/by-industry/real-estate-and-reits) — financial-impact and asset-management precedent.
4. [Jupiter adaptation and entity modelling announcement](https://www.jupiterintel.com/blog/adaptation-and-cem-have-arrived-weve-raised-the-bar-on-climate-informed-capital-decisions) — adaptation and entity-analysis precedent.
5. [CBUAE sustainable finance](https://centralbank.ae/en/our-operations/sustainable-finance/) and [CBUAE Climate-related Financial Risk Management Regulation](https://rulebook.centralbank.ae/en/rulebook/climate-related-financial-risk-management-regulation) — existing regulatory context. The regulation is listed in the official rulebook; full article-by-article applicability has not been assessed for this concept.
6. [NASA NEX-GDDP-CMIP6](https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/) — example of available projection data and the importance of spatial-resolution limits.
