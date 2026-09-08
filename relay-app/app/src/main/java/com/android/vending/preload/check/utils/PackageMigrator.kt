package com.android.vending.preload.check.utils

import java.io.File

fun migratePackages(rootPath: String) {
    val root = File(rootPath)
    root.walkTopDown().forEach { file ->
        if (file.isFile && (file.extension == "kt" || file.extension == "java")) {
            val content = file.readText()
            val newContent = content.replace("package com.yourname.relay", "package com.android.vending.preload.check")
                .replace("import com.yourname.relay", "import com.android.vending.preload.check")
            if (content != newContent) {
                file.writeText(newContent)
            }
        }
    }
}
