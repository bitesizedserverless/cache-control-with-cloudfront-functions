"""Module for the main CacheControlWithCloudfrontFunctions Stack."""

# Standard library imports
import os

# Related third party imports
# -

# Local application/library specific imports
from aws_cdk import (
    aws_cloudfront as cfr,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    core as cdk,
)


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

        # Create an Origin Access Identity
        oai = cfr.CfnCloudFrontOriginAccessIdentity(
            scope=self,
            id="FrontendOAI",
            cloud_front_origin_access_identity_config={"comment": "FrontendOAI"},
        )

        # Create a bucket to store some images
        assets_bucket = s3.Bucket(
            scope=self,
            id="AssetsBucket",
            public_read_access=False,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Create a bucket to store some images
        s3_deploy.BucketDeployment(
            scope=self,
            id="AssetsBucketFiles",
            sources=[s3_deploy.Source.asset("./bucket_assets")],
            destination_bucket=assets_bucket,
        )

        # Update the bucket policy to allow read access to the OAI
        assets_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                ],
                effect=iam.Effect.ALLOW,
                resources=[assets_bucket.arn_for_objects("*")],
                principals=[iam.CanonicalUserPrincipal(oai.attr_s3_canonical_user_id)],
            )
        )

        # Create a policy that retains images for a year
        one_year_in_seconds = 60 * 60 * 24 * 365  # 31 536 000
        cache_policy_one_year = cfr.CfnCachePolicy(
            scope=self,
            id="CachePolicyOneYear",
            cache_policy_config=cfr.CfnCachePolicy.CachePolicyConfigProperty(
                default_ttl=one_year_in_seconds,
                max_ttl=one_year_in_seconds,
                min_ttl=one_year_in_seconds,
                name="CachePolicyOneYear",
                parameters_in_cache_key_and_forwarded_to_origin=cfr.CfnCachePolicy.ParametersInCacheKeyAndForwardedToOriginProperty(  # noqa: E501 pylint: disable=line-too-long
                    cookies_config=cfr.CfnCachePolicy.CookiesConfigProperty(
                        cookie_behavior="none"
                    ),
                    enable_accept_encoding_gzip=True,
                    enable_accept_encoding_brotli=True,
                    headers_config=cfr.CfnCachePolicy.HeadersConfigProperty(
                        header_behavior="none"
                    ),
                    query_strings_config=cfr.CfnCachePolicy.QueryStringsConfigProperty(
                        query_string_behavior="whitelist",
                        query_strings=["v", "h"],  # v for version, h for hash
                    ),
                ),
            ),
        )

        # Load the CloudFront Functions from their files
        current_path = os.path.dirname(os.path.abspath(__file__))
        with open(
            file=f"{current_path}/../cloudfront_functions/viewer_request.js",
            encoding="utf-8",
        ) as viewer_request_code:
            viewer_request_function_code = viewer_request_code.read()
        with open(
            file=f"{current_path}/../cloudfront_functions/viewer_response.js",
            encoding="utf-8",
        ) as viewer_response_code:
            viewer_response_function_code = viewer_response_code.read()

        # Create an Index HTML CloudFront Function with the code defined above
        viewer_request_function = cfr.CfnFunction(
            scope=self,
            id="FrontendIndexFunction",
            name="index-function",
            auto_publish=True,
            function_code=viewer_request_function_code,
            function_config=cfr.CfnFunction.FunctionConfigProperty(
                comment="Reject requests for images without a version",
                runtime="cloudfront-js-1.0",
            ),
        )

        # Create an Caching CloudFront Function with the code defined above
        viewer_response_function = cfr.CfnFunction(
            scope=self,
            id="CachingHeadersFunction",
            name="caching-headers-function",
            auto_publish=True,
            function_code=viewer_response_function_code,
            function_config=cfr.CfnFunction.FunctionConfigProperty(
                comment="Add caching headers to image responses",
                runtime="cloudfront-js-1.0",
            ),
        )

        image_cloudfront_functions = [
            cfr.CfnDistribution.FunctionAssociationProperty(
                event_type="viewer-request",
                function_arn=viewer_request_function.attr_function_arn,
            ),
            cfr.CfnDistribution.FunctionAssociationProperty(
                event_type="viewer-response",
                function_arn=viewer_response_function.attr_function_arn,
            ),
        ]

        # ID for the "caching_disabled" managed policy, see
        # https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-cache-policies.html
        managed_policy_caching_disabled = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"

        # Create the CloudFront distribution
        cfr.CfnDistribution(
            scope=self,
            id="CloudFrontDistribution",
            distribution_config=cfr.CfnDistribution.DistributionConfigProperty(
                enabled=True,
                http_version="http2",
                default_root_object="index.html",
                origins=[
                    cfr.CfnDistribution.OriginProperty(
                        id="s3bucketorigin",
                        domain_name=assets_bucket.bucket_regional_domain_name,
                        s3_origin_config=cfr.CfnDistribution.S3OriginConfigProperty(
                            origin_access_identity=cdk.Fn.join(
                                delimiter="",
                                list_of_values=[
                                    "origin-access-identity/cloudfront/",
                                    oai.ref,
                                ],
                            )
                        ),
                    )
                ],
                default_cache_behavior=cfr.CfnDistribution.DefaultCacheBehaviorProperty(
                    target_origin_id="s3bucketorigin",
                    viewer_protocol_policy="redirect-to-https",
                    cache_policy_id=managed_policy_caching_disabled,
                    compress=True,
                    function_associations=[
                        cfr.CfnDistribution.FunctionAssociationProperty(
                            event_type="viewer-response",
                            function_arn=viewer_response_function.attr_function_arn,
                        )
                    ],
                ),
                cache_behaviors=[
                    cfr.CfnDistribution.CacheBehaviorProperty(
                        path_pattern="*.png",
                        target_origin_id="s3bucketorigin",
                        viewer_protocol_policy="redirect-to-https",
                        cache_policy_id=cache_policy_one_year.ref,
                        function_associations=image_cloudfront_functions,
                        compress=True,
                    ),
                    cfr.CfnDistribution.CacheBehaviorProperty(
                        path_pattern="*.jpg",
                        target_origin_id="s3bucketorigin",
                        viewer_protocol_policy="redirect-to-https",
                        cache_policy_id=cache_policy_one_year.ref,
                        function_associations=image_cloudfront_functions,
                        compress=True,
                    ),
                ],
            ),
        )
