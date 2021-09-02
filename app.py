#!/usr/bin/env python3
"""The main app. Contains all the stacks."""

# Standard library imports
# -

# Related third party imports
# -

# Local application/library specific imports
from aws_cdk import core as cdk
from config import Config
from cache_control_with_cloudfront_functions.cache_control_with_cloudfront_functions_stack import (
    CacheControlWithCloudfrontFunctionsStack,
)

config = Config()

app = cdk.App()
CacheControlWithCloudfrontFunctionsStack(
    scope=app,
    construct_id="CacheControlWithCloudfrontFunctionsStack",
    config=config.base(),
)

app.synth()
