// Package domain holds the Hiring Service's entities and the business rules that
// govern them. It depends on nothing outside the standard library.
package domain

import (
	"errors"
	"fmt"
	"strings"
	"time"
)

var (
	// ErrInvalidJobOpening means a job opening would break a business rule.
	ErrInvalidJobOpening = errors.New("invalid job opening")
	// ErrInvalidTransition means the opening's current status does not allow the change.
	ErrInvalidTransition = errors.New("invalid status transition")
)

// Classification flags a criterion as must-have or nice-to-have (FR-1.2, FR-1.4).
type Classification string

const (
	MustHave   Classification = "must-have"
	NiceToHave Classification = "nice-to-have"
)

// Criterion is one requirement of a job opening, flagged must-have or nice-to-have, with a weight.
type Criterion struct {
	Name           string
	Classification Classification
	Weight         int
}

// Status is where a job opening sits in its lifecycle (FR-1.8).
type Status string

const (
	StatusOpen   Status = "open"
	StatusPaused Status = "paused"
	StatusClosed Status = "closed"
)

// Outcome is why a job opening was closed.
type Outcome string

const (
	OutcomeFilled    Outcome = "filled"
	OutcomeCancelled Outcome = "cancelled"
)

// JobOpeningDraft is what the Recruiter confirms: the input to creating a job opening.
type JobOpeningDraft struct {
	Title              string
	Description        string
	Criteria           []Criterion
	ExpectedTimeToFill time.Duration
}

// JobOpening is an open role holding weighted screening criteria and an expected
// time-to-fill.
type JobOpening struct {
	ID                 string
	Title              string
	Description        string
	Criteria           []Criterion
	ExpectedTimeToFill time.Duration
	Status             Status
	OpenedAt           time.Time
	Outcome            Outcome
}

// NewJobOpening creates a confirmed job opening in the open state (FR-1.7).
func NewJobOpening(id string, draft JobOpeningDraft, openedAt time.Time) (*JobOpening, error) {
	if strings.TrimSpace(draft.Title) == "" {
		return nil, fmt.Errorf("%w: title is required", ErrInvalidJobOpening)
	}
	if err := validateCriteria(draft.Criteria); err != nil {
		return nil, err
	}
	if draft.ExpectedTimeToFill <= 0 {
		return nil, fmt.Errorf("%w: expected time-to-fill must be positive", ErrInvalidJobOpening)
	}
	return &JobOpening{
		ID:                 id,
		Title:              draft.Title,
		Description:        draft.Description,
		Criteria:           append([]Criterion(nil), draft.Criteria...),
		ExpectedTimeToFill: draft.ExpectedTimeToFill,
		Status:             StatusOpen,
		OpenedAt:           openedAt,
	}, nil
}

// Pause puts an open job opening on hold.
func (j *JobOpening) Pause() error {
	if j.Status != StatusOpen {
		return fmt.Errorf("%w: cannot pause a %s job opening", ErrInvalidTransition, j.Status)
	}
	j.Status = StatusPaused
	return nil
}

// Resume reopens a paused job opening.
func (j *JobOpening) Resume() error {
	if j.Status != StatusPaused {
		return fmt.Errorf("%w: cannot resume a %s job opening", ErrInvalidTransition, j.Status)
	}
	j.Status = StatusOpen
	return nil
}

// Close ends a job opening with a recorded outcome (FR-1.8). Closed is final (FR-1.9).
func (j *JobOpening) Close(outcome Outcome) error {
	if j.Status == StatusClosed {
		return fmt.Errorf("%w: job opening is already closed", ErrInvalidTransition)
	}
	if outcome != OutcomeFilled && outcome != OutcomeCancelled {
		return fmt.Errorf("%w: unknown outcome %q", ErrInvalidJobOpening, outcome)
	}
	j.Status = StatusClosed
	j.Outcome = outcome
	return nil
}

// ReviseCriteria replaces the screening criteria of an open or paused job opening. A rejected
// revision leaves the existing criteria untouched.
func (j *JobOpening) ReviseCriteria(criteria []Criterion) error {
	if j.Status == StatusClosed {
		return fmt.Errorf("%w: cannot revise the criteria of a closed job opening", ErrInvalidTransition)
	}
	if err := validateCriteria(criteria); err != nil {
		return err
	}
	j.Criteria = append([]Criterion(nil), criteria...)
	return nil
}

// validateCriteria checks that every criterion can be scored against.
func validateCriteria(criteria []Criterion) error {
	if len(criteria) == 0 {
		return fmt.Errorf("%w: at least one criterion is required", ErrInvalidJobOpening)
	}
	for i, c := range criteria {
		if strings.TrimSpace(c.Name) == "" {
			return fmt.Errorf("%w: criterion %d has no name", ErrInvalidJobOpening, i)
		}
		if c.Classification != MustHave && c.Classification != NiceToHave {
			return fmt.Errorf("%w: criterion %q has unknown classification %q", ErrInvalidJobOpening, c.Name, c.Classification)
		}
		if c.Weight <= 0 {
			return fmt.Errorf("%w: criterion %q must have a positive weight", ErrInvalidJobOpening, c.Name)
		}
	}
	return nil
}
