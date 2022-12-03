import tempfile
import time
from fastapi import HTTPException
from pydantic import BaseModel
import requests
import boto3
import os
import requests.exceptions as reqexc
from typing import Any

from server.tango import TangoInterface


COURSE_LAB = "awap"
MAKEFILE = "bots/autograde-Makefile"


class UserSubmission(BaseModel):
    username: str
    s3_bucket_name: str
    s3_object_name: str


class Match(BaseModel):
    game_engine_name: str
    num_players: int
    user_submissions: list[UserSubmission]


class MatchCallback(BaseModel):
    team_name_1: str
    team_name_2: str
    game_replay: list[Any]


class MatchRunner:
    match: Match
    tango: TangoInterface

    files_param: list

    def __init__(
        self,
        match: Match,
        match_runner_config: dict,
        tango: TangoInterface,
        s3_resource,
    ):
        self.match = match
        self.s3 = s3_resource
        self.match_id = time.time_ns()

        self.files_param = [
            match_runner_config.get("makefile"),
            match_runner_config.get("engine"),
        ]

        self.tango = tango
        self.fastapi_host = match_runner_config["fastapi_host"]

    def uploadFile(self, pathname: str) -> dict[str, str]:
        filename = pathname.split("/")[-1]
        with_id = f"{self.match_id}-{filename}"
        return self.tango.upload_file(pathname, with_id, filename)

    def sendJob(self):
        """
        Send the job to the match runner by calling Tango API
        You would likely need to download the user submissions from the remote location
        and then send it together with the game engine to the match runner

        You will likely need the requests library to call the Tango API
        Tango API https://docs.autolabproject.com/tango-rest/
        """
        with tempfile.TemporaryDirectory() as tempdir:
            for i, submission in enumerate(self.match.user_submissions):
                local_path = os.path.join(tempdir, f"team{i+1}.py")
                self.s3.download_file(
                    submission.s3_bucket_name, submission.s3_object_name, local_path
                )
                self.files_param.append(self.uploadFile(local_path))

        callback_url = f"{self.fastapi_host}/single_match_callback/{self.match_id}"
        output_file = f"output-{self.match_id}.json"
        print(output_file)

        return self.tango.add_job(
            self.match_id,
            self.files_param,
            output_file,
            callback_url,
        )
