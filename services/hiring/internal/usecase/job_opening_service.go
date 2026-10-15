// Package usecase holds the Hiring Service's application operations. It depends on the
// domain and on the ports declared here; adapters implement the ports and are injected.
package usecase

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/frngrit/HireAssist/services/hiring/internal/domain"
)

// ErrNotFound means no job opening exists with the requested id.
var ErrNotFound = errors.New("job opening not found")

// JobOpeningRepository stores job openings. Implemented by an adapter.
type JobOpeningRepository interface {
	Save(ctx context.Context, opening *domain.JobOpening) error
	FindByID(ctx context.Context, id string) (*domain.JobOpening, error)
	List(ctx context.Context) ([]domain.JobOpening, error)
}

// Clock tells the current time, so tests can fix it.
type Clock interface {
	Now() time.Time
}

// IDGenerator issues identifiers for new job openings.
type IDGenerator interface {
	NewID() string
}

// JobOpeningService implements the job opening operations of the Hiring Service.
type JobOpeningService struct {
	repo  JobOpeningRepository
	clock Clock
	ids   IDGenerator
}

// NewJobOpeningService wires the service to its dependencies.
func NewJobOpeningService(repo JobOpeningRepository, clock Clock, ids IDGenerator) *JobOpeningService {
	return &JobOpeningService{repo: repo, clock: clock, ids: ids}
}

// CreateJobOpening stores a Recruiter-confirmed job opening in the open state (UC-1, FR-1.7).
// It makes no AI call: the criteria arrive already confirmed, from a proposal or entered manually.
func (s *JobOpeningService) CreateJobOpening(ctx context.Context, draft domain.JobOpeningDraft) (*domain.JobOpening, error) {
	opening, err := domain.NewJobOpening(s.ids.NewID(), draft, s.clock.Now())
	if err != nil {
		return nil, err
	}
	if err := s.repo.Save(ctx, opening); err != nil {
		return nil, fmt.Errorf("saving job opening: %w", err)
	}
	return opening, nil
}

// GetJobOpening returns one job opening, or ErrNotFound.
func (s *JobOpeningService) GetJobOpening(ctx context.Context, id string) (*domain.JobOpening, error) {
	return s.repo.FindByID(ctx, id)
}

// ListJobOpenings returns every job opening in the order they were created.
func (s *JobOpeningService) ListJobOpenings(ctx context.Context) ([]domain.JobOpening, error) {
	return s.repo.List(ctx)
}

// ReviseScreeningCriteria replaces the criteria of an open or paused job opening. Resumes
// already handed to screening keep the snapshot they were sent with.
func (s *JobOpeningService) ReviseScreeningCriteria(ctx context.Context, id string, criteria []domain.Criterion) (*domain.JobOpening, error) {
	return s.update(ctx, id, func(o *domain.JobOpening) error { return o.ReviseCriteria(criteria) })
}

// PauseOpening puts an open job opening on hold (FR-1.8).
func (s *JobOpeningService) PauseOpening(ctx context.Context, id string) (*domain.JobOpening, error) {
	return s.update(ctx, id, (*domain.JobOpening).Pause)
}

// ResumeOpening reopens a paused job opening (FR-1.8).
func (s *JobOpeningService) ResumeOpening(ctx context.Context, id string) (*domain.JobOpening, error) {
	return s.update(ctx, id, (*domain.JobOpening).Resume)
}

// CloseOpening closes a job opening with a recorded outcome (FR-1.8); closing is final (FR-1.9).
func (s *JobOpeningService) CloseOpening(ctx context.Context, id string, outcome domain.Outcome) (*domain.JobOpening, error) {
	return s.update(ctx, id, func(o *domain.JobOpening) error { return o.Close(outcome) })
}

// update loads an opening, applies a domain change, and saves it only if the change was allowed.
func (s *JobOpeningService) update(ctx context.Context, id string, change func(*domain.JobOpening) error) (*domain.JobOpening, error) {
	opening, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if err := change(opening); err != nil {
		return nil, err
	}
	if err := s.repo.Save(ctx, opening); err != nil {
		return nil, fmt.Errorf("saving job opening: %w", err)
	}
	return opening, nil
}
