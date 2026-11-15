# Sign-up and sign-in: a Cognito user pool. The site talks to Cognito directly
# (SignUp / ConfirmSignUp / InitiateAuth), so all screens stay in Ukrainian.

resource "aws_cognito_user_pool" "main" {
  name                     = local.name
  user_pool_tier           = "LITE"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  deletion_protection      = "INACTIVE"

  password_policy {
    minimum_length                   = 8
    require_lowercase                = false
    require_uppercase                = false
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  # Cognito's own sender: free, up to 50 emails a day. Enough for a prototype.
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Код підтвердження: Симулятор стажувань"
    email_message        = "Твій код підтвердження: {####}"
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    mutable             = true
    required            = false
    string_attribute_constraints {
      min_length = 0
      max_length = 100
    }
  }
}

resource "aws_cognito_user_pool_client" "web" {
  name                          = "${local.name}-web"
  user_pool_id                  = aws_cognito_user_pool.main.id
  generate_secret               = false
  explicit_auth_flows           = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  prevent_user_existence_errors = "ENABLED"
  id_token_validity             = 60
  access_token_validity         = 60
  refresh_token_validity        = 30
  token_validity_units {
    id_token      = "minutes"
    access_token  = "minutes"
    refresh_token = "days"
  }
  read_attributes  = ["email", "email_verified", "name"]
  write_attributes = ["email", "name"]
}

resource "aws_cognito_user_group" "reviewers" {
  name         = "reviewers"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Team members who write reviews and see metrics"
}
