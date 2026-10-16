# Builds the Hiring Service into a small static image (ADR-005 rule 4).
FROM golang:1.25-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /hiring ./cmd/hiring

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /hiring /hiring
EXPOSE 8080
ENTRYPOINT ["/hiring"]
