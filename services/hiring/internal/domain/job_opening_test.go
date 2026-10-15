package domain_test

import (
	"errors"
	"testing"
	"time"

	"github.com/frngrit/HireAssist/services/hiring/internal/domain"
)

var openedAt = time.Date(2026, 9, 24, 9, 0, 0, 0, time.UTC)

func validCriteria() []domain.Criterion {
	return []domain.Criterion{
		{Name: "3+ years of Go", Classification: domain.MustHave, Weight: 5},
		{Name: "Kubernetes experience", Classification: domain.NiceToHave, Weight: 2},
	}
}

func validDraft() domain.JobOpeningDraft {
	return domain.JobOpeningDraft{
		Title:              "Backend Engineer",
		Description:        "We need a backend engineer who writes Go and knows Kubernetes.",
		Criteria:           validCriteria(),
		ExpectedTimeToFill: 30 * 24 * time.Hour,
	}
}

// FR-1.7: a confirmed job opening is stored in the open state, recording the date it
// was opened and retaining the original free-text description.
func TestNewJobOpening_IsOpenWithOpeningDateAndOriginalDescription(t *testing.T) {
	draft := validDraft()

	opening, err := domain.NewJobOpening("jo-1", draft, openedAt)

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if opening.ID != "jo-1" {
		t.Errorf("ID = %q, want %q", opening.ID, "jo-1")
	}
	if opening.Status != domain.StatusOpen {
		t.Errorf("Status = %q, want %q", opening.Status, domain.StatusOpen)
	}
	if !opening.OpenedAt.Equal(openedAt) {
		t.Errorf("OpenedAt = %v, want %v", opening.OpenedAt, openedAt)
	}
	if opening.Description != draft.Description {
		t.Errorf("Description = %q, want the original %q", opening.Description, draft.Description)
	}
	if len(opening.Criteria) != 2 {
		t.Errorf("len(Criteria) = %d, want 2", len(opening.Criteria))
	}
	// FR-1.6: expected time-to-fill is recorded.
	if opening.ExpectedTimeToFill != draft.ExpectedTimeToFill {
		t.Errorf("ExpectedTimeToFill = %v, want %v", opening.ExpectedTimeToFill, draft.ExpectedTimeToFill)
	}
}

// A job opening must be screenable: without a title, criteria it can be scored against,
// and an expected time-to-fill (which UC-4 uses to detect stale positions), it is rejected.
func TestNewJobOpening_RejectsUnscreenableDrafts(t *testing.T) {
	tests := []struct {
		name   string
		mutate func(d *domain.JobOpeningDraft)
	}{
		{"blank title", func(d *domain.JobOpeningDraft) { d.Title = "   " }},
		{"no criteria", func(d *domain.JobOpeningDraft) { d.Criteria = nil }},
		{"criterion without a name", func(d *domain.JobOpeningDraft) { d.Criteria[0].Name = "" }},
		{"unknown classification", func(d *domain.JobOpeningDraft) { d.Criteria[0].Classification = "optional" }},
		{"zero weight", func(d *domain.JobOpeningDraft) { d.Criteria[0].Weight = 0 }},
		{"negative weight", func(d *domain.JobOpeningDraft) { d.Criteria[1].Weight = -1 }},
		{"no expected time-to-fill", func(d *domain.JobOpeningDraft) { d.ExpectedTimeToFill = 0 }},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			draft := validDraft()
			tt.mutate(&draft)

			_, err := domain.NewJobOpening("jo-1", draft, openedAt)

			if !errors.Is(err, domain.ErrInvalidJobOpening) {
				t.Fatalf("err = %v, want ErrInvalidJobOpening", err)
			}
		})
	}
}

func openOpening(t *testing.T) *domain.JobOpening {
	t.Helper()
	opening, err := domain.NewJobOpening("jo-1", validDraft(), openedAt)
	if err != nil {
		t.Fatalf("setup: %v", err)
	}
	return opening
}

// FR-1.8: a Recruiter can pause an open job opening and resume it again.
func TestJobOpening_PauseAndResume(t *testing.T) {
	opening := openOpening(t)

	if err := opening.Pause(); err != nil {
		t.Fatalf("Pause: unexpected error: %v", err)
	}
	if opening.Status != domain.StatusPaused {
		t.Fatalf("after Pause, Status = %q, want %q", opening.Status, domain.StatusPaused)
	}

	if err := opening.Resume(); err != nil {
		t.Fatalf("Resume: unexpected error: %v", err)
	}
	if opening.Status != domain.StatusOpen {
		t.Fatalf("after Resume, Status = %q, want %q", opening.Status, domain.StatusOpen)
	}
}

// Only an open opening can be paused, and only a paused one resumed.
func TestJobOpening_RejectsPauseOrResumeFromWrongState(t *testing.T) {
	opening := openOpening(t)
	if err := opening.Resume(); !errors.Is(err, domain.ErrInvalidTransition) {
		t.Errorf("Resume while open: err = %v, want ErrInvalidTransition", err)
	}

	_ = opening.Pause()
	if err := opening.Pause(); !errors.Is(err, domain.ErrInvalidTransition) {
		t.Errorf("Pause while paused: err = %v, want ErrInvalidTransition", err)
	}
}

// FR-1.8: an opening is closed with a recorded outcome of filled or cancelled,
// whether it was open or paused at the time.
func TestJobOpening_CloseRecordsOutcome(t *testing.T) {
	tests := []struct {
		name    string
		paused  bool
		outcome domain.Outcome
	}{
		{"open, filled", false, domain.OutcomeFilled},
		{"open, cancelled", false, domain.OutcomeCancelled},
		{"paused, filled", true, domain.OutcomeFilled},
		{"paused, cancelled", true, domain.OutcomeCancelled},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			opening := openOpening(t)
			if tt.paused {
				_ = opening.Pause()
			}

			if err := opening.Close(tt.outcome); err != nil {
				t.Fatalf("Close: unexpected error: %v", err)
			}
			if opening.Status != domain.StatusClosed {
				t.Errorf("Status = %q, want %q", opening.Status, domain.StatusClosed)
			}
			if opening.Outcome != tt.outcome {
				t.Errorf("Outcome = %q, want %q", opening.Outcome, tt.outcome)
			}
		})
	}
}

// The outcome must be one of the two the business recognises.
func TestJobOpening_CloseRejectsUnknownOutcome(t *testing.T) {
	opening := openOpening(t)

	err := opening.Close("abandoned")

	if !errors.Is(err, domain.ErrInvalidJobOpening) {
		t.Fatalf("err = %v, want ErrInvalidJobOpening", err)
	}
	if opening.Status != domain.StatusOpen {
		t.Errorf("Status = %q, want it unchanged at %q", opening.Status, domain.StatusOpen)
	}
}

// Closed is final: the recorded outcome feeds UC-4's metrics and cannot be reopened or rewritten.
func TestJobOpening_ClosedIsFinal(t *testing.T) {
	opening := openOpening(t)
	_ = opening.Close(domain.OutcomeFilled)

	if err := opening.Pause(); !errors.Is(err, domain.ErrInvalidTransition) {
		t.Errorf("Pause after close: err = %v, want ErrInvalidTransition", err)
	}
	if err := opening.Resume(); !errors.Is(err, domain.ErrInvalidTransition) {
		t.Errorf("Resume after close: err = %v, want ErrInvalidTransition", err)
	}
	if err := opening.Close(domain.OutcomeCancelled); !errors.Is(err, domain.ErrInvalidTransition) {
		t.Errorf("Close after close: err = %v, want ErrInvalidTransition", err)
	}
	if opening.Outcome != domain.OutcomeFilled {
		t.Errorf("Outcome = %q, want the original %q", opening.Outcome, domain.OutcomeFilled)
	}
}

// reviseScreeningCriteria(): the Recruiter can correct the criteria after creation, while the
// opening is open or paused. Batches already running are unaffected — each resume carries a
// snapshot of the criteria it was scored against (NFR-15).
func TestJobOpening_ReviseCriteriaReplacesTheSet(t *testing.T) {
	revised := []domain.Criterion{
		{Name: "Shipped with Kafka or RabbitMQ", Classification: domain.MustHave, Weight: 4},
	}
	for _, paused := range []bool{false, true} {
		opening := openOpening(t)
		if paused {
			_ = opening.Pause()
		}

		if err := opening.ReviseCriteria(revised); err != nil {
			t.Fatalf("paused=%v: unexpected error: %v", paused, err)
		}
		if len(opening.Criteria) != 1 || opening.Criteria[0] != revised[0] {
			t.Errorf("paused=%v: Criteria = %+v, want %+v", paused, opening.Criteria, revised)
		}
	}
}

// Revised criteria obey the same rules as at creation; a rejected revision changes nothing.
func TestJobOpening_ReviseCriteriaRejectsInvalidSet(t *testing.T) {
	opening := openOpening(t)

	err := opening.ReviseCriteria([]domain.Criterion{{Name: "Go", Classification: domain.MustHave, Weight: 0}})

	if !errors.Is(err, domain.ErrInvalidJobOpening) {
		t.Fatalf("err = %v, want ErrInvalidJobOpening", err)
	}
	if len(opening.Criteria) != len(validCriteria()) {
		t.Errorf("Criteria changed on a rejected revision: %+v", opening.Criteria)
	}
}

// FR-1.9: a closed opening is final, including its criteria.
func TestJobOpening_ReviseCriteriaRejectedWhenClosed(t *testing.T) {
	opening := openOpening(t)
	_ = opening.Close(domain.OutcomeCancelled)

	err := opening.ReviseCriteria(validCriteria())

	if !errors.Is(err, domain.ErrInvalidTransition) {
		t.Fatalf("err = %v, want ErrInvalidTransition", err)
	}
}

// The opening keeps its own copy: the caller mutating its slice afterwards changes nothing.
func TestJobOpening_ReviseCriteriaCopiesTheInput(t *testing.T) {
	opening := openOpening(t)
	revised := validCriteria()

	_ = opening.ReviseCriteria(revised)
	revised[0].Weight = 99

	if opening.Criteria[0].Weight == 99 {
		t.Error("opening shares the caller's slice")
	}
}
