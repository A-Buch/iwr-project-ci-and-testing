# IWR-PROJECT FOR CONTINUOUS INTEGRATION AND AUTOMATED TESTING
**Test repository based on: ATTRICI - counterfactual climate for impact attribution**


Code implementing the methods described in the paper `ATTRICI 1.1 - counterfactual climate for impact attribution` in Geoscientific Model Development. The code is archived at [ZENODO](https://doi.org/10.5281/zenodo.3828914).


This is a documentation about a small project to implement Continuous Integration (CI) and automated testing in an existing project.
The aim of CI is to fasten and simplify maintenance, code updates and extension as well as debugging for the GitHub repository Attrici.
Initially a python project template was used to set up the framework. Subsequently, an Anaconda (conda) environment and Poetry for dependency management 
were initialized, packages relevant for the Attrici-toolbox were installed inside this environment. 
Continuous Integration was further done to make sure that the code maintains a certain code format and that main aspects of the Attrici code in the repository 
are always executable - independently from the different states of the toolbox. This is achieved by examples of unit and integration tests to ensure that every time 
when changes are pushed to the development branch these changes are automated tested on their consistency to the existing code. 


The workflow for CI is stored in `.github/workflow/ci.yml`


## Installation
* create conda env: `conda create -n test_env python=3.10.11` 
* Load poetry package `pip install poetry`and install dependencies `poetry install`
* Create example files `poetry run python run_estimation.py`
* Run tests `poetry run python -m unittest tests.py `

## Usage
From root dir: 
`poetry run python run_estimation.py`
`poetry run python write_netcdf.py`



## Poetry setup

Several contributors work on the Attrici project from time to time. To overcome platform dependent installation processes and minimizing conflicts between packages a poetry environment was build inside a new conda environment.
To obtain the strength between both management systems conda environments and poetry can be used together. Conda is for managing the general environment setting and the used python version, i.e. it creates an isolated environment forming the basis for a set of packages and their dependencies, while poetry can be used inside this conda environment for handling python and non-python packages. Using both management systems ensures a consistent and isolated environment, which leads always to the same results independently from the OS.

From the already existing repository for Attrici the most recent branch was used to fill the project template (last updated September 2023). The development and testing were done on a development branch, the final version was latter pushed to the main branch. The installation of dependencies was replaced by the python management system of poetry. Poetry is a CLI app and can simply installed via pip. 
In the original version of Attrici, packages were tried first to be installed by conda, however this was quite time-consuming due that a mix of different packages and distributions often resulted in inconsistent virtual environments at the first try.
To avoid repairing incompatibilities between packages as well between the contributor’s platforms, poetry was utilized to solve these time-consuming installations by a harmonized set of packages and their dependencies. Especially the previous installations of the pymc package were often incompatible with other libraries such as pytensor. To avoid these incompatibilities the loadable pymc version is limited in the pyproject.toml to >=5.30 and <=5.9.0.  The minimum versions of some other python packages were set based on experience, enabling the updating of these packages to newer versions. Compared to conda environment which automatically uses packages only from conda channels, poetry can also load pypip packages and integrates them into the existing environment.

Poetry was configured as follows: 
Initially a conda environment is activated, in which poetry will be later used. Furthermore, the python version is set to 3.10.11.
Poetry is written in python and therefore quite simple to install via pip or conda. For this project it was installed via conda. Poetry is initialized for existing projects via `poetry init`. Project information such as project name, author, license etc. are set up interactively in the shell. This creates two files, one poetry.lock file for the actual installation process and one pyproject.toml file containing project information and package names and versions. If toml file and lock file already exist and poetry should be installed in a new conda environment (e.g. with another python version) poetry environment is called by `poetry install’.
The added packages and optionally the minimum and maximum package versions are first just collected within the pyproject.toml file. Adding packages to projects is done by `poetry add <package_name>`, while only for pymc a minimum limit of the package version is installed by `poetry add pymc>=5.0.0`. 
Similar as for conda installations the dependencies can be automatically installed. The installation process in poetry this is done usually by calling `poetry update` which comprises two steps: First it resolves incompatibilities based on the defined dependencies in pyproject.toml and creates or updates the lock file with the user-defined packages and related subpackages. In a second step the actual package and subpackage installations are performs. Alternatively, both steps in `poetry update’ can be done as well by first calling `poetry lock` (first step) and then `poetry install` (second step).
After the installation process the lock file contains all from the user selected packages, their dependencies, and extra settings such as defined line-length or code styles for Ruff and Black. 
In the toml file settings for python linter and formatters can be easily defined. The usage is exemplified by increasing the allowed line-length to 150 characters and auto-fixtures for Ruff were enabled. Certain files or file types, such as jupyter notebooks, were set to be ignored by Ruff. Furthermore, the review of certain code styles in single files were excluded, e.g. pycodestyle in tests.py.
The final poetry environment can be activated via `poetry shell `. Python code can be run in the shell by `poetry run python <python_file.py>`.
In a later state changes to the environment can be easily done, either by calling `poetry add <package_name=other_version>` (mainly for defining new package versions) or just changing the definitions in the pyproject.toml  (mainly used for changing definitions in dev-dependencies) and updating the environment with the new settings via `poetry update’. In the toml file the user-defined packages are in the section tool.poetry.dependencies, stored as <package_name= "version”>. Packages relevant for the development such as test packages, linters and code formatters are stored in section tool.poetry.dev-dependencies.

## Automated testing
For the Continuous Integration of code several smaller tests were written to mainly check the output of important functions for processing artificial climate data. A good test suite comprises several types of tests, including unit tests as the main part and supplemented by integration, acceptance and performance tests. The types of tests differ in their goals. From the four types of python tests, following are implemented as examples in this project:
* Unit tests to check the behaviour of a method or function for base cases as well as for edge cases.
* An integration test as an example to test the behaviour of new or modified code to the rest of the application. Integration tests are important to guarantee that the different components of an application work correctly together.

Unit tests were written while developing the code inside a Jupyter Notebook (test-driven development), using the test package ipytest customised to run tests inside Jupyter Notebook. Later the example tests were added to a python script which is uploaded on github. In general, Jupyter Notebooks were not uploaded on git, instead only the final versions of code snippets were pushed via python files to the development branch. 
For the unit test the intern standard python test framework was used, so no additional package for unit tests was downloaded.
As mentioned before integration tests are done to check that the components of a project correctly work together. This is particularly important when several developers are working on the same project and changes to the code need to be verified for compatibility with the rest of the project. 
The automation of testing is done by calling test.py via `python -m unittest tests/tests.py` or `poetry run python -m unittest tests/tests.py`. The tests contained in the test file are automated called by:

## Continuous Integration with GitHub Actions
In this project it was decided to exemplify the functioning of GitHub Actions instead of pre-commit hooks. Pre-commits are used to check the code before it is pushed to a remote repository, so it runs on the local machine. It fulfils a similar function as GitHub Actions, namely, to ensure that the shared code meets certain requirements, e.g. runs under different OS or python versions, as well as complies with pep-standard or other code formats.  It was decided to test new or modified code after it was pushed to the remote repository. Consequently, a virtual environment is created by GitHub and do there the testing. This behaviour is advantageous for package development when the final application can be installed on multiple OS. Also, when the project is a joint work of multiple contributors working from different OS, as done for the Attrici-toolbox, GitHub Actions are preferable over pre-commits. Implementing unit testing as a GitHub Action, makes it possible to run the test on these systems as well. Disadvantage is that only certain tests, such for functions to connect to an API or database, do not make sense as a GitHub Action, due that they have to run on the local machine. 
The uploaded code was tested for its usability under the newest ubuntu version with python 3.10. As part of the Continuous Integration of code to the remote repository the code style was examined for discrepancies by a python linter and code formatter called Ruff. It is established in the project to automatically repair improper code formats, likewise it splits too long code lines into multiple lines (max set to 150 characters). Benefit of Ruff as a linter is its fast performance. With incorporating Ruff as part of the Continuous Integration, the linter and formatter is automatically applied, every time when code changes are pushed to the develop branch. 
Besides the verification of code style, also the previous mentioned unit and integration tests are run as jobs inside a GitHub Action. In general, Jupyter Notebooks were not pushed to the repository, therefore they are not covered by the integration tests. Rather code snippets such as new functions or modified methods were tested directly inside the notebook.  

## Links related to the project
* Cookiecutter project: https://github.com/ssciwr/cookiecutter-python-package
* Stage of original Attrici project used to build test repository: https://github.com/ISI-MIP/attrici/tree/cff389d3ee55cb41d6e0ee9b812b44f2ec1c32d2





## Credits

We rely on the [pymc3](https://github.com/pymc-devs/pymc3) package for probabilistic programming (Salvatier et al. 2016).

An early version of the code on Bayesian estimation of parameters in timeseries with periodicity in PyMC3 was inspired by [Ritchie Vink's](https://www.ritchievink.com) [post](https://www.ritchievink.com/blog/2018/10/09/build-facebooks-prophet-in-pymc3-bayesian-time-series-analyis-with-generalized-additive-models/) on Bayesian timeseries analysis with additive models.

## License

This code is licensed under GPLv3, see the LICENSE.txt. See commit history for authors.