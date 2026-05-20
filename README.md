# cost_estimation_ml

Demoing cost estimation ml-model and reflecting different use cases and different perspectives and tools on construction project data. Core problem is inconsistent and unstandardized way of writing documentation for projects in general.

Current interesting points:
- Simple model to estimate costs based on certain features, mainly regression models
- LLM-api assistent exposed to project data (unstructured data at the moment)
- Text data vectorization to categorize similar projects

Current problems and limitations:
- Ustructured data, no clear datapipeline, no clear data storage architecture
- Unstructured and inconsistent conventions in writing documentation by and large: this is a structural problem in the domain of current affiliates
- Most existing projects are small and in such stage that full documentation does not exist
- Inconsistent drawing annotations and marks by and large

Future hopes and dreams:
- A clear datapipelinen would serve a limitless base for different use cases for utilizing data
- As clawdBot (open claw) showed, a powerful LLM-assistant in the datapipeline and backend (isolated via service layer) would benefit users tremendously
- A domain as slow and old as construction would benefit from data utilization in a "white-collar" sense, and in my personal point of view is not being utilized nearly to its full potential. This view is shared by all affiliates i have ever worked with, from construction site workers to managers, to consultants and owners to real estate development leaders.
- Just by automating repetitive knowledge-work would benefit the whole industry as a whole, and utilizing data would greatly benefit each sub-domain end-to-end