# ADR-0004: Hilt + KSP + Kotlin 2.1+ Compatibility Resolution

## Status
Accepted

## Context
During development, we encountered critical compatibility issues between Hilt, KSP, and Kotlin 2.1+:

- **Error**: `java.lang.String com.squareup.javapoet.ClassName.canonicalName()`
- **Root Cause**: Incomplete plugin configuration and version mismatches
- **Impact**: Hilt code generation completely failed, preventing app compilation

## Investigation
The error was traced to two main issues:
1. **Missing plugin declarations** in root build.gradle.kts
2. **Version incompatibilities** between Kotlin, KSP, and Hilt

## Decision
Adopt the exact configuration pattern from Android Architecture Samples:

### 1. Complete Plugin Declaration (Critical)
**Root build.gradle.kts must declare ALL plugins:**
```kotlin
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.hilt) apply false          // CRITICAL!
    alias(libs.plugins.ksp) apply false           // CRITICAL!
}
```

### 2. Proven Compatible Versions
```toml
[versions]
kotlin = "2.1.10"
ksp = "2.1.10-1.0.30"
hilt = "2.53.1"
room = "2.6.1"
```

### 3. KSP2 Configuration
```properties
# gradle.properties
# Disable KSP2 for stability (as in Android samples)
# ksp.useKSP2=true
```

## Consequences

### Positive
- **Build Success**: 100% compilation success rate
- **Code Generation**: All Hilt classes generate correctly
- **Stability**: Matches proven Android Architecture Samples configuration
- **Performance**: KSP significantly faster than KAPT

### Negative
- **Version Lock-in**: Must maintain exact version compatibility
- **Complexity**: Requires understanding of plugin interaction patterns

## Lessons Learned

### Critical Requirements
1. **Plugin Declaration Pattern**: ALL plugins must be declared in root build.gradle.kts, even if only used in modules
2. **Version Alignment**: Kotlin and KSP versions must match exactly (first two numbers)
3. **Hilt Compatibility**: Use tested combinations from official Android samples
4. **Plugin Order**: Apply plugins in correct sequence (Android → Kotlin → Hilt → KSP)

### Debugging Approach
1. **Check Plugin Declaration**: Verify ALL plugins in root build.gradle.kts
2. **Version Matrix**: Ensure Kotlin ↔ KSP ↔ Hilt compatibility
3. **Reference Samples**: Compare with working Android Architecture Samples
4. **Clean Builds**: Always clean between major configuration changes

## Verification
- ✅ Build success: `./gradlew clean assembleDebug`
- ✅ Hilt generation: Files present in `build/generated/ksp/debug/`
- ✅ App installation: No runtime crashes
- ✅ DI functionality: @AndroidEntryPoint and @HiltViewModel work correctly

## References
- [Android Architecture Samples](https://github.com/android/architecture-samples)
- [KSP Migration Guide](https://developer.android.com/build/migrate-to-ksp)
- [Hilt Documentation](https://dagger.dev/hilt/)
