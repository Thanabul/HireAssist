// Package api carries the Hiring Service's OpenAPI contract (ADR-005 rule 1). The YAML file is
// the source of truth; this package only embeds it so the service and its tests can read it.
package api

import _ "embed"

// Spec is the OpenAPI document for the Hiring Service's REST API.
//
//go:embed openapi.yaml
var Spec []byte
