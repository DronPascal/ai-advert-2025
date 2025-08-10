# Constraints - AI Chat NextGen

## Technical Constraints

### Android Version Support
- **Minimum SDK**: 24 (Android 7.0)
- **Target SDK**: 35 (Android 15)
- **Compile SDK**: 35

### Language and Framework
- **Language**: Kotlin 2.1.10 (matches Android Architecture Samples)
- **UI Framework**: Jetpack Compose with Material 3
- **Architecture**: Clean Architecture mandatory
- **Dependency Injection**: Hilt only
- **Annotation Processing**: KSP (not KAPT) for performance

### Performance Constraints
- **App Size**: Target <50MB APK size
- **Memory**: Efficient RecyclerView with LazyColumn
- **Network**: Handle offline scenarios gracefully
- **Database**: Room with max 10MB local storage

## Security Constraints

### API Key Management
- **Development**: API keys in local.properties only
- **Production**: No API keys in APK (use secure backend)
- **Logging**: No sensitive data in production logs

### Data Protection
- **Local Storage**: Encrypt sensitive data if needed
- **Network**: HTTPS only, no cleartext traffic
- **ProGuard**: Mandatory obfuscation for release builds

## Business Constraints

### OpenAI API Limits
- **Rate Limits**: Handle 429 errors gracefully
- **Token Limits**: Max 150 tokens per request
- **Model**: GPT-3.5-turbo only (cost optimization)
- **Context**: Limited conversation history (last 6 messages)

### User Experience
- **Response Time**: <3 seconds for API responses
- **Offline Mode**: View cached messages when offline
- **Error Handling**: User-friendly error messages
- **Accessibility**: Basic accessibility support required

## Development Constraints

### Code Quality
- **Testing**: Minimum 80% unit test coverage for domain layer
- **Documentation**: All public APIs must be documented
- **Code Style**: Follow Kotlin coding conventions
- **Git**: English commit messages mandatory

### Build and Deployment
- **Build Tool**: Gradle with KSP (no KAPT)
- **CI/CD**: Ready for automated testing
- **Variants**: Debug and Release build types
- **Signing**: Release signing configuration required

## External Dependencies

### Required Libraries
- AndroidX Core, Lifecycle, Compose BOM
- Hilt 2.53.1 for dependency injection (verified compatibility with Kotlin 2.1.10)
- KSP 2.1.10-1.0.30 for annotation processing (matches Kotlin version)
- Room 2.6.1 for local database
- Retrofit for networking
- Kotlinx Serialization for JSON parsing

### Testing Libraries
- Kotest for BDD-style unit tests
- Mockito for mocking dependencies
- Turbine for Flow testing
- Coroutines Test for async testing

### Prohibited Dependencies
- ❌ Dagger (use Hilt instead)
- ❌ Gson (use Kotlinx Serialization)
- ❌ RxJava (use Coroutines/Flow)
- ❌ Legacy support libraries
