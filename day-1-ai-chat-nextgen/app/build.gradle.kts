import java.io.FileInputStream
import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.hilt)
    alias(libs.plugins.ksp)
    alias(libs.plugins.detekt)
}

android {
    namespace = "com.example.day1_ai_chat_nextgen"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.day1_ai_chat_nextgen"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // Security: Only load API key in debug builds, use encrypted storage in production
        val localProperties = Properties()
        val localPropertiesFile = rootProject.file("local.properties")
        if (localPropertiesFile.exists()) {
            localProperties.load(FileInputStream(localPropertiesFile))
        }

        // Only expose API key in debug builds
        if (gradle.startParameter.taskNames.any { it.contains("debug", ignoreCase = true) }) {
            buildConfigField(
                "String",
                "OPENAI_API_KEY",
                "\"${localProperties.getProperty("openai_api_key", "")}\""
            )
        } else {
            buildConfigField("String", "OPENAI_API_KEY", "\"\"")
        }

        buildConfigField(
            "boolean",
            "IS_DEBUG_BUILD",
            "${gradle.startParameter.taskNames.any { it.contains("debug", ignoreCase = true) }}"
        )
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
            isDebuggable = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        release {
            isMinifyEnabled = true
            isDebuggable = false
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        create("analyze") {
            initWith(getByName("debug"))
            isMinifyEnabled = true
            isShrinkResources = false
            isDebuggable = false // enable full R8 optimizations
            matchingFallbacks += listOf("debug")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
                "proguard-usage.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf(
            "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
            "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api"
        )
    }

    buildFeatures {
        compose = true
        buildConfig = true
        viewBinding = false
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // Core Android
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)

    // Compose BOM
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)

    // Navigation
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.core.splashscreen)

    // Networking
    implementation(libs.retrofit)
    implementation(libs.retrofit.kotlinx.serialization)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)

    // Dependency Injection
    implementation(libs.hilt.android)
    implementation(libs.hilt.navigation.compose)
    ksp(libs.hilt.compiler)

    // ViewModel
    implementation(libs.androidx.lifecycle.viewmodel.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)

    // Coroutines
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.coroutines.android)

    // Database
    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)

    // Testing
    testImplementation(libs.junit)
    testImplementation(libs.mockito.core)
    testImplementation(libs.mockito.kotlin)
    testImplementation(libs.turbine)
    testImplementation(libs.kotest.runner)
    testImplementation(libs.kotest.assertions)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.archunit.junit4)

    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    androidTestImplementation(libs.hilt.android.testing)
    kspAndroidTest(libs.hilt.compiler)

    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}

// Allow references to generated code
ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
}

// Detekt configuration
detekt {
    buildUponDefaultConfig = true
    allRules = false
    config.setFrom("$projectDir/../detekt.yml")
    baseline = file("$projectDir/detekt-baseline.xml")
}

// Task to generate a human-readable unused code report from R8 printusage output
tasks.register("reportUnusedCode") {
    group = "verification"
    description = "Generate unused_code_report.md from R8 printusage for analyze build"
    doLast {
        val input = file("$buildDir/reports/unused/printusage-analyze.txt")
        val output = file("$projectDir/../unused_code_report.md")
        if (!input.exists()) {
            println("No printusage file found. Run :app:assembleAnalyze first.")
            return@doLast
        }
        val raw = input.readLines()
        val projectPkg = "com.example.day1_ai_chat_nextgen"

        // Keep only our package lines and drop method/member signature noise and generated code patterns
        val skipSubstrings = listOf(
            "_Factory", "_MembersInjector", "Dagger", "HiltComponents", "_Hilt",
            "hilt_aggregated_deps", "_Impl", "\$\$serializer", "\$\$inlined\$", "copy\$default",
            ":", // often class header noise
        )
        val filtered = raw.asSequence()
            .filter { it.contains(projectPkg) }
            .filter { line ->
                // remove obvious method signatures and access flags
                !line.contains("(") && !line.contains(")") &&
                !line.contains(" public ") && !line.contains(" synthetic ")
            }
            .map { it.trim().removePrefix("-").trim() }
            .filter { line -> skipSubstrings.none { sub -> line.contains(sub) } }
            .toList()

        val grouped = filtered.groupBy { line ->
            val pkg = line.substringBeforeLast('.', missingDelimiterValue = line)
            pkg.substringBeforeLast('.', missingDelimiterValue = pkg)
        }

        val builder = StringBuilder()
        builder.appendLine("# Unused Code Report (from R8 printusage)")
        builder.appendLine()
        builder.appendLine("Source: app/build/reports/unused/printusage-analyze.txt")
        builder.appendLine()
        if (filtered.isEmpty()) {
            builder.appendLine("No project classes detected as unused by R8 (after filtering generated code). ✅")
        } else {
            grouped.toSortedMap().forEach { (pkg, items) ->
                builder.appendLine("## $pkg")
                items.sorted().forEach { builder.appendLine("- $it") }
                builder.appendLine()
            }
        }
        output.writeText(builder.toString())
        println("Report written to: ${output.absolutePath}")
    }
}
