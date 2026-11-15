# ADR 0001: Terraform with state in S3

- Status: accepted · Date: 2026-11-15

**Context.** The author's previous AWS project used Terraform (`hashicorp/aws ~> 6.0`) with state in HCP
Terraform and OIDC from CI, and it worked. Teammates must deploy without the owner's AWS keys.

**Decision.** Terraform in `infra/`. State in a versioned, private S3 bucket with native locking
(`use_lockfile`), created by `infra/bootstrap/`. CI assumes an IAM role through GitHub OIDC; the role's trust
policy only accepts workflows on `main`.

**Alternatives.** HCP Terraform: every teammate would need another account. AWS CDK: a second tool and a
bootstrap stack, with no gain for this size.

**Consequences.** Bootstrap (budget, state bucket, CI role) is applied once by the account owner. Pull requests
run `terraform validate`, not `plan` (no AWS access from PRs).
