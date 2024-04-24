# lambda_github_backups

From an Amazon Web Services Lambda titled `scheduled-github-backups`, this code completes the following steps:

- Fetches a GitHub Personal Access Token from `Secrets` in order to authenticate to the GitHub Api.

- Moves into a `/tmp` directory in order to write files for brief storage.

- Calls the GitHub API and parses out the name every Cyberight repository, appends that name with a timestamp and returns all newly named files as a list for further consumption in the code. 

- Iterates over all repository zip archives and pushes them to an S3 bucket depending on the current date, creating a `Daily`, `Weekly`, and `Monthly` backup hierarchy.
