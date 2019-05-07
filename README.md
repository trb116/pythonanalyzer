# Repository summary
The *src/* folder contains the main script that replaces all function calls in a python with *foo()*, working on a dataset that resides under *data/input*, whose file paths are specified under *src/paths.txt*. For each file whose file path is contained in the *paths.txt*, the script will generate a side by side comparison between the original and the processed source file that are stored in *data/output*. It will also collect statistics on how many of the function calls are simple calls vs chained calls(like a.b.c() has one chained function call, or a.b.c().d() has two) vs print calls and save a plot in data/call_stats.png

There is also testing functionality in the *test/* folder, which aims to cover various cases of function calls.

## Instructions
### Running python_analyzer
In src/  just run *python python_analyzer.py*
### Testing the main functionality
In test/  just run *python <test_script>.py* (due to lack of time the tests for collecting statistics are in separata files). Feel free to peek at the test inputs and their expected outputs
### Installing RedBaron
I'm not sure if the conda environment does anything, as when I installed redbaron I did so by downloading the repo as a zip, unpacking it and running *python setup.py* but it didn't seem to affect my conda environment at all (you will probaly have to run python setup.py as well, repo is at https://github.com/PyCQA/redbaron). Other than RedBaron I'm only using standard libraries.
## Python files RedBaron isn't able to parse:
```
../data/input/Azure/Azure-MachineLearning-ClientLibrary-Python/azureml/http.py
Untreated elements: '\ufeff# coding: utf-8\n\n#-----------------------  occuring at  ../data/input/Azure/azure-sdk-for-python/azure-mgmt/tests/test_mgmt_apps.py
Untreated elements: '\ufeff#------------------------------------------  occuring at  ../data/input/Azure/azure-sdk-for-python/azure-servicebus/tests/servicebus_settings_fake.py
Untreated elements: '\ufeff#------------------------------------------  occuring at  ../data/input/Azure/azure-storage-python/azure/storage/blob/_chunking.py
Untreated elements: '\ufeff#------------------------------------------  occuring at  ../data/input/Azure/azure-storage-python/azure/storage/table/_error.py
Untreated elements: '\ufeff#------------------------------------------  occuring at  ../data/input/Azure/azure-storage-python/tests/blob_performance.py
Error, got an unexpected token STRING here:

  13 
  14 libraryNotFound = False
  15 
  16 import sys, os, time
  17 try:
  18 	from defcon import Font
  19 except:
  20 	print "ERROR: This script requires defcon. It can be downloaded from https://github.com/typesupply/defcon"<---- here

The token STRING should be one of those: AMPER, AMPER_EQUAL, AND, AT, AT_EQUAL, CIRCUMFLEX, CIRCUMFLEX_EQUAL, COLON, COMMA, COMMENT, DEF, DOT, DOUBLE_SLASH, DOUBLE_SLASH_EQUAL, DOUBLE_STAR, DOUBLE_STAR_EQUAL, ENDL, EQUAL, EQUAL_EQUAL, FOR, GREATER, GREATER_EQUAL, IF, IN, IS, LEFT_PARENTHESIS, LEFT_SHIFT, LEFT_SHIFT_EQUAL, LEFT_SQUARE_BRACKET, LESS, LESS_EQUAL, MINUS, MINUS_EQUAL, NOT, NOT_EQUAL, OR, PERCENT, PERCENT_EQUAL, PLUS, PLUS_EQUAL, RIGHT_SHIFT, RIGHT_SHIFT_EQUAL, SEMICOLON, SLASH, SLASH_EQUAL, SPACE, STAR, STAR_EQUAL, VBAR, VBAR_EQUAL, WITH

Baron has failed to parse this input. If this is valid python code (and by that I mean that the python binary successfully parse this code without any syntax error) (also consider that python does not yet parse python 3 code integrally) it would be kind if you can extract a snippet of your code that make Baron fails and open a bug here: https://github.com/PyCQA/baron/issues

Sorry for the inconvenience.  occuring at  ../data/input/adobe-type-tools/python-scripts/generateAllMarkFiles.py
```
# Original specification is detailed below

# python-analyze

This repository will eventually contain source code to analyze short Python programs.

## Task 1
- Create a small repository (~1000 codes) of Python programs attempting student submissions.

Datasets like these should be helpful to get you started.

https://www.itshared.org/2015/12/codeforces-submissions-dataset-for.html

- Write a script such that for every program in your repository, you replace *every* existing function call with *foo()*.
For instance, if your program reads -
```
def count_list_repeats(li):
    x = 5
    verify_results(li, x)
    ...
```
it should automatically get converted to -
```
def count_list_repeats(li):
    x = 5
    foo(li, x)
    ...
```
Are there special/edge cases to consider? What challenges can you face while attempting to solve this?

- Hint: Do not be tempted to use a regular expression/grep like strategy to make these replacements. Look up what abstract syntax trees of programs are. Modify them to achieve this functionality.

- Have at least one plot, or one table which summarizes relevant statistics from the dataset. To begin with, for the task mentioned above, ask yourself what statistics you think are even relevant and would want answered?

- Evaluation -- How will you evalute whether your algorithm/strategy covers all cases? It could well be we're unsure of this no matter what we do.

## Instructions
- Do not fork this repo. Work on a local copy. Make it a habit to push changes upstream to your repo as frequently as feasible.
- Use `Python3.7+` for this work.
- We workship the lords of reproducability of results. Use `conda` to create an environment and set up your repository. 
- Use a `.gitignore` file to ensure you are not adding junk files to the repo.
- Have a `./src/` folder containing the source.
- Have a `./env/` folder containing the Conda environment file you create for this project.
- Have a `./data/` folder containing all the data your source accesses.
- Have a `./tests/` folder to write out unit tests for key functions. Look up the `unittest` package in Python if you haven't used it before.
- Keep updating this README with instructions which will help with the reproducability of your work/results.

Setting these up can be a little painful and time consuming. Wade through it. Focus on getting the core functionality right first, though.



## Goals
- Have a working prototype
- (We will) assess how well you scope and assess the different components involved which will solve this problem
- Assess how you divide your labor into the components you identify. Remember, there's a time budget of ~2 days.
- Assess how you wiggle out of situations when you're stuck.
- Assess how well you communicate and let all stakeholders know of your progress.
