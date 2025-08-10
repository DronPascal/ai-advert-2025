# Operational Notes

## Build & Run
- Build: `./gradlew :day-1-ai-chat:build`
- Install debug: `./gradlew :day-1-ai-chat:installDebug`

## OpenAI API Key (production)
- Do not commit keys. Store in `local.properties` only:

```properties
openai_api_key=sk-proj-<your-key>
```

- Rebuild after changes: `./gradlew clean build`

## Networking
- HTTPS only, certificate validation enabled by OkHttp by default.
- Set reasonable timeouts in `RetrofitClient` if not already.

## Testing
- Unit tests: add coverage for `ChatViewModel`.
- Acceptance tests: basic chat flow in demo mode.


