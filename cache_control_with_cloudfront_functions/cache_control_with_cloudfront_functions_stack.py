"""Module for the main CacheControlWithCloudfrontFunctions Stack."""

# Standard library imports
# -

# Related third party imports
# -

# Local application/library specific imports
from aws_cdk import core as cdk


class CacheControlWithCloudfrontFunctionsStack(cdk.Stack):
    """The CacheControlWithCloudfrontFunctions Stack."""

    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        config: dict,  # pylint: disable=unused-argument
        **kwargs,
    ) -> None:
        """Construct a new CacheControlWithCloudfrontFunctionsStack."""
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
