# cost_estimation_ml

Demoing cost estimation ml-model, local- and api-llm's and reflecting different use cases and different perspectives and tools on construction project data. Core problem is inconsistent and unstandardized way of writing documentation for projects in general, and limited time of course.

All in all this has proven to be a very interesting project. When combined with the project management system and the idea of well-designed database- and data-architecture to a pipeline, and agentic llm serving between APIs and personnel, there seems to be all the tools necessary to create something wildly useful - not unlike ClawdBot - for organizations (and people in general) of all sizes.

My vision and view has moved on to general open source system designed especially to small-to-midsize settings. The pain of my own traversals as a construction entrepreneur was the sparking light of this project, and of the project management system, and i'm hoping to continue to work on this project in the future. If you stumble upon this and read through up to this point, i'd be glad of any opinions and help.

---

WIP:
Currently exploring local llm options for larger text-file parsing and summarization. Biggest problem to tackle is the small context window vs. large text file contents. Bouncing between trying to parse files via fixed engine and just piping the whole (initially parsed) file to a local sub-agent for parsing, and creating a tooling architecture that exposes only key data to a frontier level paid API. Interesting options not yet implemented e.g.

- smaller dataset exposition to a paid frontier level LLM API
- better designed toolsets for api-llm's to reduce token costs
- routing large datasets to small context windows
- sub-agent parsing seems to work fine, but it's too slow for interactive use; this is probably not a poblem if the work is offloaded to idle time and data parsing is handled outside of office-hours

---

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

Files:
This project folder is somewhat arbitrarily structured since most of the data is "proprietary", i.e. small company made-for excel sheets for cost  estimation, and randomly selected documentation from different projects. As such, most of the notebooks are as more of an exploratory form to harvest data from semi-structured and inconsistent files. However, a brief overview:

- reno_parser_featuret.ipynb: data parsing from one affiliate cost estimation excle files.
- data_esikasittely.ipynb: data harvesting and munging, exploring what data is and how it can be converted to more useful form. Some visualization, some parsing, some slicing etc. to be forwarded to model testing.
- mallien_testit.ipynb: model testing notebook. Some general regression model briefing and testing, mainly to (1) see if the data is in a form that a model can accept it (2) compare models in high level (3) see if the models produce useful signals.
- agent_file_demo.py: a very short testing on chatGPT agents SDK framework and how it could be useful as an agentic assistant

Some conlusions:

- data embeddings and semantic search, colpali / byaldi recommended, VLM (visual language model) didn't work, the model is too large for current hardware