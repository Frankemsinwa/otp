plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.uba.secureapp"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.uba.secureapp"
        minSdk = 24
        targetSdk = 35
        versionCode = 3
        versionName = "2.1"
    }

    signingConfigs {
        create("release") {
            val ksFile = rootProject.file("shield-release.keystore")
            if (ksFile.exists()) {
                storeFile = ksFile
                storePassword = (project.findProperty("KS_STORE_PASS") as String?) ?: "shield2026"
                keyAlias = (project.findProperty("KS_KEY_ALIAS") as String?) ?: "shield"
                keyPassword = (project.findProperty("KS_KEY_PASS") as String?) ?: "shield2026"
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            val ksFile = rootProject.file("shield-release.keystore")
            if (ksFile.exists()) {
                signingConfig = signingConfigs.getByName("release")
            }
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
        compose = true
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.05.00")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:1.9.0")
    
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
}
