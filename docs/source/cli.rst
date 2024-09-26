CLI Usage
=========

The ``nrk-psapi`` library includes a command-line interface (CLI) script to interact with the API. Below are examples of how to use the CLI script.


Browse Podcasts
---------------

To browse podcasts by a specific letter:

.. code-block:: bash

    poetry run nrk browse A


Get Podcast
-----------

To get details of a specific podcast:

.. code-block:: bash

    poetry run nrk podcast <podcast_id>

To get episodes of a specific podcast:

.. code-block:: bash

    poetry run nrk podcast <podcast_id> --episodes


Get Episode
-----------

To get details of a specific episode:

.. code-block:: bash

    poetry run nrk episode <podcast_id> <episode_id>

To get metadata of a specific episode:

.. code-block:: bash

    poetry run nrk episode <podcast_id> <episode_id> --metadata


Build RSS Feed
--------------

To build a RSS feed for a specific podcast:

.. code-block:: bash

    poetry run nrk rss <podcast_id> <output_path>


Search
------

To search for podcasts or other content:

.. code-block:: bash

    poetry run nrk search <query>
