# Project Plan: Startupticker Data Insights

## Goal
Develop a prototype to provide data insights from Startupticker data, addressing both use cases: (1) trend recognition with semantic search and (2) benchmarking for investors and support organizations, prioritizing feasibility and reachability for a demo.

## Phase 1: Data Preparation & Integration

1.  **[ ] Load Data:**
    *   Read `Data-startupticker.xlsx` into a pandas DataFrame.
    *   Read `Data-crunchbase.xlsx` into a pandas DataFrame.
    *   Optional: Create a web scraper for SOGC data if time permits.
    *   **How:** Use the pandas library in Python (`pd.read_excel`).
    *   **Tools:** Python, Pandas, Beautiful Soup/Scrapy (optional)
2.  **[ ] Explore Data:**
    *   Analyze columns, data types, missing values, and unique values in both datasets.
    *   Understand the fields using the README and Crunchbase data dictionary (`full_data_dictionary_crunchbase.pdf`).
    *   Identify potential keys for merging or linking data (e.g., company names, domains, CHE codes for entity resolution).
    *   Extract text descriptions, sector information and other categorical data for later semantic analysis.
    *   **How:** Use pandas functions (`.info()`, `.describe()`, `.isnull().sum()`, `.nunique()`, `.value_counts()`). Use basic plotting for distributions.
    *   **Tools:** Python, Pandas, Matplotlib/Seaborn
3.  **[ ] Clean & Preprocess Data:**
    *   Develop strategies for handling missing values:
        *   Conditional imputation (e.g., industry-based averages for missing funding data).
        *   Mark categorical missings as 'Unknown'.
        *   Drop rows with critical missing values when necessary.
    *   Standardize data formats:
        *   Dates (e.g., 'Founding year' to datetime objects in ISO format).
        *   Currency/Funding amounts (convert to numerical type, handle different currencies if present).
        *   Normalize text fields (lowercasing, special character removal, standardized abbreviations).
        *   Standardize sector names with a consistent taxonomy.
        *   Canton names and geographical classification.
    *   Create a unified dataset by merging/joining relevant tables using entity resolution:
        *   Implement fuzzy matching algorithms using Levenshtein distance for company names lacking exact matches.
        *   Use CHE codes (if available) as primary identifiers.
    *   **How:** Use pandas functions for data manipulation, fuzzy matching libraries (fuzzywuzzy, recordlinkage).
    *   **Tools:** Python, Pandas, NumPy, fuzzywuzzy
4.  **[ ] Feature Engineering:**
    *   Derive new features useful for analysis:
        *   Company age at time of investment.
        *   Time between funding rounds.
        *   Growth rates from sequential funding rounds.
        *   Binary flags for status (e.g., acquired, liquidated).
        *   Binary flags for special attributes (female-led, spin-offs, award winners).
        *   Geographical classifications (aggregate Canton data into economic regions).
        *   Create industry hierarchy with primary sectors and subsectors.
    *   Create temporal features to enable time-series analysis of trends.
    *   Calculate derived metrics like funding efficiency, growth velocity.
    *   **How:** Use pandas datetime functions, custom calculations.
    *   **Tools:** Python, Pandas

## Phase 2: Ontology & Semantic Analysis for Trend Recognition (Use Case 1)

5.  **[ ] Ontology Development:**
    *   Design a hierarchical structure with key dimensions:
        *   Industry (Biotech, Fintech, Cleantech, etc.) with subsector relationships.
        *   Technology (AI/ML, Blockchain, Advanced Materials, etc.).
        *   Funding Stage (Pre-seed, Seed, Series A through E, Exit).
        *   Geography (Economic regions and tech hubs).
        *   Business Model (B2B, B2C, Marketplace, SaaS, etc.).
    *   Define inter-dimensional relationships (e.g., how technologies map to industries).
    *   Create taxonomic hierarchies with "is-a" relationships.
    *   Implement in a suitable format (simple JSON structure for this prototype).
    *   **How:** Create structured dictionaries/mappings of terms and relationships.
    *   **Tools:** Python, JSON
6.  **[ ] Text Processing:**
    *   Extract and clean text data from relevant fields (company descriptions, sector information, etc.).
    *   Create a corpus of documents for analysis (one document per startup).
    *   Preprocess text data (tokenization, stop word removal, lemmatization).
    *   **How:** Use NLTK or spaCy for text preprocessing.
    *   **Tools:** Python, NLTK/spaCy
7.  **[ ] Semantic Model Implementation:**
    *   **Recommended Model: Sentence-BERT (sBERT)**
        *   Optimized for semantic similarity comparison with fixed-size sentence embeddings.
        *   Support for multiple languages (crucial for Swiss market with German/French/Italian regions).
        *   Computationally efficient for search applications.
    *   **Alternatives (if computational resources are limited):**
        *   TF-IDF vectorization as a simpler alternative.
        *   LDA (Latent Dirichlet Allocation) for topic modeling.
    *   Generate embeddings for company descriptions, sectors, and other textual data.
    *   Store embeddings for efficient similarity computation.
    *   **How:** Use HuggingFace's transformers for Sentence-BERT or scikit-learn for alternatives.
    *   **Tools:** Python, Transformers, scikit-learn, FAISS (for vector storage)
8.  **[ ] Trend Analysis Implementation:**
    *   **Clustering Approach:**
        *   Primary: K-means with automatic K selection (Silhouette analysis, Elbow method).
        *   Secondary: HDBSCAN (Hierarchical Density-Based Spatial Clustering) for identifying irregular clusters and outliers.
    *   Implement trend detection by analyzing temporal patterns in:
        *   Company creation rates by sector/technology.
        *   Funding events and amounts over time.
        *   Semantic shifts in company descriptions.
    *   Create functions to search semantically similar companies given a text query.
    *   Generate visualizations (trend lines, cluster plots) to show identified trends.
    *   **How:** Use scikit-learn for clustering, pandas for time series analysis.
    *   **Tools:** Python, scikit-learn, pandas, plotly/matplotlib

## Phase 3: Benchmarking Analytics (Use Case 2)

9.  **[ ] Define Benchmarking Metrics:**
    *   Identify key metrics relevant to startups and investors. Examples:
        *   Average/median funding per round.
        *   Total funding raised.
        *   Time between funding rounds.
        *   Company age at different funding stages.
        *   Number of startups founded per year/sector/canton.
        *   Distribution of deal types (funding, acquisition, liquidation).
        *   Growth velocity between funding rounds.
    *   Decide on aggregation levels (e.g., overall, by sector, by canton, by founding year range).
    *   Define peer group selection criteria for comparisons.
    *   **How:** Analyze data distributions, consider use case 2 from README.
    *   **Tools:** Data Analysis (using Pandas), Domain knowledge.
10. **[ ] Calculate & Validate Metrics:**
    *   Implement functions to compute the defined metrics.
    *   Use pandas grouping and aggregation functions.
    *   Create statistical tests to validate metrics and identify significant patterns.
    *   Implement comparative analysis functions to enable benchmarking.
    *   Create quartile indicators to show relative performance within peer groups.
    *   **How:** Write Python functions using Pandas, implement statistical tests.
    *   **Tools:** Python, Pandas, SciPy, statsmodels

## Phase 4: Dashboard Implementation

11. **[ ] Set Up Dashboard Framework:**
    *   Select and install appropriate framework (Streamlit recommended for rapid prototyping).
    *   Create the basic structure for both use cases.
    *   **How:** `pip install streamlit`, create app files.
    *   **Tools:** Python, Streamlit
12. **[ ] Implement Semantic Search Component:**
    *   Create a search interface for trend recognition.
    *   Develop visualization of semantic clusters and trends.
    *   Implement ontology-based filtering and faceted navigation.
    *   **How:** Use Streamlit input widgets, integrate with semantic model.
    *   **Tools:** Python, Streamlit, Plotly
13. **[ ] Implement Benchmarking Component:**
    *   Create interactive peer comparison interface.
    *   Develop multi-dimensional visualization for benchmarking.
    *   Implement filtering by various criteria (sector, stage, year, etc.).
    *   **How:** Use Streamlit widgets, connect to benchmarking functions.
    *   **Tools:** Python, Streamlit, Plotly
14. **[ ] Refine and Test:**
    *   Thoroughly test all analytics and visualizations.
    *   Ensure accuracy of metrics and trends identified.
    *   Optimize any slow calculations with caching.
    *   **How:** Manual testing, code review, profiling.
    *   **Tools:** Python profiling tools, Streamlit caching, manual testing

## Phase 5: Presentation & Demo Prep

15. **[ ] Prepare Presentation Slides:**
    *   Outline the problem, solution approach, data sources used.
    *   Showcase both use cases with examples.
    *   Explain the analytics methodology and insights generated.
    *   Address judging criteria (visual design, feasibility, reachability).
    *   **How:** Use presentation software.
    *   **Tools:** PowerPoint, Google Slides, etc.
16. **[ ] Prepare Live Demo:**
    *   Ensure the application runs reliably locally.
    *   Prepare specific scenarios that showcase both use cases:
        *   Trend discovery example: "Show emerging trends in Swiss fintech sector"
        *   Benchmarking example: "Compare this biotech startup against peers"
    *   Script the demonstration flow for efficiency.
    *   **How:** Run the Streamlit app locally, practice demonstration.
    *   **Tools:** Streamlit

## Key Considerations:

*   **Balance Both Use Cases:** Both trend recognition and benchmarking are core requirements, allocate time accordingly.
*   **Model Selection:** Choose NLP/ML models that balance accuracy with implementation simplicity - Sentence-BERT is recommended.
*   **Data Quality:** Be prepared for inconsistencies or missing data in the real-world datasets. Document cleaning decisions.
*   **Computational Efficiency:** Ensure analytics can run reasonably quickly for the demo - use caching and simplified models if needed.
*   **External Data:** Consider SOGC data for enrichment only if essential and feasible within timeframe.
*   **Testing with Real Queries:** Test the system with realistic queries that investors and startups might ask.