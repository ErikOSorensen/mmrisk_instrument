# mmrisk_instrument
Code to run experiment for "Risk taking on behalf of others: Does the timing of uncertainty revelation matter?" by Alexander W. Cappelen, Erik Ø. Sørensen, Bertil Tungodden and Xiaogeng Xu.

This code runs as a Django project. The files distributed here are configured to run
as a local project with the development server. For proper production run, more infrastructure
is needed.

- A proper database. The experiment was run in the summer of 2019 with Postgres.
- A webserver. The experiment was run in the summer of 2019 with Apache.
 
## Extracting information

In the `extracting_information` directory, there are two files. These are run after the
online survey part to do 1) extract the feedback to be sent to participants by text
message by the service provder, 2) extract data for analysis purposes, and 3) extract
the information to be provided to the mTurk recipients.

These functions and scripts must be evaluated in the Django environment of the experiment.

- `extract_data.py` : 
  - The `feedback_file` function extracts the text message feedback to be provided to survey participants (`feedback_mmr2.csv`). 
  - The `get_data` function extracts three files with data for analysis purposes:
    - `players.csv`: Running id of participants, treatment, status (whether they completed or not) and a time stamp for when the participant registered.
    - `decisions.csv`: For each individual, and each decision, which die they faced, what the safe amount was, and whether they chose to take risk. Also a timestamp.
    - `answers.csv`: One row for each of the participant and each non-incentivized question, and what the response was. 
- `extract_payments.py`: A script that connects to the database and generates the mTurk-payments (and messages) to be provided to the recipients, written to `payments_mmrisk.csv`.
