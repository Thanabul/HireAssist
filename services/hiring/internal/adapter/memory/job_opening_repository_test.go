package memory_test

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/frngrit/HireAssist/services/hiring/internal/adapter/memory"
	"github.com/frngrit/HireAssist/services/hiring/internal/domain"
	"github.com/frngrit/HireAssist/services/hiring/internal/usecase"
)

// Compile-time check: the adapter satisfies the use case's port.
var _ usecase.JobOpeningRepository = (*memory.JobOpeningRepository)(nil)

func opening(id, title string) *domain.JobOpening {
	return &domain.JobOpening{
		ID:       id,
		Title:    title,
		Criteria: []domain.Criterion{{Name: "Go", Classification: domain.MustHave, Weight: 3}},
		Status:   domain.StatusOpen,
		OpenedAt: time.Date(2026, 9, 26, 0, 0, 0, 0, time.UTC),
	}
}

func TestRepository_SaveThenFind(t *testing.T) {
	repo := memory.NewJobOpeningRepository()
	ctx := context.Background()
	_ = repo.Save(ctx, opening("jo-1", "Backend Engineer"))

	got, err := repo.FindByID(ctx, "jo-1")

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got.Title != "Backend Engineer" {
		t.Errorf("Title = %q", got.Title)
	}
}

func TestRepository_UnknownIDIsNotFound(t *testing.T) {
	_, err := memory.NewJobOpeningRepository().FindByID(context.Background(), "jo-404")

	if !errors.Is(err, usecase.ErrNotFound) {
		t.Fatalf("err = %v, want usecase.ErrNotFound", err)
	}
}

// Saving an existing id updates it in place rather than adding a second entry.
func TestRepository_ListKeepsCreationOrderAcrossUpdates(t *testing.T) {
	repo := memory.NewJobOpeningRepository()
	ctx := context.Background()
	_ = repo.Save(ctx, opening("jo-1", "Backend Engineer"))
	_ = repo.Save(ctx, opening("jo-2", "QA Engineer"))
	updated := opening("jo-1", "Senior Backend Engineer")
	_ = repo.Save(ctx, updated)

	list, _ := repo.List(ctx)

	if len(list) != 2 || list[0].Title != "Senior Backend Engineer" || list[1].Title != "QA Engineer" {
		t.Errorf("list = %+v", list)
	}
}

// Changes only reach the store through Save: neither the saved value nor a returned one
// shares memory with what is stored.
func TestRepository_StoredCopyIsIsolated(t *testing.T) {
	repo := memory.NewJobOpeningRepository()
	ctx := context.Background()
	original := opening("jo-1", "Backend Engineer")
	_ = repo.Save(ctx, original)

	original.Criteria[0].Weight = 99
	found, _ := repo.FindByID(ctx, "jo-1")
	found.Criteria[0].Name = "changed"
	found.Status = domain.StatusClosed

	again, _ := repo.FindByID(ctx, "jo-1")
	if again.Criteria[0].Weight != 3 || again.Criteria[0].Name != "Go" || again.Status != domain.StatusOpen {
		t.Errorf("stored opening was changed without Save: %+v", again)
	}
}

// Many requests at once must not corrupt the store (run with -race).
func TestRepository_ConcurrentAccess(t *testing.T) {
	repo := memory.NewJobOpeningRepository()
	ctx := context.Background()
	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			id := fmt.Sprintf("jo-%d", i)
			_ = repo.Save(ctx, opening(id, "Role"))
			_, _ = repo.FindByID(ctx, id)
			_, _ = repo.List(ctx)
		}(i)
	}
	wg.Wait()

	list, _ := repo.List(ctx)
	if len(list) != 50 {
		t.Errorf("len(list) = %d, want 50", len(list))
	}
}
