# Terraform skeleton — one-click path from local compose to live websites.
# HONEST STATUS: this is a reviewed-but-not-applied skeleton (gap G-5). It encodes
# the intended topology: one VM (or container host) running the same docker-compose,
# plus Cloudflare DNS + a NAMED tunnel per public hostname (the stable successor to
# the TryCloudflare quick tunnels used in dev).
#
#   terraform init && terraform apply \
#     -var cloudflare_api_token=… -var zone=aidoneright.dev
#
# Works identically with OpenTofu.

terraform {
  required_providers {
    cloudflare = { source = "cloudflare/cloudflare", version = "~> 4.0" }
    random     = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

variable "cloudflare_api_token" { type = string, sensitive = true }
variable "cloudflare_account_id" { type = string }
variable "zone" { type = string, default = "aidoneright.dev" }

# Every public surface, keyed exactly like shared/products.js — adding a hub to
# production is one entry here + SERVICE_<ID>_SECRET, mirroring the one-line
# 'private → live' flip in the prototypes.
variable "surfaces" {
  type = map(string) # key → subdomain ("" = apex)
  default = {
    parent = ""
    baltor = "baltor"
    teleon = "teleon"
    opencontexthub  = "context"
    openskillshub   = "skills"
    opentoolshub    = "tools"
    openskilltotool = "skilltotool"
    openmcphub      = "mcp"
    opencompressionhub = "compression"
    openbenchmarkhub   = "benchmarks"
    openreviewhub      = "reviews"
    openharnesshub     = "harness"
  }
}

provider "cloudflare" { api_token = var.cloudflare_api_token }

# --- service-account secrets, generated once and injected into the host's .env ---
resource "random_password" "service_secret" {
  for_each = var.surfaces
  length   = 48
  special  = false
}
resource "random_password" "core_jwt_secret" { length = 64, special = false }

# --- one named tunnel for the platform host ---
resource "cloudflare_tunnel" "platform" {
  account_id = var.cloudflare_account_id
  name       = "aidoneright-platform"
  secret     = random_password.core_jwt_secret.result # placeholder; rotate properly
}

# --- DNS: every surface CNAMEs to the tunnel ---
data "cloudflare_zone" "main" { name = var.zone }

resource "cloudflare_record" "surface" {
  for_each = var.surfaces
  zone_id  = data.cloudflare_zone.main.id
  name     = each.value == "" ? "@" : each.value
  type     = "CNAME"
  content  = "${cloudflare_tunnel.platform.id}.cfargotunnel.com"
  proxied  = true
}

# --- tunnel ingress: hostname → the same Caddy that dev runs ---
resource "cloudflare_tunnel_config" "platform" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_tunnel.platform.id
  config {
    dynamic "ingress_rule" {
      for_each = var.surfaces
      content {
        hostname = each.value == "" ? var.zone : "${each.value}.${var.zone}"
        service  = "http://localhost:8080" # Caddy from docker-compose, same as dev
      }
    }
    ingress_rule { service = "http_status:404" }
  }
}

# --- emit the host .env so compose and Terraform agree on secrets ---
resource "local_file" "host_env" {
  filename = "${path.module}/generated.env"
  content  = join("\n", concat(
    ["CORE_JWT_SECRET=${random_password.core_jwt_secret.result}"],
    [for k, v in var.surfaces : "SERVICE_${upper(k)}_SECRET=${random_password.service_secret[k].result}"]
  ))
}

output "tunnel_token_hint" {
  value = "Run on the host: cloudflared tunnel run --token <token from Cloudflare dashboard for '${cloudflare_tunnel.platform.name}'>"
}

# TODO (next infra pass): host provisioning module (DigitalOcean droplet / AWS Lightsail /
# Hetzner) that cloud-inits docker + this repo + `docker compose up -d`; remote state;
# per-surface health checks; Postgres instead of the JSON file via a DATABASE_URL var.
