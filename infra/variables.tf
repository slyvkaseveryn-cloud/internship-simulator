variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "donate_url" {
  description = "Charity collection behind «Підтримати волонтерів». Chosen by Severyn; empty shows a placeholder."
  type        = string
  default     = ""

  validation {
    condition     = var.donate_url == "" || startswith(var.donate_url, "https://")
    error_message = "donate_url must be empty or an https:// link."
  }
}
