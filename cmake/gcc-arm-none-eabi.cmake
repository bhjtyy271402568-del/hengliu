set(CMAKE_SYSTEM_NAME               Generic)
set(CMAKE_SYSTEM_PROCESSOR          arm)

set(CMAKE_C_COMPILER_ID GNU)
set(CMAKE_CXX_COMPILER_ID GNU)
set(CMAKE_ASM_COMPILER_ID GNU)
set(CMAKE_C_COMPILER_ID_RUN TRUE)
set(CMAKE_ASM_COMPILER_ID_RUN TRUE)
set(CMAKE_C_COMPILER_VERSION 14.3.1)
set(CMAKE_C_ABI_COMPILED TRUE)
set(CMAKE_C_COMPILER_ABI ELF)
set(CMAKE_C_SIZEOF_DATA_PTR 4)
set(CMAKE_C_BYTE_ORDER LITTLE_ENDIAN)

# Keep the whole build on the STM32 VS Code bundle toolchain.
# Relying on PATH can accidentally pick another Arm GCC installation.
set(TOOLCHAIN_BIN_DIR               "C:/Users/Administrator/AppData/Local/stm32cube/bundles/gnu-tools-for-stm32/14.3.1+st.2/bin")
set(TOOLCHAIN_PREFIX                "${TOOLCHAIN_BIN_DIR}/arm-none-eabi-")

set(CMAKE_C_COMPILER                "${TOOLCHAIN_PREFIX}gcc.exe")
set(CMAKE_ASM_COMPILER              "${CMAKE_C_COMPILER}")
set(CMAKE_CXX_COMPILER              "${TOOLCHAIN_PREFIX}g++.exe")
set(CMAKE_LINKER                    "${TOOLCHAIN_PREFIX}gcc.exe")
set(CMAKE_AR                        "${TOOLCHAIN_PREFIX}ar.exe")
set(CMAKE_RANLIB                    "${TOOLCHAIN_PREFIX}ranlib.exe")
set(CMAKE_STRIP                     "${TOOLCHAIN_PREFIX}strip.exe")
set(CMAKE_OBJCOPY                   "${TOOLCHAIN_PREFIX}objcopy.exe")
set(CMAKE_SIZE                      "${TOOLCHAIN_PREFIX}size.exe")

set(CMAKE_C_COMPILER_WORKS          TRUE)
set(CMAKE_ASM_COMPILER_WORKS        TRUE)
set(CMAKE_C_COMPILER_FORCED         TRUE)
set(CMAKE_ASM_COMPILER_FORCED       TRUE)

set(CMAKE_EXECUTABLE_SUFFIX_ASM     ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_C       ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_CXX     ".elf")

set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# MCU specific flags
set(TARGET_FLAGS "-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard ")
set(SPECS_FLAGS "--specs=nano.specs --specs=nosys.specs")

set(CMAKE_C_FLAGS "${TARGET_FLAGS} -Wall -fdata-sections -ffunction-sections")
set(CMAKE_ASM_FLAGS "${TARGET_FLAGS} -x assembler-with-cpp -MMD -MP")

set(CMAKE_C_FLAGS_DEBUG "-O0 -g3")
set(CMAKE_C_FLAGS_RELEASE "-Os -g0")
set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g3")
set(CMAKE_CXX_FLAGS_RELEASE "-Os -g0")

set(CMAKE_CXX_FLAGS "${CMAKE_C_FLAGS} -fno-rtti -fno-exceptions -fno-threadsafe-statics")

set(CMAKE_EXE_LINKER_FLAGS "${TARGET_FLAGS}")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -T \"${CMAKE_SOURCE_DIR}/STM32G431XX_FLASH.ld\"")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${SPECS_FLAGS}")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-Map=${CMAKE_PROJECT_NAME}.map -Wl,--gc-sections")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,--print-memory-usage")
set(TOOLCHAIN_LINK_LIBRARIES "m")
