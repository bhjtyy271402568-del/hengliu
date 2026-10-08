"""Execute the actual Debug ELF on an emulated Cortex-M (no board connection).

Run: python tests/test_laser_safety.py [path/to/hengliu.elf]
Requires unicorn and pyelftools; local test-only installs in tmp are supported.
GPIO set/reset side effects are modeled, and ADC HAL calls return injected
samples/status. TIM6 startup is skipped and its callback is invoked explicitly
once per simulated millisecond. These tests do not validate analog voltages,
ADC calibration/conversion hardware, RCC startup or real interrupt scheduling.
"""

import struct
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tmp/firmware_safety_test_vendor"))
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
    UC_ARM_REG_PRIMASK, UC_ARM_REG_XPSR,
)

ELF_PATH = Path(sys.argv.pop(1)) if len(sys.argv) > 1 else ROOT / "build/Debug/hengliu.elf"
GPIOA, GPIOB, GPIOC = 0x48000000, 0x48000400, 0x48000800
DAC = 0x50000800
RCC_AHB2ENR = 0x4002104C
RETURN = 0x20007000
TEST_DAC = int(re.search(r"#define TEST_DAC_VALUE (\d+)U", (ROOT / "Core/Src/main.c").read_text()).group(1))
START_MS = (TEST_DAC + 49) // 50 + 100


class Firmware:
    def __init__(self):
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        for address, size in ((0x08000000, 0x20000), (0x20000000, 0x8000),
                              (0x40000000, 0x30000), (GPIOA, 0x2000),
                              (0x50000000, 0x2000), (0xE000E000, 0x2000)):
            self.cpu.mem_map(address, size)
        with ELF_PATH.open("rb") as stream:
            elf = ELFFile(stream)
            self.symbols = {s.name: s["st_value"] for s in elf.get_section_by_name(".symtab").iter_symbols()}
            self.sizes = {s.name: s["st_size"] for s in elf.get_section_by_name(".symtab").iter_symbols()}
            for segment in elf.iter_segments():
                if segment["p_type"] == "PT_LOAD" and segment["p_filesz"]:
                    self.cpu.mem_write(segment["p_vaddr"], segment.data())
        self.writes = []
        self.start_masks = []
        self.adc_raw = 0
        self.adc_failure = None
        self.cpu.hook_add(UC_HOOK_MEM_WRITE, self._write_hook)
        self.cpu.hook_add(UC_HOOK_CODE, self._code_hook)
        self.write(self.symbols["hdac1"], DAC)
        self.write(self.symbols["htim6"], 0x40001000)
        self.write(RCC_AHB2ENR, 0x10007)
        self.write(GPIOB + 0x10, 1 << 12)  # STOP inactive
        self.key(False)

    def write(self, address, value):
        self.cpu.mem_write(address, struct.pack("<I", value))

    def read(self, address):
        return struct.unpack("<I", self.cpu.mem_read(address, 4))[0]

    def state(self):
        return int.from_bytes(self.cpu.mem_read(self.symbols["g_laser_state"], self.sizes["g_laser_state"]), "little")

    def key(self, pressed):
        self.write(GPIOC + 0x10, 0 if pressed else 1 << 9)

    def _write_hook(self, cpu, access, address, size, value, user):
        self.writes.append((address, value))
        for port in (GPIOA, GPIOB, GPIOC):
            if address == port + 0x18:  # BSRR
                self.write(port + 0x14, (self.read(port + 0x14) | (value & 0xFFFF)) & ~(value >> 16))
            elif address == port + 0x28:  # BRR
                self.write(port + 0x14, self.read(port + 0x14) & ~value)

    def _code_hook(self, cpu, address, size, user):
        # Only ADC peripheral behavior is stubbed; LED logic runs from the ELF.
        for name in ("HAL_ADC_Start", "HAL_ADC_PollForConversion", "HAL_ADC_GetValue", "HAL_ADC_Stop"):
            if address == (self.symbols.get(name, 0) & ~1):
                result = self.adc_raw if name == "HAL_ADC_GetValue" else int(self.adc_failure == name)
                cpu.reg_write(UC_ARM_REG_R0, result)
                cpu.reg_write(UC_ARM_REG_PC, cpu.reg_read(UC_ARM_REG_LR))
                return
        if address == (self.symbols["Laser_TIM6_Start_1ms"] & ~1):
            cpu.reg_write(UC_ARM_REG_PC, cpu.reg_read(UC_ARM_REG_LR))
        if address == (self.symbols["Laser_Start"] & ~1):
            self.start_masks.append(cpu.reg_read(UC_ARM_REG_PRIMASK))

    def call(self, name, arg=0, terminal=False):
        self.cpu.reg_write(UC_ARM_REG_SP, 0x20007FF8)
        self.cpu.reg_write(UC_ARM_REG_LR, RETURN | 1)
        self.cpu.reg_write(UC_ARM_REG_R0, arg)
        self.cpu.reg_write(UC_ARM_REG_XPSR, 1 << 24)
        self.cpu.emu_start(self.symbols[name] | 1, RETURN, count=20000)
        if not terminal:
            assert self.cpu.reg_read(UC_ARM_REG_PC) == RETURN, name + " did not return"

    def tick(self, count=1, adc=False):
        for _ in range(count):
            self.write(self.symbols["uwTick"], (self.read(self.symbols["uwTick"]) + 1) & 0xFFFFFFFF)
            if adc:
                self.call("Laser_Process_Current_Sample")
            self.call("HAL_TIM_PeriodElapsedCallback", self.symbols["htim6"])

    def green(self):
        return bool(self.read(GPIOC + 0x14) & (1 << 13))

    def init(self):
        self.call("Laser_Hardware_Init")

    def press(self):
        self.key(True)
        self.tick(20)
        self.call("Laser_Process_Key1_Requests")

    def off(self):
        return not (self.read(GPIOA + 0x14) & (1 << 9)) and self.read(DAC + 8) == 0


class LaserSafetyTests(unittest.TestCase):
    def setUp(self):
        self.fw = Firmware()
        self.fw.init()

    def test_idle_and_shoot_disabled(self):
        self.assertEqual(self.fw.state(), 0)
        self.assertTrue(self.fw.off())
        self.assertEqual(self.fw.cpu.mem_read(self.fw.symbols["g_laser_shoot_enabled"], 1), b"\0")

    def test_held_at_boot_requires_release(self):
        f = self.fw
        f.key(True)
        f.init()
        f.tick(30)
        f.call("Laser_Process_Key1_Requests")
        self.assertTrue(f.off())
        f.key(False)
        f.tick()
        f.press()
        self.assertEqual(f.state(), 1)

    def test_debounce_ramp_and_manual_duration(self):
        f = self.fw
        f.key(True)
        f.tick(19)
        f.call("Laser_Process_Key1_Requests")
        self.assertTrue(f.off())
        f.tick()
        f.call("Laser_Process_Key1_Requests")
        self.assertEqual(f.state(), 1)
        f.tick()
        self.assertEqual(f.read(DAC + 8), 50)
        f.tick(15)
        self.assertEqual(f.read(DAC + 8), min(800, TEST_DAC))
        f.tick(2100)
        self.assertEqual(f.state(), 2)
        self.assertEqual(f.read(DAC + 8), TEST_DAC)
        self.assertFalse(f.off())

    def test_release_before_request_consumed(self):
        f = self.fw
        f.key(True)
        f.tick(20)
        f.key(False)  # release after debounce, before the next TIM6 sample
        f.call("Laser_Process_Key1_Requests")
        self.assertTrue(f.off(), "stale button request enabled output after release")
        self.assertEqual(f.state(), 0)

    def test_sampled_release_cancels_pending_start(self):
        f = self.fw
        f.key(True)
        f.tick(20)
        f.key(False)
        f.tick()
        f.call("Laser_Process_Key1_Requests")
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)

    def test_start_commit_keeps_interrupts_masked(self):
        self.fw.press()
        self.assertEqual(self.fw.start_masks, [1])
        self.assertEqual(self.fw.cpu.reg_read(UC_ARM_REG_PRIMASK), 0)

    def test_preserves_existing_interrupt_mask(self):
        self.fw.cpu.reg_write(UC_ARM_REG_PRIMASK, 1)
        self.fw.call("Laser_Process_Key1_Requests")
        self.assertEqual(self.fw.cpu.reg_read(UC_ARM_REG_PRIMASK), 1)

    def test_release_during_ramp_without_main_loop(self):
        f = self.fw
        f.press()
        f.tick(5)
        f.key(False)
        f.tick()  # deliberately no main-loop request processing
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)
        f.tick(30)
        self.assertTrue(f.off())

    def test_release_running_without_main_loop_and_restart(self):
        f = self.fw
        f.press()
        f.tick(START_MS)
        self.assertEqual(f.state(), 2)
        f.key(False)
        f.tick()
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)
        f.press()
        self.assertEqual(f.state(), 1)

    def test_fault_lockout_is_preserved(self):
        f = self.fw
        f.press()
        f.tick(START_MS)
        f.write(GPIOB + 0x10, 0)
        f.call("HAL_GPIO_EXTI_Callback", 1 << 12)
        f.tick(5)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())
        f.key(False)
        f.tick()
        f.press()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_all_fatal_handlers_turn_output_off(self):
        for handler in ("Error_Handler", "HardFault_Handler", "NMI_Handler",
                        "MemManage_Handler", "BusFault_Handler", "UsageFault_Handler"):
            with self.subTest(handler=handler):
                f = Firmware()
                f.init()
                f.press()
                f.tick(16)
                f.write(GPIOC + 0x14, 1 << 13)
                f.writes.clear()
                f.call(handler, terminal=True)
                self.assertTrue(f.off())
                self.assertFalse(f.green())
                self.assertEqual(f.cpu.reg_read(UC_ARM_REG_PRIMASK), 1)
                pwm = next(i for i, (a, v) in enumerate(f.writes) if a == GPIOA + 0x28 and v == 1 << 9)
                dac = next(i for i, (a, v) in enumerate(f.writes) if a == DAC + 8 and v == 0)
                self.assertLess(pwm, dac)

    def test_fatal_before_peripheral_clocks(self):
        f = self.fw
        f.write(RCC_AHB2ENR, 0)
        f.writes.clear()
        f.call("HardFault_Handler", terminal=True)
        self.assertFalse(any(a in (GPIOA + 0x28, DAC + 8) for a, _ in f.writes))
        self.assertEqual(f.cpu.reg_read(UC_ARM_REG_PRIMASK), 1)

    def test_no_feedback_never_gives_steady_green(self):
        f = self.fw
        f.press()
        f.tick(START_MS + 200)
        self.assertEqual(f.state(), 2)
        self.assertFalse(f.green())

    def test_idle_zero_target_and_startup_cannot_qualify(self):
        f = self.fw
        f.adc_raw = round(TEST_DAC * 82 / 273)
        f.tick(110, adc=True)
        self.assertFalse(f.green())
        f.press()
        f.tick(START_MS - 1, adc=True)
        self.assertEqual(f.state(), 1)
        self.assertFalse(f.green())
        f.key(False)
        f.tick()
        f.call("Laser_Start", 0)
        f.adc_raw = 0
        f.tick(250, adc=True)
        self.assertFalse(f.green())

    def test_restart_requires_new_qualification(self):
        f = self.fw
        f.press()
        f.tick(START_MS)
        f.adc_raw = round(TEST_DAC * 82 / 273)
        f.tick(100, adc=True)
        self.assertTrue(f.green())
        f.key(False)
        f.tick()
        f.press()
        f.tick(START_MS)
        f.tick(99, adc=True)
        self.assertFalse(f.green())
        f.tick(adc=True)
        self.assertTrue(f.green())

    def test_sampling_recovers_across_systick_wrap(self):
        f = self.fw
        f.press()
        f.tick(START_MS)
        f.write(f.symbols["uwTick"], 0xFFFFFFF0)
        f.adc_raw = round(TEST_DAC * 82 / 273)
        f.tick(100, adc=True)
        self.assertTrue(f.green())

    def test_current_requires_100_ms_and_resets_on_low_sample(self):
        f = self.fw
        f.press()
        f.tick(START_MS)
        f.adc_raw = round(TEST_DAC * 82 / 273)
        f.tick(99, adc=True)
        self.assertFalse(f.green())
        f.tick(adc=True)
        self.assertTrue(f.green())
        f.adc_raw = 0
        f.tick(adc=True)
        self.assertFalse(f.green())
        f.adc_raw = round(TEST_DAC * 82 / 273)
        f.tick(99, adc=True)
        self.assertFalse(f.green())
        f.tick(adc=True)
        self.assertTrue(f.green())
        f.key(False)
        f.tick()
        self.assertTrue(f.off())
        self.assertFalse(f.green())

    def test_target_tracks_dac_and_twenty_percent_boundaries(self):
        for dac in (400, 800, 900, 1600, 4095):
            lower = (dac * 82 * 80 + 27300 - 1) // 27300
            upper = dac * 82 * 120 // 27300
            for raw, expected in ((0, False), (lower - 1, False), (lower, True),
                                  (upper, True), (upper + 1, False), (4095, False)):
                with self.subTest(dac=dac, raw=raw):
                    f = Firmware()
                    f.init()
                    f.call("Laser_Start", dac)
                    f.tick((dac + 49) // 50 + 100)
                    f.adc_raw = raw
                    f.tick(100, adc=True)
                    self.assertEqual(f.green(), expected)
                    self.assertEqual(f.read(DAC + 8), dac, "LED logic must not compensate DAC")

    def test_eleven_percent_low_current_qualifies_after_100_ms(self):
        f = self.fw
        f.press()
        f.tick(START_MS)
        f.adc_raw = round(TEST_DAC * 82 / 273 * 0.89)
        f.tick(99, adc=True)
        self.assertFalse(f.green())
        f.tick(adc=True)
        self.assertTrue(f.green())
        self.assertEqual(f.read(DAC + 8), TEST_DAC)

    def test_stale_or_failed_adc_turns_green_off(self):
        for failure in (None, "HAL_ADC_Start", "HAL_ADC_PollForConversion", "HAL_ADC_Stop"):
            with self.subTest(failure=failure):
                f = Firmware()
                f.init()
                f.press()
                f.tick(START_MS)
                f.adc_raw = round(TEST_DAC * 82 / 273)
                f.tick(100, adc=True)
                self.assertTrue(f.green())
                f.adc_failure = failure
                f.tick(5, adc=failure is not None)
                self.assertFalse(f.green())
                self.assertEqual(f.state(), 2)

    def test_fault_blink_survives_current_monitor(self):
        f = self.fw
        f.press()
        f.tick(START_MS)
        f.adc_raw = round(TEST_DAC * 82 / 273)
        f.tick(100, adc=True)
        f.write(GPIOB + 0x10, 0)
        f.call("HAL_GPIO_EXTI_Callback", 1 << 12)
        f.tick(adc=True)
        self.assertFalse(f.green(), "pending fault must cancel steady green")
        f.tick(4, adc=True)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())
        self.assertTrue(f.green())
        f.tick(250, adc=True)
        self.assertFalse(f.green())
        f.tick(250, adc=True)
        self.assertTrue(f.green())


if __name__ == "__main__":
    print("Testing:", ELF_PATH)
    unittest.main(verbosity=2)
