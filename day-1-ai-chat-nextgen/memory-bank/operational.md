# Operational Guidelines - AI Chat NextGen

## Build and Deployment

### Build Commands
```bash
# Clean build
./gradlew clean

# Debug build
./gradlew assembleDebug

# Release build (requires signing)
./gradlew assembleRelease

# Run tests
./gradlew test

# Run with specific API key
# Create or edit local.properties file
echo "openai_api_key=your_actual_api_key_here" >> local.properties
./gradlew assembleDebug
```

### Environment Setup
1. **API Key Configuration**
   - Create `local.properties` in project root
   - Add: `openai_api_key=your_openai_api_key_here`
   - Never commit API keys to version control

2. **Build Requirements**
   - JDK 17 or higher
   - Android SDK 35
   - Gradle 8.9+

### Release Checklist
- [ ] API key removed from debug builds
- [ ] ProGuard enabled and tested
- [ ] All tests passing
- [ ] APK size under 50MB
- [ ] No sensitive data in logs

## Monitoring and Logging

### Debug Logging
```kotlin
// Only in debug builds
if (BuildConfig.IS_DEBUG_BUILD) {
    Log.d("ChatRepo", "Sending message: ${message.content}")
}
```

### Error Tracking
- Log all `ChatError` types with context
- Track API error rates and response times
- Monitor offline/online transition behavior

### Performance Metrics
- Message send/receive latency
- Database query performance
- UI rendering performance (composition stats)
- Memory usage patterns

## Maintenance

### Regular Tasks
- **Weekly**: Update dependencies and security patches
- **Monthly**: Review API usage and costs
- **Quarterly**: Performance audit and optimization

### Database Migrations
- Room handles schema changes automatically
- Backup strategy for user data if needed
- Migration testing for schema changes

### API Rate Limit Management
- Monitor 429 errors from OpenAI
- Implement exponential backoff
- Consider request queuing for burst scenarios

## Security Operations

### API Key Rotation
1. Generate new OpenAI API key
2. Update `local.properties`
3. Test with new key
4. Revoke old key

### Security Audits
- Regular dependency vulnerability scans
- ProGuard mapping file security
- Network traffic analysis
- Local data encryption review

## Troubleshooting

### Common Issues

**Build Fails with KSP Errors**
- Ensure Kotlin and KSP versions are compatible
- Clean build and retry
- Check Hilt annotation processing

**API Calls Failing**
- Verify API key in `local.properties`
- Check network connectivity
- Review OpenAI API status
- Validate request format

**UI Not Updating**
- Check StateFlow subscriptions
- Verify immutable state usage
- Review recomposition triggers

**Tests Failing**
- Ensure coroutine test dispatcher setup
- Check mock configurations
- Verify test isolation

### Debug Mode Features
- Enhanced logging with request/response details
- Database inspection tools
- UI layout bounds and composition stats
- Network request monitoring

## Backup and Recovery

### User Data
- Room database stored in app's private directory
- Automatic Android backup if enabled
- No cloud sync implemented (future enhancement)

### Configuration
- API keys in local.properties (developer responsibility)
- Build configuration in version control
- Dependency versions locked in libs.versions.toml
