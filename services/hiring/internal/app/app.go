// Package app is the composition root: the one place that chooses concrete adapters and
// injects them into the use cases. Nothing else in the service constructs its own dependencies.
package app

import (
	"context"
	"fmt"
	"net/http"

	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/frngrit/HireAssist/services/hiring/internal/adapter/httpapi"
	"github.com/frngrit/HireAssist/services/hiring/internal/adapter/memory"
	"github.com/frngrit/HireAssist/services/hiring/internal/adapter/postgres"
	"github.com/frngrit/HireAssist/services/hiring/internal/adapter/system"
	"github.com/frngrit/HireAssist/services/hiring/internal/usecase"
)

// Config is the service's startup configuration, read from the environment by main.
type Config struct {
	// DatabaseURL selects PostgreSQL (ADR-003). Empty means in-memory storage, lost on restart —
	// for tests and quick local runs only.
	DatabaseURL string
}

// New assembles the Hiring Service. With a database it connects, verifies the connection and
// applies the schema before returning, so a bad database fails startup rather than the first
// request. The returned func releases what New acquired.
func New(ctx context.Context, cfg Config) (http.Handler, func(), error) {
	var (
		repo    usecase.JobOpeningRepository = memory.NewJobOpeningRepository()
		release                              = func() {}
	)
	if cfg.DatabaseURL != "" {
		pool, err := pgxpool.New(ctx, cfg.DatabaseURL)
		if err != nil {
			return nil, nil, fmt.Errorf("configuring database: %w", err)
		}
		if err := pool.Ping(ctx); err != nil {
			pool.Close()
			return nil, nil, fmt.Errorf("connecting to database: %w", err)
		}
		if err := postgres.Migrate(ctx, pool); err != nil {
			pool.Close()
			return nil, nil, err
		}
		repo, release = postgres.NewJobOpeningRepository(pool), pool.Close
	}

	openings := usecase.NewJobOpeningService(repo, system.Clock{}, system.RandomIDs{})
	return httpapi.NewHandler(openings), release, nil
}
