#!/usr/bin/env python3

import boto3
import requests
import json
import re
import datetime
import shutil
import os


def get_auth_token():

    secret_name = "secret"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    jtoken = get_secret_value_response["SecretString"]
    token = json.loads(jtoken)
    return token["github_service_pat"]


def get_repo_names(token):
    # Get repo names and return as a list.
    os.chdir("/tmp")
    auth = f"token {token}"
    owner = "Optm-Main"
    repos_url = f"https://api.github.com/orgs/{owner}/repos"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": auth,
    }

    session = requests.Session()
    current_page = session.get(repos_url, headers=headers)
    repo_names = []
    first_run = True

    while True:
        sj = json.dumps(current_page.json())
        names = json.loads(sj)

        for i in names:
            repo_names.append(i["name"])

        try: 
            current_page.links["next"]["url"]
            next_page_url = current_page.links["next"]["url"]
            current_page = session.get(next_page_url, headers=headers)
        except:
            break
        first_run = False
    return repo_names


def get_repo_archives_to_s3(token):
    # S3 vars
    s3_client = boto3.client("s3")
    bucket = "cyberight-github-backups"
    year = datetime.datetime.now().strftime("%Y")
    month = datetime.datetime.now().strftime("%B")
    day_of_month = datetime.datetime.now().strftime("%d")
    day_of_week = datetime.datetime.now().strftime("%A")

    # Determines the numeric week of the year; 1-52
    week_of_year = datetime.datetime.today()
    week = week_of_year.isocalendar()[1]

    daily_upload_path = f"Daily/{year}/{month}/"
    monthly_upload_path = f"Monthly/{year}/"
    weekly_upload_path = f"Weekly/{year}/"

    repo_names = get_repo_names(token)
    auth = f"token {token}"
    owner = "Optm-Main"
    repos_url = f"https://api.github.com/orgs/{owner}/repos?per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": auth,
    }

    # Get the zip archives
    for repo in repo_names:
        a = requests.get(
            f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
            stream=True,
            headers=headers,
        )
        date = datetime.date.today()
        with open(f"{repo}-{date}.zip", "wb") as f:
            shutil.copyfileobj(a.raw, f)

        # if day is first of month add to month dir
        s3_client.upload_file(
            f"{repo}-{date}.zip", bucket, f"{daily_upload_path}{repo}-{date}.zip"
        )

        if day_of_month == "1":
            s3_client.upload_file(
                f"{repo}-{date}.zip", bucket, f"{monthly_upload_path}{repo}-{date}.zip"
            )

        if day_of_week == "Sunday":
            s3_client.upload_file(
                f"{repo}-{date}.zip", bucket, f"{weekly_upload_path}{repo}-{date}.zip"
            )

def lambda_handler(event, context):
    token = get_auth_token()
    get_repo_archives_to_s3(token)

