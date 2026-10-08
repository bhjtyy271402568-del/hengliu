"""Run bench-mode behavior against an actual Debug ELF in the safety emulator.

Usage: python tests/test_laser_bench.py 1|2 path/to/hengliu.elf
The existing safety suite remains the regression suite for mode 0.
This models software behavior, not board timing or analog/thermal behavior.
"""

import sys
import unittest

MODE = int(sys.argv.pop(1))
if MODE not in (1, 2):
    raise SystemExit("Expected bench mode 1 or 2")

import test_laser_safety as safety


class BenchTests(unittest.TestCase):
    def setUp(self):
        self.f = safety.Firmware()
        self.f.init()

    def release(self):
        self.f.key(False)
        self.f.tick()

    def run_main(self, count):
        for _ in range(count):
            self.f.tick()
            self.f.call("Laser_Process_Key1_Requests")

    def fault(self):
        self.f.write(safety.GPIOB + 0x10, 0)
        self.f.call("HAL_GPIO_EXTI_Callback", 1 << 12)

    def test_boot_held_key_needs_release_and_new_press(self):
        f = self.f
        f.key(True)
        f.init()
        self.run_main(1200)
        self.assertTrue(f.off())
        self.release()
        f.press()
        self.assertEqual(f.state(), 1)

    def test_first_press_debounced_and_dac_ramps(self):
        f = self.f
        f.key(True)
        f.tick(19)
        f.call("Laser_Process_Key1_Requests")
        self.assertTrue(f.off())
        f.tick()
        f.call("Laser_Process_Key1_Requests")
        self.assertEqual(f.state(), 1)
        self.assertEqual(f.read(safety.DAC + 8), 0)
        f.tick()
        self.assertEqual(f.read(safety.DAC + 8), 50)
        f.tick(safety.START_MS - 1)
        self.assertEqual(f.state(), 2)
        self.assertEqual(f.read(safety.DAC + 8), safety.TEST_DAC)

    def test_release_keeps_output_on(self):
        self.f.press()
        self.release()
        self.f.tick(safety.START_MS)
        self.assertEqual(self.f.state(), 2)
        self.assertFalse(self.f.off())

    def test_completed_click_can_start_after_release(self):
        f = self.f
        f.key(True)
        f.tick(20)
        self.release()
        f.call("Laser_Process_Key1_Requests")
        self.assertEqual(f.state(), 1)

    def test_second_press_stops_without_main_loop(self):
        f = self.f
        f.press()
        self.release()
        f.tick(safety.START_MS)
        f.key(True)
        f.tick(19)
        self.assertFalse(f.off())
        f.tick()
        self.assertTrue(f.off())
        self.run_main(1200)
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)

    def test_second_press_stops_during_ramp(self):
        f = self.f
        f.press()
        self.release()
        f.key(True)
        f.tick(20)
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)

    def test_second_press_cancels_unconsumed_start(self):
        f = self.f
        f.key(True)
        f.tick(20)
        self.release()
        f.key(True)
        f.tick(20)
        f.call("Laser_Process_Key1_Requests")
        self.run_main(1200)
        self.assertTrue(f.off())

    def test_explicit_stop_cancels_automatic_restart(self):
        f = self.f
        f.press()
        f.tick(safety.START_MS)
        f.call("Laser_Stop")
        self.run_main(1200)
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)

    def test_fault_during_startup_stays_locked(self):
        f = self.f
        f.write(safety.GPIOB + 0x10, 0)
        f.press()
        f.tick(safety.START_MS)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())
        self.release()
        f.press()
        self.run_main(1200)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_running_fault_stays_locked_after_input_recovers(self):
        f = self.f
        f.press()
        f.tick(safety.START_MS)
        self.fault()
        f.tick(5)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())
        f.write(safety.GPIOB + 0x10, 1 << 12)
        self.release()
        f.press()
        self.run_main(1200)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_stop_preserves_fault_lockout(self):
        f = self.f
        f.press()
        f.call("Laser_Emergency_Kill")
        f.call("Laser_Stop")
        self.run_main(1200)
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 3)
        self.release()
        f.press()
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.off())

    def test_reinitialization_clears_active_bench(self):
        f = self.f
        f.press()
        f.tick(10)
        self.release()
        f.init()
        self.run_main(1200)
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)

    def test_start_commit_preserves_interrupt_mask(self):
        f = self.f
        f.press()
        self.assertEqual(f.start_masks, [1])
        self.assertEqual(f.cpu.reg_read(safety.UC_ARM_REG_PRIMASK), 0)

    def test_current_feedback_and_fault_blink_still_work(self):
        f = self.f
        f.press()
        f.tick(safety.START_MS)
        f.adc_raw = round(safety.TEST_DAC * 82 / 273)
        f.tick(100, adc=True)
        self.assertTrue(f.green())
        self.fault()
        f.tick(5, adc=True)
        self.assertEqual(f.state(), 3)
        self.assertTrue(f.green())
        f.tick(250, adc=True)
        self.assertFalse(f.green())
        f.tick(250, adc=True)
        self.assertTrue(f.green())

    @unittest.skipUnless(MODE == 1, "continuous mode")
    def test_continuous_mode_has_no_one_second_timeout(self):
        self.f.press()
        self.release()
        self.run_main(2500)
        self.assertEqual(self.f.state(), 2)
        self.assertFalse(self.f.off())

    @unittest.skipUnless(MODE == 2, "cycle mode")
    def test_cycle_has_1000ms_on_100ms_off_and_new_ramp(self):
        f = self.f
        f.press()
        for _ in range(3):
            f.tick(999)
            self.assertFalse(f.off())
            f.tick()
            self.assertTrue(f.off())
            self.assertEqual(f.state(), 0)
            self.run_main(99)
            self.assertTrue(f.off())
            self.run_main(1)
            self.assertEqual(f.state(), 1)
            self.assertFalse(f.off())
            self.assertEqual(f.read(safety.DAC + 8), 0)

    @unittest.skipUnless(MODE == 2, "cycle mode")
    def test_delayed_main_loop_does_not_shorten_on_interval(self):
        f = self.f
        f.key(True)
        f.tick(20)
        f.tick(1500)
        self.assertTrue(f.off())
        f.call("Laser_Process_Key1_Requests")
        f.tick(999)
        self.assertFalse(f.off())
        f.tick()
        self.assertTrue(f.off())
        f.tick(1500)
        self.assertTrue(f.off())
        f.call("Laser_Process_Key1_Requests")
        f.tick(999)
        self.assertFalse(f.off())
        f.tick()
        self.assertTrue(f.off())

    @unittest.skipUnless(MODE == 2, "cycle mode")
    def test_press_during_off_gap_cancels_cycle(self):
        f = self.f
        f.press()
        self.release()
        f.tick(999)
        self.assertTrue(f.off())
        f.press()
        self.run_main(1200)
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)

    @unittest.skipUnless(MODE == 2, "cycle mode")
    def test_press_at_restart_boundary_cancels_cycle(self):
        f = self.f
        f.press()
        self.release()
        f.tick(999)
        f.tick(80)
        f.key(True)
        f.tick(20)
        f.call("Laser_Process_Key1_Requests")
        self.run_main(1200)
        self.assertTrue(f.off())

    @unittest.skipUnless(MODE == 2, "cycle mode")
    def test_fault_debounce_survives_cycle_boundary(self):
        f = self.f
        f.press()
        f.tick(998)
        self.fault()
        f.tick(2)
        self.assertEqual(f.state(), 2)
        f.tick(3)
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 3)
        self.run_main(1200)
        self.assertEqual(f.state(), 3)

    @unittest.skipUnless(MODE == 2, "cycle mode")
    def test_short_fault_glitch_at_boundary_does_not_latch(self):
        f = self.f
        f.press()
        f.tick(998)
        self.fault()
        f.tick(2)
        f.write(safety.GPIOB + 0x10, 1 << 12)
        f.tick(3)
        self.assertTrue(f.off())
        self.assertEqual(f.state(), 0)
        self.run_main(100)
        self.assertEqual(f.state(), 1)


if __name__ == "__main__":
    print("Testing bench mode", MODE, safety.ELF_PATH)
    unittest.main(verbosity=2)
