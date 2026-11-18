# Frontend: private S3 bucket behind CloudFront. HTTPS on the default *.cloudfront.net domain.
# /api/* goes to the HTTP API, so the site and the API share one origin (no CORS).

resource "aws_s3_bucket" "site" {
  bucket        = "${local.name}-site-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket                  = aws_s3_bucket.site.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "site" {
  name                              = "${local.name}-site"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

resource "aws_cloudfront_function" "spa" {
  name    = "${local.name}-spa"
  runtime = "cloudfront-js-2.0"
  comment = "Serve index.html for client-side routes"
  code    = file("${path.module}/spa-rewrite.js")
}

resource "aws_cloudfront_distribution" "site" {
  enabled             = true
  comment             = local.name
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  http_version        = "http2and3"

  origin {
    origin_id                = "site"
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.site.id
  }

  origin {
    origin_id   = "api"
    domain_name = replace(aws_apigatewayv2_api.main.api_endpoint, "https://", "")
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "site"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = data.aws_cloudfront_cache_policy.optimized.id
    compress               = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa.arn
    }
  }

  ordered_cache_behavior {
    path_pattern             = "/api/*"
    target_origin_id         = "api"
    viewer_protocol_policy   = "https-only"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_except_host.id
    compress                 = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "CloudFrontRead"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.site.arn}/*"
      Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.site.arn } }
    }]
  })
}

# Runtime config for the frontend: no rebuild needed when infra changes.
resource "aws_s3_object" "config" {
  bucket        = aws_s3_bucket.site.id
  key           = "config.json"
  content_type  = "application/json"
  cache_control = "no-cache"
  content = jsonencode({
    region     = var.region
    userPoolId = aws_cognito_user_pool.main.id
    clientId   = aws_cognito_user_pool_client.web.id
    donateUrl  = var.donate_url
  })
}

# Case files for candidates. ONLY cases/*/candidate/** is uploaded, never author/.
locals {
  candidate_files = toset([for f in fileset("${local.repo_root}/cases", "*/candidate/**") : f])
  content_types = {
    md    = "text/markdown; charset=utf-8"
    csv   = "text/csv; charset=utf-8"
    html  = "text/html; charset=utf-8"
    ipynb = "application/x-ipynb+json"
    json  = "application/json"
  }
}

resource "aws_s3_object" "case_files" {
  for_each      = local.candidate_files
  bucket        = aws_s3_bucket.site.id
  key           = "cases/${each.value}"
  source        = "${local.repo_root}/cases/${each.value}"
  etag          = filemd5("${local.repo_root}/cases/${each.value}")
  content_type  = lookup(local.content_types, reverse(split(".", each.value))[0], "application/octet-stream")
  cache_control = "max-age=300"
}

resource "aws_s3_object" "cases_index" {
  for_each      = toset(["cases.json", "professions.json"])
  bucket        = aws_s3_bucket.site.id
  key           = "cases/${each.value}"
  source        = "${local.repo_root}/cases/${each.value}"
  etag          = filemd5("${local.repo_root}/cases/${each.value}")
  content_type  = "application/json"
  cache_control = "max-age=60"
}
