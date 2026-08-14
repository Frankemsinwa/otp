plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "com.yourname.relay"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.yourname.relay"
        minSdk = 24          // Android 7.0 — covers ~98% of active devices
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        // Build-time injection of the relay secret into BuildConfig
        // Override on the command line: ./gradlew assembleRelease -PRELAY_SECRET=abc...
        val relaySecret: String = (project.findProperty("RELAY_SECRET") as String?) ?: ""
        buildConfigField("String", "RELAY_SECRET", "\"$relaySecret\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
            // In debug builds, fall back to a placeholder secret if none supplied
            val relaySecret: String = (project.findProperty("RELAY_SECRET") as String?) ?: "DEBUG_SECRET_CHANGE_ME"
            buildConfigField("String", "RELAY_SECRET", "\"$relaySecret\"")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        buildConfig = true
    }

    // Room annotation processor (Phase 4 — offline SMS buffer)
    ksp {
        arg("room.schemaLocation", "$projectDir/schemas")
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.localbroadcastmanager:localbroadcastmanager:1.1.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")

    // WorkManager — periodic drain of the offline buffer
    implementation("androidx.work:work-runtime-ktx:2.9.1")

    // Room — local SQLite queue so failed-relay SMS survive offline gaps
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")
}
