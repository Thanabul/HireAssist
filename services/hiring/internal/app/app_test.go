package app_test

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"

	"github.com/frngrit/HireAssist/services/hiring/internal/app"
)

// UC-1 through the fully wired service over real HTTP: the Recruiter creates an opening,
// then opens it at the location the service returned.
// It runs in memory, and again against PostgreSQL when HIRING_TEST_DATABASE_URL is set.
func TestAssembledService_CreateThenOpen(t *testing.T) {
	configs := map[string]app.Config{"memory": {}}
	if url := os.Getenv("HIRING_TEST_DATABASE_URL"); url != "" {
		configs["postgres"] = app.Config{DatabaseURL: url}
	}
	for name, cfg := range configs {
		t.Run(name, func(t *testing.T) { createThenOpen(t, cfg) })
	}
}

func createThenOpen(t *testing.T, cfg app.Config) {
	handler, closeService, err := app.New(context.Background(), cfg)
	if err != nil {
		t.Fatalf("app.New: %v", err)
	}
	defer closeService()
	srv := httptest.NewServer(handler)
	defer srv.Close()

	created, err := http.Post(srv.URL+"/job-openings", "application/json", strings.NewReader(`{
		"title": "Backend Engineer",
		"description": "Backend engineer, 3+ years of Go.",
		"criteria": [{"name": "3+ years of Go", "classification": "must-have", "weight": 5}],
		"expected_time_to_fill_days": 30
	}`))
	if err != nil {
		t.Fatal(err)
	}
	defer created.Body.Close()
	if created.StatusCode != http.StatusCreated {
		t.Fatalf("create status = %d", created.StatusCode)
	}
	location := created.Header.Get("Location")
	if !strings.HasPrefix(location, "/job-openings/jo_") {
		t.Fatalf("Location = %q, want a generated jo_ id", location)
	}

	fetched, err := http.Get(srv.URL + location)
	if err != nil {
		t.Fatal(err)
	}
	defer fetched.Body.Close()
	var body struct {
		Title  string `json:"title"`
		Status string `json:"status"`
	}
	_ = json.NewDecoder(fetched.Body).Decode(&body)
	if fetched.StatusCode != http.StatusOK || body.Title != "Backend Engineer" || body.Status != "open" {
		t.Errorf("GET %s = %d %+v", location, fetched.StatusCode, body)
	}
}

// A database that cannot be reached fails startup instead of failing the first request.
func TestNew_UnreachableDatabaseFailsStartup(t *testing.T) {
	_, _, err := app.New(context.Background(), app.Config{
		DatabaseURL: "postgres://nobody:wrong@127.0.0.1:1/none?sslmode=disable&connect_timeout=1",
	})

	if err == nil {
		t.Fatal("app.New succeeded against an unreachable database")
	}
}
