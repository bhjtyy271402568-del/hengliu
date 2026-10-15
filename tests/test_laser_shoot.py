"""Run active-low SHOOT and K2 toggle tests on the actual dual-trigger ELF.

Usage: python -B tests/test_laser_shoot.py build/Debug/hengliu.elf
Reuses the Cortex-M emulator. Tick calls model 1 ms sampling, not physical
interrupt latency, optocoupler thresholds, IWDG reset or laser shutdown time.
"""

import unittest

import test_laser_safety as safety

SHOOT = 1 << 8
STOP = 1 << 12
EXTI_IMR1 = 0x40010400


class Firmware(safety.Firmware):
    def value(self, name):
        return int.from_bytes(self.cpu.mem_read(self.symbols[name], self.sizes[name]), "little")

    def set_value(self, name, value):
        self.cpu.mem_write(self.symbols[name], value.to_bytes(self.sizes[name], "little"))

    def signal(self, active):
        # TLP2761: external 5 V -> PA8 LOW; inactive -> PA8 HIGH.
        self.write(safety.GPIOA + 0x10, 0 if active else SHOOT)

    def fault(self, active):
        self.write(safety.GPIOB + 0x10, 0 if active else STOP)

    def enable(self):
        self.set_value("g_laser_shoot_dac_val", safety.TEST_DAC)
        self.call("Laser_Set_Shoot_Enable", 1)

    def requests(self):
        self.call("Laser_Process_Key1_Requests")
        self.call("Laser_Process_Shoot_Requests")

    def start(self):
        self.signal(False)
        self.call("HAL_GPIO_EXTI_Callback", SHOOT)
        self.tick(5)
        self.signal(True)
        self.call("HAL_GPIO_EXTI_Callback", SHOOT)
        self.tick(5)
        self.requests()


class ShootTests(unittest.TestCase):
    def setUp(self):
        self.f = Firmware()
        self.f.init()
        self.f.enable()

    def running(self):
        self.f.start()
        self.assertEqual(self.f.state(), 1)
        self.f.tick(safety.START_MS)
        self.assertEqual(self.f.state(), 2)

    def test_active_at_boot_requires_inactive_then_new_active(self):
        f = self.f
        f.signal(True)
        f.tick(50)
        f.requests()
        self.assertTrue(f.off())
        f.start()
        self.assertEqual(f.state(), 1)

    def test_inactive_stays_off_and_short_active_does_not_start(self):
        f = self.f
        f.signal(False)
        f.tick(20)
        f.requests()
        self.assertTrue(f.off())
        f.signal(True)
        f.tick(4)
        f.requests()
        self.assertTrue(f.off())
        f.signal(False)
        f.tick()
        f.signal(True)
        f.tick(4)
        f.requests()
        self.assertTrue(f.off())
        f.tick()
        f.requests()
        self.assertEqual(f.state(), 1)

    def test_maintained_signal_runs_past_bench_cycle_and_keeps_dac(self):
        self.running()
        self.f.tick(1200)
        self.assertEqual(self.f.state(), 2)
        self.assertEqual(self.f.read(safety.DAC + 8), safety.TEST_DAC)

    def test_withdrawal_stops_ramp_and_run_without_main_loop(self):
        for ticks in (3, safety.START_MS):
            with self.subTest(ticks=ticks):
                f = Firmware()
                f.init()
                f.enable()
                f.start()
                self.assertEqual(f.state(), 1)
                f.tick(ticks)
                f.signal(False)
                f.call("HAL_GPIO_EXTI_Callback", SHOOT)
                f.tick(4)
                self.assertFalse(f.off())
                f.tick()
                self.assertTrue(f.off())
                self.assertEqual(f.state(), 0)

    def test_short_inactive_glitch_does_not_stop_running(self):
        self.running()
        f = self.f
        f.signal(False)
        f.tick(4)
        f.signal(True)
        f.tick()
        self.assertEqual(f.state(), 2)

    def test_stale_start_rechecks_raw_level_before_next_tick(self):
        f = self.f
        f.signal(False)
        f.tick(5)
        f.signal(True)
        f.call("HAL_GPIO_EXTI_Callback", SHOOT)
        f.tick(5)
        self.assertEqual(f.value("g_laser_shoot_start_req"), 1)
        f.signal(False)  # no TIM6 between withdrawal and main-loop commit
        f.requests()
        self.assertTrue(f.off())

    def test_sampled_withdrawal_cancels_pending_start(self):
        f = self.f
        f.signal(False)
        f.tick(5)
        f.signal(True)
        f.tick(5)
        f.signal(False)
        f.tick()
        f.signal(True)
        f.requests()
        self.assertTrue(f.off())

    def test_start_commit_atomic_and_preserves_interrupt_mask(self):
        self.f.start()
        self.assertEqual(self.f.start_masks, [1])
        self.assertEqual(self.f.cpu.reg_read(safety.UC_ARM_REG_PRIMASK), 0)
        self.f.cpu.reg_write(safety.UC_ARM_REG_PRIMASK, 1)
        self.f.requests()
        self.assertEqual(self.f.cpu.reg_read(safety.UC_ARM_REG_PRIMASK), 1)

    def test_k2_stops_without_main_and_cannot_restart_held_signal(self):
        self.running()
        f = self.f
        f.key(True)
        f.tick(20)
        self.assertTrue(f.off())
        f.key(False)
        f.tick(30)
        f.requests()
        self.assertTrue(f.off())
        f.start()
        self.assertEqual(f.state(), 1)

    def test_k2_alone_toggles_and_release_keeps_running(self):
        f = self.f
        f.signal(False)
        f.tick(5)
        f.press()
        self.assertEqual(f.state(), 1)
        f.key(False)
        f.tick(1200)
        f.requests()
        self.assertEqual(f.state(), 2)
        self.assertEqual(f.read(safety.DAC + 8), safety.TEST_DAC)
        f.key(True)
        f.tick(20)
        self.assertTrue(f.off())
        f.key(False)
        f.tick(1200)
        f.requests()
        self.assertTrue(f.off())

    def test_shoot_withdrawal_stops_button_started_output(self):
        f = self.f
        f.signal(False)
        f.tick(5)
        f.press()
        f.key(False)
        f.tick(safety.START_MS)
        f.signal(True)
        f.tick(5)
        f.requests()
        self.assertEqual(f.state(), 2)
        self.assertEqual(len(f.start_masks), 1, "SHOOT must not restart an active ramp")
        f.signal(False)
        f.tick(5)
        self.assertTrue(f.off())
        f.requests()
        f.tick(1200)
        self.assertTrue(f.off())

    def test_withdrawal_wins_over_button_press_on_same_tick(self):
        self.running()
        f = self.f
        f.key(True)
        f.tick(15)
        f.signal(False)
        f.tick(5)  # both withdrawal and K2 press qualify in this tick
        f.requests()
        self.assertTrue(f.off())
        f.tick(50)
        f.requests()
        self.assertTrue(f.off(), "held K2 must not restart after withdrawal")
        f.key(False)
        f.tick()
        f.press()
        self.assertEqual(f.state(), 1)

    def test_withdrawal_cancels_queued_button_start(self):
        f = self.f
        f.signal(False)
        f.tick(5)
        f.key(True)
        f.tick(20)  # completed press, main loop has not consumed it
        self.assertEqual(f.value("g_key1_start_req"), 1)
        f.signal(True)
        f.tick(5)
        f.signal(False)
        f.tick(5)
        f.requests()
        self.assertTrue(f.off())
        f.tick(50)
        f.requests()
        self.assertTrue(f.off())

    def test_button_stop_wins_over_new_shoot_on_same_tick(self):
        f = self.f
        f.signal(False)
        f.tick(5)
        f.press()
        f.key(False)
        f.tick(safety.START_MS)
        self.assertEqual(f.state(), 2)
        f.key(True)
        f.tick(15)
        f.signal(True)
        f.tick(5)
        f.requests()
        self.assertTrue(f.off())
        f.key(False)
        f.tick(50)
        f.requests()
        self.assertTrue(f.off())
        f.start()
        self.assertEqual(f.state(), 1)

    def test_boot_with_button_and_shoot_held_does_not_start(self):
        f = Firmware()
        f.key(True)
        f.signal(True)
        f.init()
        f.enable()
        f.tick(50)
        f.requests()
        self.assertTrue(f.off())
        f.key(False)
        f.tick(50)
        f.requests()
        self.assertTrue(f.off())
        f.start()
        self.assertEqual(f.state(), 1)

    def test_button_can_stop_shoot_started_ramp(self):
        f = self.f
        f.start()
        self.assertEqual(f.state(), 1)
        f.key(True)
        f.tick(20)
        self.assertTrue(f.off())
        f.key(False)
        f.tick(50)
        f.requests()
        self.assertTrue(f.off())

    def test_button_start_and_held_press_keep_dac_at_requested_target(self):
        f = self.f
        f.signal(False)
        f.tick(5)
        f.press()
        self.assertEqual(f.state(), 1)
        f.tick(1200)
        f.requests()
        self.assertEqual(f.state(), 2)
        self.assertEqual(f.read(safety.DAC + 8), 2835)
        self.assertEqual(len(f.start_masks), 1)

    def test_fault_blocks_both_button_and_shoot_restart(self):
        self.running()
        f = self.f
        f.fault(True)
        f.tick(5)
        f.fault(False)
        f.press()
        f.start()
        f.requests()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_k2_held_blocks_external_start_and_release_is_not_start(self):
        f = self.f
        f.key(True)
        f.start()
        self.assertTrue(f.off())
        f.key(False)
        f.tick(20)
        f.requests()
        self.assertTrue(f.off())
        f.start()
        self.assertEqual(f.state(), 1)

    def test_k2_raw_press_cancels_queued_start_before_next_tick(self):
        f = self.f
        f.signal(False)
        f.tick(5)
        f.signal(True)
        f.tick(5)
        f.key(True)
        f.requests()
        self.assertTrue(f.off())

    def test_disable_stops_and_reenable_requires_new_signal(self):
        self.running()
        f = self.f
        f.call("Laser_Set_Shoot_Enable", 0)
        self.assertTrue(f.off())
        f.enable()
        f.tick(20)
        f.requests()
        self.assertTrue(f.off())
        f.start()
        self.assertEqual(f.state(), 1)

    def test_zero_dac_cannot_start(self):
        self.f.set_value("g_laser_shoot_dac_val", 0)
        self.f.start()
        self.assertTrue(self.f.off())

    def test_shoot_exti_stays_masked(self):
        f = self.f
        f.start()
        f.call("HAL_GPIO_EXTI_Callback", SHOOT)
        f.signal(False)
        f.tick(5)
        self.assertEqual(f.read(EXTI_IMR1) & SHOOT, 0)

    def test_fault_latches_without_edge_and_blocks_retrigger(self):
        self.running()
        f = self.f
        f.fault(True)
        f.tick(5)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())
        f.fault(False)
        f.enable()
        f.start()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_startup_fault_mask_is_retained(self):
        f = self.f
        f.fault(True)
        f.start()
        f.tick(safety.START_MS - 1)
        self.assertEqual(f.state(), 1)
        f.tick()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_withdrawal_shuts_off_before_pending_fault_is_confirmed(self):
        self.running()
        f = self.f
        f.signal(False)
        f.tick(4)
        f.fault(True)
        f.call("HAL_GPIO_EXTI_Callback", STOP)
        f.tick()
        self.assertTrue(f.off(), "FAULT debounce must never delay requested shutdown")
        self.assertEqual(f.state(), 0)
        self.assertGreater(f.value("g_laser_fault_debounce_ms"), 0)
        f.call("Laser_Start", safety.TEST_DAC)
        self.assertTrue(f.off(), "pending FAULT must block restart")
        f.tick(4)
        self.assertEqual(f.state(), 3)

    def test_repeated_stop_cannot_clear_pending_fault(self):
        self.running()
        f = self.f
        f.fault(True)
        f.tick()
        for _ in range(4):
            f.call("Laser_Stop")
            self.assertTrue(f.off())
            f.tick()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_fault_recovers_after_stop_without_rearming_exti(self):
        self.running()
        f = self.f
        f.fault(True)
        f.tick()
        f.call("Laser_Stop")
        self.assertTrue(f.off())
        f.fault(False)
        f.tick()
        self.assertEqual(f.state(), 0)
        self.assertEqual(f.value("g_laser_fault_debounce_ms"), 0)
        self.assertEqual(f.read(EXTI_IMR1) & STOP, 0)
        f.start()
        self.assertEqual(f.state(), 1)

    def test_normal_shutdown_does_not_start_new_fault_debounce(self):
        self.running()
        f = self.f
        f.signal(False)
        f.tick(5)
        f.fault(True)  # an indication caused only by already-disabled output
        f.tick(10)
        self.assertEqual(f.state(), 0)

    def test_real_main_enables_external_mode_with_existing_target(self):
        f = Firmware()
        skip = {address & ~1 for name, address in f.symbols.items()
                if name.startswith("MX_") or name in
                ("HAL_Init", "SystemClock_Config", "HAL_ADCEx_Calibration_Start")}

        def observe(cpu, address, size, user):
            if address in skip:
                cpu.reg_write(safety.UC_ARM_REG_R0, 0)
                cpu.reg_write(safety.UC_ARM_REG_PC, cpu.reg_read(safety.UC_ARM_REG_LR))
            if address == (f.symbols["Laser_Process_Key1_Requests"] & ~1):
                cpu.emu_stop()

        f.cpu.hook_add(safety.UC_HOOK_CODE, observe)
        f.call("main", terminal=True)
        self.assertEqual(f.value("g_laser_shoot_enabled"), 1)
        self.assertEqual(f.value("g_laser_shoot_dac_val"), safety.TEST_DAC)
        self.assertTrue(f.off())


if __name__ == "__main__":
    unittest.main(verbosity=2)
