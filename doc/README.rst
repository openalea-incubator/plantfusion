PlantFusion Documentation Notes
=====================================

Compile the main doc
*********************

To compile the documentation use make in the doc folder:

.. code-block:: bash
    
    make html

Documentation will be generated (in HTML format) inside the ``build/html`` dir.

Start over
*********************

To clean up all generated documentation files and start from scratch run:

.. code-block:: bash
    
    make clean

Keep in mind that this command won't touch any documentation source files.

Add a langage version of the doc
**********************************

1) To generate translation files first run:

.. code-block:: bash
    
    make gettext

This will create ``.pot`` file. 

2) Then, from the ``.pot`` file, you need to create ``.po`` files with the command:

.. code-block:: bash
    
    sphinx-intl update -p _build/gettext -l fr

This will create the files in ``locale/fr/LC MESSAGES``.

3) Finally for building the translated part, run:

.. code-block:: bash
    
    sphinx-build.exe -b html -D language=fr . .\_build\html\fr