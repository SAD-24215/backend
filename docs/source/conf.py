# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from dotenv import load_dotenv


project = 'Carting Docs'
copyright = '2026, SAD-24215'
author = 'SAD-24215'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
dotenv_path = os.path.join(root_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

sys.path.insert(0, os.path.abspath('../../app'))
sys.path.insert(0, os.path.abspath('../../'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'ru'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
