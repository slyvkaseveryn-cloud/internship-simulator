# ADR 0002: Only pay-per-use services

- Status: accepted · Date: 2026-11-15

**Context.** The account runs on promotional credits; the goal is $0 charged to the card.

**Decision.** S3 + CloudFront (default `*.cloudfront.net` HTTPS), Cognito (Lite tier), API Gateway HTTP API,
Lambda (Python, arm64), DynamoDB on-demand. No always-on servers. A budget alerts on actual or forecast spend
above $1 **after credits**. All resources tagged `project=internship-simulator`.

**Alternatives.** RDS/Aurora (always-on or slow cold start, not in free tier); EC2/containers (always-on).

**Consequences.** Single-table DynamoDB means queries are designed per access pattern. Cognito's own email
sender allows 50 emails a day: enough for a prototype, SES needed beyond that.
