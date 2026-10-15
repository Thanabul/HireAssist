// Package app is the composition root: the one place that chooses concrete adapters and
// injects them into the use cases. Nothing else in the service constructs its own dependencies.
package app

import (
	"net/http"

	"github.com/frngrit/HireAssist/services/hiring/internal/adapter/httpapi"
	"github.com/frngrit/HireAssist/services/hiring/internal/adapter/memory"
	"github.com/frngrit/HireAssist/services/hiring/internal/adapter/system"
	"github.com/frngrit/HireAssist/services/hiring/internal/usecase"
)

// New assembles the Hiring Service. Storage is in memory until the PostgreSQL adapter exists;
// swapping it is a change to this function only.
func New() http.Handler {
	openings := usecase.NewJobOpeningService(
		memory.NewJobOpeningRepository(),
		system.Clock{},
		system.RandomIDs{},
	)
	return httpapi.NewHandler(openings)
}
