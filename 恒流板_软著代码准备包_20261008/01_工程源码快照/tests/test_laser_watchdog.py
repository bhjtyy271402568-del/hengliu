"""Exercise IWDG feed policy, FAULT polling and CSS against the compiled ELF.

Usage: python -B tests/test_laser_watchdog.py 0|1|2 path/to/hengliu.elf
Reuses the safety emulator without running its mode-0 test suite. Peripheral
register writes and explicit callback execution verify software behavior only;
LSI timing, IWDG reset, physical clock failure and interrupt timing are not
simulated. All three build modes must be tested with their corresponding ELF.
"""

import sys
import unittest

if len(sys.argv) < 3 or sys.argv[1] not in ("0", "1", "2"):
    raise SystemExit("Usage: test_laser_watchdog.py 0|1|2 path/to/hengliu.elf")
MODE = int(sys.argv.pop(1))

import test_laser_safety as safety

IWDG_KR = 0x40003000
EXTI_IMR1 = 0x40010400
RCC_CIFR, RCC_CICR = 0x4002101C, 0x40021020
STOP = 1 << 12
CSS = 1 << 8


class Firmware(safety.Firmware):
    def __init__(self):
        self.css_entries = []
        self.drop_on_reenable = False
        self.progress_on_refresh = False
        self.stop_at = None
        super().__init__()
        self.write(self.symbols["hiwdg"], IWDG_KR)

    def value(self, name):
        return int.from_bytes(self.cpu.mem_read(self.symbols[name], self.sizes[name]), "little")

    def fault(self, active):
        self.write(safety.GPIOB + 0x10, 0 if active else STOP)

    def refresh_count(self):
        return sum(a == IWDG_KR and v == 0xAAAA for a, v in self.writes)

    def watchdog(self):
        self.call("Laser_Process_Watchdog")

    def _code_hook(self, cpu, address, size, user):
        super()._code_hook(cpu, address, size, user)
        if self.stop_at and address == (self.symbols[self.stop_at] & ~1):
            cpu.emu_stop()
        if self.drop_on_reenable and address == (self.symbols["Laser_Enable_Stop_EXTI"] & ~1):
            self.drop_on_reenable = False
            self.fault(True)
        if self.progress_on_refresh and address == (self.symbols["HAL_IWDG_Refresh"] & ~1):
            self.progress_on_refresh = False
            # Model a completed TIM6 interrupt after the main-loop snapshot.
            self.write(self.symbols["g_tim6_completed"], (self.value("g_tim6_completed") + 1) & 0xFFFFFFFF)
        for name in ("HAL_RCC_NMI_IRQHandler", "HAL_RCC_CSSCallback"):
            if address == (self.symbols[name] & ~1):
                self.css_entries.append((name, self.off(), len(self.writes)))


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.f = Firmware()
        self.f.init()

    def test_no_tim6_progress_cannot_feed(self):
        for _ in range(10):
            self.f.watchdog()
        self.assertEqual(self.f.refresh_count(), 0)

    def test_each_new_progress_allows_only_one_feed(self):
        f = self.f
        for expected in range(1, 4):
            f.tick()
            f.watchdog()
            f.watchdog()
            self.assertEqual(f.refresh_count(), expected)

    def test_accumulated_ticks_cannot_bank_feeds(self):
        f = self.f
        f.tick(30)
        for _ in range(30):
            f.watchdog()
        self.assertEqual(f.refresh_count(), 1)

    def test_tim6_without_main_loop_never_feeds(self):
        self.f.tick(1000)
        self.assertEqual(self.f.value("g_tim6_completed"), 1000)
        self.assertEqual(self.f.refresh_count(), 0)

    def test_other_timer_is_not_progress(self):
        f = self.f
        f.write(f.symbols["htim6"], 0x40000000)  # TIM2 instance in this handle
        f.call("HAL_TIM_PeriodElapsedCallback", f.symbols["htim6"])
        f.watchdog()
        self.assertEqual(f.value("g_tim6_completed"), 0)
        self.assertEqual(f.refresh_count(), 0)

    def test_incomplete_tim6_task_cannot_feed(self):
        f = self.f
        f.stop_at = "Laser_Process_Fault_LED"
        f.call("HAL_TIM_PeriodElapsedCallback", f.symbols["htim6"], terminal=True)
        self.assertEqual(f.value("g_tim6_completed"), 0)
        f.stop_at = None
        f.watchdog()
        self.assertEqual(f.refresh_count(), 0)

    def test_counter_wrap_is_new_progress(self):
        f = self.f
        for name in ("g_tim6_completed", "g_watchdog_last_completed"):
            f.write(f.symbols[name], 0xFFFFFFFF)
        f.watchdog()
        self.assertEqual(f.refresh_count(), 0)
        f.tick()
        self.assertEqual(f.value("g_tim6_completed"), 0)
        f.watchdog()
        f.watchdog()
        self.assertEqual(f.refresh_count(), 1)

    def test_refresh_records_snapshot_without_losing_new_progress(self):
        f = self.f
        f.tick()
        f.progress_on_refresh = True
        f.watchdog()
        self.assertEqual(f.value("g_watchdog_last_completed"), 1)
        self.assertEqual(f.value("g_tim6_completed"), 2)
        f.watchdog()
        f.watchdog()
        self.assertEqual(f.refresh_count(), 2)

    def test_initialization_discards_previous_progress(self):
        f = self.f
        f.tick(3)
        f.watchdog()
        f.tick()
        f.init()
        self.assertEqual(f.value("g_tim6_completed"), 0)
        self.assertEqual(f.value("g_watchdog_last_completed"), 0)
        f.writes.clear()
        f.watchdog()
        self.assertEqual(f.refresh_count(), 0)

    def test_real_main_loop_feeds_after_key_shoot_and_adc_tasks(self):
        f = self.f
        tasks = ("Laser_Process_Key1_Requests", "Laser_Process_Shoot_Requests",
                 "Laser_Process_Current_Sample", "Laser_Process_Watchdog")
        task_addresses = {f.symbols[name] & ~1: name for name in tasks}
        skip = {address & ~1 for name, address in f.symbols.items()
                if name.startswith("MX_") or name in
                ("HAL_Init", "SystemClock_Config", "HAL_ADCEx_Calibration_Start")}
        visits, feed_counts = [], []
        key_visits = 0

        def observe_main(cpu, address, size, user):
            nonlocal key_visits
            if address in skip:
                cpu.reg_write(safety.UC_ARM_REG_R0, 0)
                cpu.reg_write(safety.UC_ARM_REG_PC, cpu.reg_read(safety.UC_ARM_REG_LR))
            name = task_addresses.get(address)
            if name == tasks[0]:
                key_visits += 1
                if key_visits == 3:
                    cpu.emu_stop()
                    return
                if key_visits == 1:
                    # Supply one completed interrupt; the real loop must consume it.
                    f.write(f.symbols["g_tim6_completed"], 1)
            if name:
                visits.append(name)
                feed_counts.append(f.refresh_count())

        f.cpu.hook_add(safety.UC_HOOK_CODE, observe_main)
        f.call("main", terminal=True)
        self.assertEqual(visits, list(tasks) * 2)
        self.assertEqual(feed_counts, [0] * 4 + [1] * 4)
        self.assertEqual(f.refresh_count(), 1)


class FaultAndCSSTests(unittest.TestCase):
    def setUp(self):
        self.f = Firmware()
        self.f.init()

    def running(self):
        self.f.press()
        self.f.tick(safety.START_MS)
        self.assertEqual(self.f.state(), 2)

    def test_low_level_without_exti_kills_on_fifth_sample_and_locks(self):
        f = self.f
        self.running()
        f.fault(True)
        f.tick(4)
        self.assertEqual(f.state(), 2)
        self.assertFalse(f.off())
        self.assertEqual(f.value("g_laser_fault_debounce_ms"), 1)
        self.assertEqual(f.read(EXTI_IMR1) & STOP, 0)
        f.tick()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())
        f.fault(False)
        f.key(False)
        f.tick()
        f.press()
        for _ in range(1200):
            f.tick()
            f.call("Laser_Process_Key1_Requests")
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_high_sample_cancels_short_low_and_rearms_exti(self):
        f = self.f
        self.running()
        f.fault(True)
        f.tick(4)
        f.fault(False)
        f.tick()
        self.assertEqual(f.state(), 2)
        self.assertEqual(f.value("g_laser_fault_debounce_ms"), 0)
        self.assertEqual(f.read(EXTI_IMR1) & STOP, STOP)
        f.fault(True)
        f.tick(4)
        self.assertEqual(f.state(), 2)
        f.tick()
        self.assertEqual(f.state(), 3)

    def test_latched_fault_keeps_feeding_without_unlocking(self):
        f = self.f
        self.running()
        f.fault(True)
        f.tick(5)
        self.assertEqual(f.state(), 3)
        f.watchdog()  # Consume all progress accumulated before the locked interval.
        f.writes.clear()
        f.fault(False)
        for expected in range(1, 11):
            f.tick()
            f.call("Laser_Process_Key1_Requests")
            f.call("Laser_Process_Shoot_Requests")
            f.call("Laser_Process_Current_Sample")
            f.watchdog()
            f.watchdog()
            self.assertEqual(f.refresh_count(), expected)
            self.assertEqual(f.state(), 3)
            self.assertTrue(f.off())

    def test_irq_and_poll_do_not_extend_pending_fault(self):
        f = self.f
        self.running()
        f.fault(True)
        f.call("HAL_GPIO_EXTI_Callback", STOP)
        for remaining in (4, 3, 2, 1):
            f.tick()
            self.assertEqual(f.value("g_laser_fault_debounce_ms"), remaining)
            f.call("HAL_GPIO_EXTI_Callback", STOP)
            self.assertEqual(f.value("g_laser_fault_debounce_ms"), remaining)
        f.tick()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_low_during_exti_rearm_starts_new_confirmation(self):
        f = self.f
        self.running()
        f.fault(True)
        f.tick(4)
        f.fault(False)
        f.drop_on_reenable = True
        f.tick()  # high sample, then low at Laser_Enable_Stop_EXTI entry
        self.assertFalse(f.drop_on_reenable)
        self.assertEqual(f.state(), 2)
        self.assertEqual(f.value("g_laser_fault_debounce_ms"), 5)
        f.tick(4)
        self.assertEqual(f.state(), 2)
        f.tick()
        self.assertEqual(f.state(), 3)

    def test_startup_mask_still_kills_low_at_mask_expiry(self):
        f = self.f
        f.fault(True)
        f.press()
        f.tick(safety.START_MS - 1)
        self.assertEqual(f.state(), 1)
        self.assertEqual(f.value("g_laser_fault_debounce_ms"), 0)
        f.tick()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    @unittest.skipUnless(MODE == 2, "cycle mode")
    def test_polled_fault_survives_cycle_boundary(self):
        f = self.f
        f.press()
        f.tick(998)
        f.fault(True)
        f.tick(2)
        self.assertEqual(f.state(), 2)
        self.assertFalse(f.off())
        f.tick(3)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_css_nmi_shuts_down_before_rcc_handling_and_never_feeds(self):
        f = self.f
        self.running()
        f.write(RCC_CIFR, CSS)
        f.writes.clear()
        f.call("NMI_Handler", terminal=True)
        self.assertTrue(f.off())
        self.assertEqual(f.refresh_count(), 0)
        self.assertEqual(f.cpu.reg_read(safety.UC_ARM_REG_PRIMASK), 1)
        self.assertNotEqual(f.cpu.reg_read(safety.UC_ARM_REG_PC), safety.RETURN)
        self.assertEqual([name for name, _, _ in f.css_entries],
                         ["HAL_RCC_NMI_IRQHandler", "HAL_RCC_CSSCallback"])
        self.assertTrue(all(off for _, off, _ in f.css_entries))
        pwm = next(i for i, (a, v) in enumerate(f.writes)
                   if a == safety.GPIOA + 0x28 and v == 1 << 9)
        dac = next(i for i, (a, v) in enumerate(f.writes) if a == safety.DAC + 8 and v == 0)
        clear = next(i for i, (a, v) in enumerate(f.writes) if a == RCC_CICR and v & CSS)
        self.assertLess(pwm, dac)
        self.assertLess(dac, f.css_entries[0][2])
        self.assertLess(dac, clear)


if __name__ == "__main__":
    print("Testing watchdog/FAULT/CSS, mode", MODE, safety.ELF_PATH)
    unittest.main(verbosity=2)
