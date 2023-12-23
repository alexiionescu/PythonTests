## Inheritance method 
Uses conf.json and index.tex.j2  
*py -3 -m jupyter nbconvert .\NbLearn.ipynb --to latex  --TemplateExporter.exclude_input=True --template=alex_latex --debug*  
<span style="color:yellow">WARNING</span>: does not work, need study  

## Workaround  
copy base.tex.j2 to  
**%pythoninstallpath%**\share\jupyter\nbconvert\templates\latex  
**%pythoninstallpath%** = **%localappdata%**\programs\python\python39 (default)  
then use  
*py -3 -m jupyter nbconvert .\NbLearn.ipynb --to latex --TemplateExporter.exclude_input=True*

## Modify notebook metadata
Open .ipynb files as JSON text

<pre><code>
{
 "metadata": {
   "title" :"Learning Jupyter Notebook",
   "authors" : [{"name": "Alex Johnson"}],
 ...
 </code></pre>


 ## Latex directly from notebook
 %%latex 
 magic command sets a cell to latex mode (see [ipython magic comands](https://ipython.readthedocs.io/en/stable/interactive/magics.html))