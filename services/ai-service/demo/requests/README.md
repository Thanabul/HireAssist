# Example requests

Ready to paste into Postman's gRPC message body, grpcui, or `grpcurl -d @`. One file per
operation, named for the RPC it calls.

Field names are the protobuf JSON mapping — `candidateId`, `mustHave`, `workHistory`. The
original `snake_case` from the `.proto` is accepted too; Postman generates camelCase, so these
match what its "Generate example message" button produces.

These are **synthetic**. Never put a real resume in this folder — see the root `CLAUDE.md`.
