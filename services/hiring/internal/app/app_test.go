package app_test

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/frngrit/HireAssist/services/hiring/internal/app"
)

// UC-1 through the fully wired service over real HTTP: the Recruiter creates an opening,
// then opens it at the location the service returned.
func TestAssembledService_CreateThenOpen(t *testing.T) {
	srv := httptest.NewServer(app.New())
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
