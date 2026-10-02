/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dac.h"
#include "dma.h"
#include "iwdg.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define LASER_SHOOT_DEBOUNCE_MS 5U
#define LASER_FAULT_DEBOUNCE_MS 5U
#define LASER_FAULT_LED_BLINK_MS 250U
#define LASER_DAC_RAMP_STEP_PER_MS 50U
#define LASER_START_MASK_EXTRA_MS 100U
#define LASER_START_MASK_MAX_MS 200U
#define KEY1_PRESS_DEBOUNCE_MS 20U
#define TEST_DAC_VALUE 3645U
#define LASER_CURRENT_GOOD_MS 100U
#define LASER_CURRENT_STALE_MS 5U
#define LASER_CURRENT_TOLERANCE_PERCENT 20U

/* Bench test only: 0 = hold K2; 1 = toggle; 2 = toggle a timed cycle.
   K2 is named KEY1 in the generated GPIO definitions. */
#ifndef LASER_BENCH_MODE
#define LASER_BENCH_MODE 1U
#endif
#if LASER_BENCH_MODE > 2U
#error "LASER_BENCH_MODE must be 0, 1 or 2"
#endif
#define BENCH_CYCLE_ON_MS 1000U
#define BENCH_CYCLE_OFF_MS 100U

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
volatile Laser_State_t g_laser_state = LASER_STATE_IDLE;
volatile uint16_t g_laser_start_mask_ms = 0U;
volatile uint16_t g_laser_fault_debounce_ms = 0U;
static volatile uint16_t g_laser_dac_target_val = 0U;
static volatile uint16_t g_laser_dac_current_val = 0U;
volatile uint16_t g_laser_shoot_dac_val = 0U;
static volatile uint16_t g_laser_shoot_debounce_ms = 0U;
static volatile uint16_t g_laser_fault_led_blink_ms = 0U;
static volatile uint16_t g_laser_shoot_req_dac_val = 0U;
static volatile uint8_t g_laser_shoot_enabled = 0U;
static volatile uint8_t g_laser_shoot_start_req = 0U;
static volatile uint8_t g_laser_shoot_stop_req = 0U;
static volatile uint16_t g_key1_press_debounce_ms = 0U;
static volatile uint8_t g_key1_latched_pressed = 0U;
static volatile uint8_t g_key1_start_req = 0U;
static volatile uint8_t g_key1_release_required = 0U;
/* Nominal, uncalibrated ISMON feedback. Visible in the debugger. */
volatile uint16_t g_laser_current_adc = 0U;
volatile uint16_t g_laser_target_adc = 0U;
volatile uint8_t g_laser_current_valid = 0U;
static volatile uint16_t g_laser_current_age_ms = LASER_CURRENT_STALE_MS;
static volatile uint16_t g_laser_current_good_ms = 0U;
static volatile uint32_t g_tim6_completed = 0U;
static uint32_t g_watchdog_last_completed = 0U;
#if LASER_BENCH_MODE != 0U
static volatile uint8_t g_bench_active = 0U;
static volatile uint16_t g_bench_phase_ms = 0U;
#endif

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
static void Laser_Disable_Stop_EXTI(void);
static uint8_t Laser_Enable_Stop_EXTI(void);
static void Laser_Disable_Shoot_EXTI(void);
static void Laser_Enable_Shoot_EXTI(void);
static void Laser_Process_Shoot_Debounce(void);
static void Laser_Process_Shoot_Requests(void);
static void Laser_Process_Fault_LED(void);
static void Laser_Process_Key1_Debounce(void);
static void Laser_Process_Key1_Requests(void);
static uint16_t Laser_Calc_Start_Mask_Ms(uint16_t dac_val);
static void Laser_Process_Dac_Ramp(void);
static void Laser_Set_Dac_12bit(uint16_t dac_val);
static void Laser_TIM6_Start_1ms(void);
static void Laser_Process_Current_Sample(void);
static void Laser_Process_Current_LED(void);
static void Laser_Process_Watchdog(void);
static void Laser_Process_Stop_Fault(void);
#if LASER_BENCH_MODE != 0U
static void Laser_Process_Bench(void);
#endif

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* Main-loop only: each refresh consumes a NEW completed TIM6 task. */
static void Laser_Process_Watchdog(void)
{
  uint32_t completed = g_tim6_completed;

  if (completed != g_watchdog_last_completed)
  {
    g_watchdog_last_completed = completed;
    HAL_IWDG_Refresh(&hiwdg);
  }
}

/* Main-loop only: ADC polling must not delay the TIM6 safety task. */
static void Laser_Process_Current_Sample(void)
{
  static uint32_t last_sample_ms = UINT32_MAX;
  uint32_t now = HAL_GetTick();
  uint32_t primask;
  uint16_t raw = 0U;
  uint8_t valid = 0U;

  if (now == last_sample_ms)
  {
    return;
  }
  last_sample_ms = now;

  if (HAL_ADC_Start(&hadc1) == HAL_OK)
  {
    if (HAL_ADC_PollForConversion(&hadc1, 1U) == HAL_OK)
    {
      raw = (uint16_t)HAL_ADC_GetValue(&hadc1);
      valid = 1U;
    }
  }
  if (HAL_ADC_Stop(&hadc1) != HAL_OK)
  {
    valid = 0U;
  }

  primask = __get_PRIMASK();
  __disable_irq();
  g_laser_current_adc = raw;
  g_laser_current_valid = valid;
  g_laser_current_age_ms = 0U;
  if (valid == 0U)
  {
    g_laser_current_good_ms = 0U;
  }
  if (primask == 0U)
  {
    __enable_irq();
  }
}

static void Laser_Process_Current_LED(void)
{
  uint32_t measured;
  uint32_t target;

  if (g_laser_current_age_ms < LASER_CURRENT_STALE_MS)
  {
    g_laser_current_age_ms++;
  }

  /* R2/R19 = 10k/8.2k, CTRL = 30*Rs*I, ISMON = 20*Rs*I.
     ADC and DAC share VREF+: target ADC = DAC * (41/91) * (20/30).
     This nominal ratio is NOT an ISMON accuracy calibration. */
  target = (uint32_t)g_laser_dac_target_val * 82U;
  g_laser_target_adc = (uint16_t)((target + 136U) / 273U);
  measured = (uint32_t)g_laser_current_adc * 273U * 100U;

  if ((g_laser_state == LASER_STATE_RUNNING) && (target > 0U) &&
      (g_laser_fault_debounce_ms == 0U) &&
      (HAL_GPIO_ReadPin(STOP_GPIO_Port, STOP_Pin) == GPIO_PIN_SET) &&
      (g_laser_current_valid != 0U) &&
      (g_laser_current_age_ms < LASER_CURRENT_STALE_MS) &&
      (measured >= target * (100U - LASER_CURRENT_TOLERANCE_PERCENT)) &&
      (measured <= target * (100U + LASER_CURRENT_TOLERANCE_PERCENT)))
  {
    if (g_laser_current_good_ms < LASER_CURRENT_GOOD_MS)
    {
      g_laser_current_good_ms++;
    }
  }
  else
  {
    g_laser_current_good_ms = 0U;
  }

  /* Fault blinking owns the LED while FAULT is latched. */
  if (g_laser_state != LASER_STATE_FAULT)
  {
    HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin,
                     (g_laser_current_good_ms >= LASER_CURRENT_GOOD_MS) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  }
}

static void Laser_Disable_Stop_EXTI(void)
{
  EXTI->IMR1 &= ~(uint32_t)STOP_Pin;
  __HAL_GPIO_EXTI_CLEAR_IT(STOP_Pin);
  HAL_NVIC_ClearPendingIRQ(STOP_EXTI_IRQn);
}

static uint8_t Laser_Enable_Stop_EXTI(void)
{
  __HAL_GPIO_EXTI_CLEAR_IT(STOP_Pin);
  HAL_NVIC_ClearPendingIRQ(STOP_EXTI_IRQn);

  if (HAL_GPIO_ReadPin(STOP_GPIO_Port, STOP_Pin) == GPIO_PIN_RESET)
  {
    return 0U;
  }

  EXTI->IMR1 |= (uint32_t)STOP_Pin;
  return 1U;
}

static void Laser_Process_Stop_Fault(void)
{
  if (g_laser_state != LASER_STATE_RUNNING)
  {
    return;
  }

  if (HAL_GPIO_ReadPin(STOP_GPIO_Port, STOP_Pin) == GPIO_PIN_RESET)
  {
    if (g_laser_fault_debounce_ms == 0U)
    {
      Laser_Disable_Stop_EXTI();
      g_laser_fault_debounce_ms = LASER_FAULT_DEBOUNCE_MS;
    }

    /* EXTI and polling share five consecutive 1 ms low samples. */
    g_laser_fault_debounce_ms--;
    if (g_laser_fault_debounce_ms == 0U)
    {
      Laser_Emergency_Kill();
    }
  }
  else if (g_laser_fault_debounce_ms != 0U)
  {
    g_laser_fault_debounce_ms = 0U;
    if (Laser_Enable_Stop_EXTI() == 0U)
    {
      /* A new falling edge during re-arm needs its own debounce. */
      g_laser_fault_debounce_ms = LASER_FAULT_DEBOUNCE_MS;
    }
  }
}

static void Laser_Disable_Shoot_EXTI(void)
{
  EXTI->IMR1 &= ~(uint32_t)SHOOT_Pin;
  __HAL_GPIO_EXTI_CLEAR_IT(SHOOT_Pin);
  HAL_NVIC_ClearPendingIRQ(SHOOT_EXTI_IRQn);
}

static void Laser_Enable_Shoot_EXTI(void)
{
  __HAL_GPIO_EXTI_CLEAR_IT(SHOOT_Pin);
  HAL_NVIC_ClearPendingIRQ(SHOOT_EXTI_IRQn);
  EXTI->IMR1 |= (uint32_t)SHOOT_Pin;
}

static void Laser_Process_Shoot_Debounce(void)
{
  GPIO_PinState shoot_level;

  if (g_laser_shoot_debounce_ms == 0U)
  {
    return;
  }

  g_laser_shoot_debounce_ms--;
  if (g_laser_shoot_debounce_ms > 0U)
  {
    return;
  }

  shoot_level = HAL_GPIO_ReadPin(SHOOT_GPIO_Port, SHOOT_Pin);
  if (g_laser_shoot_enabled != 0U)
  {
    if (shoot_level == GPIO_PIN_RESET)
    {
      if (g_laser_shoot_dac_val > 0U)
      {
        g_laser_shoot_req_dac_val = g_laser_shoot_dac_val;
        g_laser_shoot_start_req = 1U;
        g_laser_shoot_stop_req = 0U;
      }
      else
      {
        g_laser_shoot_start_req = 0U;
        g_laser_shoot_stop_req = 1U;
      }
    }
    else
    {
      g_laser_shoot_start_req = 0U;
      g_laser_shoot_stop_req = 1U;
    }
  }

  if (g_laser_shoot_enabled != 0U)
  {
    Laser_Enable_Shoot_EXTI();
  }
}

static void Laser_Process_Shoot_Requests(void)
{
  uint8_t start_req;
  uint8_t stop_req;
  uint16_t start_dac_val;
  uint32_t primask;

  primask = __get_PRIMASK();
  __disable_irq();
  start_req = g_laser_shoot_start_req;
  stop_req = g_laser_shoot_stop_req;
  start_dac_val = g_laser_shoot_req_dac_val;
  g_laser_shoot_start_req = 0U;
  g_laser_shoot_stop_req = 0U;
  if (primask == 0U)
  {
    __enable_irq();
  }

  if (stop_req != 0U)
  {
    Laser_Stop();
  }
  else if (start_req != 0U)
  {
    Laser_Start(start_dac_val);
  }
}

static void Laser_Process_Fault_LED(void)
{
  if (g_laser_state != LASER_STATE_FAULT)
  {
    return;
  }

  if (g_laser_fault_led_blink_ms > 0U)
  {
    g_laser_fault_led_blink_ms--;
  }

  if (g_laser_fault_led_blink_ms == 0U)
  {
    HAL_GPIO_TogglePin(R_EN_GPIO_Port, R_EN_Pin);
    g_laser_fault_led_blink_ms = LASER_FAULT_LED_BLINK_MS;
  }
}

static void Laser_Process_Key1_Debounce(void)
{
  GPIO_PinState key_level = HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin);

  if (key_level == GPIO_PIN_RESET)
  {
    if (g_key1_release_required != 0U)
    {
      g_key1_press_debounce_ms = 0U;
      return;
    }

    if (g_key1_latched_pressed == 0U)
    {
      if (g_key1_press_debounce_ms < KEY1_PRESS_DEBOUNCE_MS)
      {
        g_key1_press_debounce_ms++;
      }

      if (g_key1_press_debounce_ms >= KEY1_PRESS_DEBOUNCE_MS)
      {
        g_key1_latched_pressed = 1U;
#if LASER_BENCH_MODE != 0U
        if (g_bench_active != 0U)
        {
          /* TIM6 stops output even when the main loop is stalled. */
          Laser_Stop();
        }
        else if (g_laser_state == LASER_STATE_IDLE)
        {
          g_bench_active = 1U;
          g_bench_phase_ms = 0U;
          g_key1_start_req = 1U;
        }
#else
        g_key1_start_req = 1U;
#endif
      }
    }
  }
  else
  {
    g_key1_press_debounce_ms = 0U;
    g_key1_release_required = 0U;

    if (g_key1_latched_pressed != 0U)
    {
      g_key1_latched_pressed = 0U;
#if LASER_BENCH_MODE == 0U
      g_key1_start_req = 0U;
      /* Stop in TIM6 even if the main loop is not making progress. */
      Laser_Stop();
#endif
    }
  }
}

static void Laser_Process_Key1_Requests(void)
{
  uint32_t primask;

  primask = __get_PRIMASK();
  __disable_irq();

  if (g_key1_start_req != 0U)
  {
    g_key1_start_req = 0U;
    /* Recheck and commit together: no stale start after a stop request. */
#if LASER_BENCH_MODE != 0U
    if (g_bench_active != 0U)
#else
    if ((g_key1_latched_pressed != 0U) && (g_key1_release_required == 0U) &&
        (HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == GPIO_PIN_RESET))
#endif
    {
      Laser_Start(TEST_DAC_VALUE);
#if LASER_BENCH_MODE != 0U
      /* Count the ON interval from the actual output enable. */
      g_bench_phase_ms = 0U;
#endif
    }
  }

  if (primask == 0U)
  {
    __enable_irq();
  }
}

#if LASER_BENCH_MODE != 0U
static void Laser_Process_Bench(void)
{
  if (g_bench_active == 0U)
  {
    return;
  }

#if LASER_BENCH_MODE == 2U
  /* A delayed main loop must not consume the next ON interval. */
  if (g_key1_start_req != 0U)
  {
    return;
  }

  if (g_bench_phase_ms < UINT16_MAX)
  {
    g_bench_phase_ms++;
  }

  if (g_laser_state == LASER_STATE_IDLE)
  {
    if (g_bench_phase_ms >= BENCH_CYCLE_OFF_MS)
    {
      g_key1_start_req = 1U;
    }
  }
  else if (g_bench_phase_ms >= BENCH_CYCLE_ON_MS)
  {
    /* Finish a pending fault check before a cycle stop could clear it. */
    if (g_laser_fault_debounce_ms != 0U)
    {
      return;
    }
    Laser_Stop();
    if (g_laser_state == LASER_STATE_IDLE)
    {
      /* Only this planned stop may re-arm the cycle, within TIM6. */
      g_bench_active = 1U;
    }
  }
#endif
}
#endif

static uint16_t Laser_Calc_Start_Mask_Ms(uint16_t dac_val)
{
  uint32_t ramp_ms = ((uint32_t)dac_val + LASER_DAC_RAMP_STEP_PER_MS - 1U) / LASER_DAC_RAMP_STEP_PER_MS;
  uint32_t mask_ms = ramp_ms + LASER_START_MASK_EXTRA_MS;

  if (mask_ms > LASER_START_MASK_MAX_MS)
  {
    mask_ms = LASER_START_MASK_MAX_MS;
  }

  return (uint16_t)mask_ms;
}

static void Laser_Process_Dac_Ramp(void)
{
  uint16_t next_val;

  if ((g_laser_state != LASER_STATE_STARTING) && (g_laser_state != LASER_STATE_RUNNING))
  {
    return;
  }

  if (g_laser_dac_current_val >= g_laser_dac_target_val)
  {
    return;
  }

  next_val = g_laser_dac_current_val + LASER_DAC_RAMP_STEP_PER_MS;
  if ((next_val < g_laser_dac_current_val) || (next_val > g_laser_dac_target_val))
  {
    next_val = g_laser_dac_target_val;
  }

  g_laser_dac_current_val = next_val;
  Laser_Set_Dac_12bit(next_val);
}

static void Laser_Set_Dac_12bit(uint16_t dac_val)
{
  if (dac_val > 4095U)
  {
    dac_val = 4095U;
  }

  if (HAL_DAC_SetValue(&hdac1, DAC_CHANNEL_1, DAC_ALIGN_12B_R, dac_val) != HAL_OK)
  {
    Error_Handler();
  }
}

static void Laser_TIM6_Start_1ms(void)
{
  uint32_t tim6_clk_hz = HAL_RCC_GetPCLK1Freq();

  if ((RCC->CFGR & RCC_CFGR_PPRE1) != 0U)
  {
    tim6_clk_hz *= 2U;
  }

  __HAL_TIM_DISABLE(&htim6);
  __HAL_TIM_DISABLE_IT(&htim6, TIM_IT_UPDATE);
  __HAL_TIM_SET_PRESCALER(&htim6, (tim6_clk_hz / 1000000U) - 1U);
  __HAL_TIM_SET_AUTORELOAD(&htim6, 1000U - 1U);
  __HAL_TIM_SET_COUNTER(&htim6, 0U);
  HAL_TIM_GenerateEvent(&htim6, TIM_EVENTSOURCE_UPDATE);
  __HAL_TIM_CLEAR_FLAG(&htim6, TIM_FLAG_UPDATE);

  if (HAL_TIM_Base_Start_IT(&htim6) != HAL_OK)
  {
    Error_Handler();
  }
}

void Laser_Hardware_Init(void)
{
  g_laser_current_adc = 0U;
  g_laser_target_adc = 0U;
  g_laser_current_valid = 0U;
  g_laser_current_age_ms = LASER_CURRENT_STALE_MS;
  g_laser_current_good_ms = 0U;
  g_laser_state = LASER_STATE_IDLE;
  g_tim6_completed = 0U;
  g_watchdog_last_completed = 0U;
  g_laser_start_mask_ms = 0U;
  g_laser_fault_debounce_ms = 0U;
  g_laser_dac_target_val = 0U;
  g_laser_dac_current_val = 0U;
  g_laser_shoot_debounce_ms = 0U;
  g_laser_fault_led_blink_ms = 0U;
  g_laser_shoot_req_dac_val = 0U;
  g_laser_shoot_enabled = 0U;
  g_laser_shoot_start_req = 0U;
  g_laser_shoot_stop_req = 0U;
  g_key1_press_debounce_ms = 0U;
  g_key1_latched_pressed = 0U;
  g_key1_start_req = 0U;
  g_key1_release_required = (HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == GPIO_PIN_RESET) ? 1U : 0U;
#if LASER_BENCH_MODE != 0U
  g_bench_active = 0U;
  g_bench_phase_ms = 0U;
#endif

  Laser_Disable_Stop_EXTI();
  Laser_Disable_Shoot_EXTI();
  HAL_GPIO_WritePin(PWM_GPIO_Port, PWM_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_RESET);

  /* PA4 must be forced to 0 before enabling DAC output. */
  Laser_Set_Dac_12bit(0U);
  if (HAL_DAC_Start(&hdac1, DAC_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  Laser_Set_Dac_12bit(0U);

  Laser_TIM6_Start_1ms();
}

void Laser_Set_Shoot_Enable(uint8_t enable)
{
  if ((enable != 0U) && (g_laser_state != LASER_STATE_FAULT))
  {
    g_laser_shoot_debounce_ms = 0U;
    g_laser_shoot_start_req = 0U;
    g_laser_shoot_stop_req = 0U;
    g_laser_shoot_enabled = 1U;
    Laser_Enable_Shoot_EXTI();
  }
  else
  {
    g_laser_shoot_enabled = 0U;
    g_laser_shoot_debounce_ms = 0U;
    g_laser_shoot_start_req = 0U;
    g_laser_shoot_stop_req = 0U;
    Laser_Disable_Shoot_EXTI();
  }
}

void Laser_Start(uint16_t dac_val)
{
  uint32_t primask;

  primask = __get_PRIMASK();
  __disable_irq();

  if (g_laser_state != LASER_STATE_IDLE)
  {
    if (primask == 0U)
    {
      __enable_irq();
    }
    return;
  }

  if (dac_val > 4095U)
  {
    dac_val = 4095U;
  }

  Laser_Disable_Stop_EXTI();
  g_laser_fault_debounce_ms = 0U;
  g_laser_fault_led_blink_ms = 0U;
  g_laser_dac_target_val = dac_val;
  g_laser_dac_current_val = 0U;
  g_laser_current_valid = 0U;
  g_laser_current_good_ms = 0U;
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_RESET);

  Laser_Set_Dac_12bit(0U);
  HAL_GPIO_WritePin(PWM_GPIO_Port, PWM_Pin, GPIO_PIN_SET);

  g_laser_start_mask_ms = Laser_Calc_Start_Mask_Ms(dac_val);
  g_laser_state = LASER_STATE_STARTING;

  if (primask == 0U)
  {
    __enable_irq();
  }
}

void Laser_Stop(void)
{
  uint32_t primask;

  primask = __get_PRIMASK();
  __disable_irq();

#if LASER_BENCH_MODE != 0U
  g_bench_active = 0U;
  g_bench_phase_ms = 0U;
  g_key1_start_req = 0U;
#endif

  if (g_laser_state == LASER_STATE_FAULT)
  {
    if (primask == 0U)
    {
      __enable_irq();
    }
    return;
  }

  Laser_Disable_Stop_EXTI();

  g_laser_state = LASER_STATE_IDLE;
  g_laser_start_mask_ms = 0U;
  g_laser_fault_debounce_ms = 0U;
  g_laser_fault_led_blink_ms = 0U;
  g_laser_dac_target_val = 0U;
  g_laser_dac_current_val = 0U;

  PWM_GPIO_Port->BRR = PWM_Pin;
  Laser_Set_Dac_12bit(0U);
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_RESET);

  if (primask == 0U)
  {
    __enable_irq();
  }
}

void Laser_Emergency_Kill(void)
{
#if LASER_BENCH_MODE != 0U
  g_bench_active = 0U;
  g_bench_phase_ms = 0U;
#endif
  Laser_Disable_Stop_EXTI();
  Laser_Disable_Shoot_EXTI();

  PWM_GPIO_Port->BRR = PWM_Pin;
  Laser_Set_Dac_12bit(0U);

  g_laser_start_mask_ms = 0U;
  g_laser_fault_debounce_ms = 0U;
  g_laser_dac_target_val = 0U;
  g_laser_dac_current_val = 0U;
  g_laser_shoot_debounce_ms = 0U;
  g_laser_shoot_enabled = 0U;
  g_laser_shoot_start_req = 0U;
  g_laser_shoot_stop_req = 0U;
  g_key1_press_debounce_ms = 0U;
  g_key1_latched_pressed = 0U;
  g_key1_start_req = 0U;
  g_key1_release_required = 1U;
  g_laser_fault_led_blink_ms = LASER_FAULT_LED_BLINK_MS;
  g_laser_state = LASER_STATE_FAULT;

  /* Fault is indicated by non-blocking blinking in the TIM6 1 ms task. */
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_SET);
}

uint8_t Laser_Fault_Clear(void)
{
  if (g_laser_state != LASER_STATE_FAULT)
  {
    return 1U;
  }

  Laser_Disable_Stop_EXTI();
  Laser_Disable_Shoot_EXTI();

  PWM_GPIO_Port->BRR = PWM_Pin;
  Laser_Set_Dac_12bit(0U);

  g_laser_start_mask_ms = 0U;
  g_laser_fault_debounce_ms = 0U;
  g_laser_dac_target_val = 0U;
  g_laser_dac_current_val = 0U;
  g_laser_shoot_debounce_ms = 0U;
  g_laser_shoot_req_dac_val = 0U;
  g_laser_shoot_enabled = 0U;
  g_laser_shoot_start_req = 0U;
  g_laser_shoot_stop_req = 0U;
  g_key1_press_debounce_ms = 0U;
  g_key1_latched_pressed = 0U;
  g_key1_start_req = 0U;
  g_key1_release_required = 1U;

  g_laser_fault_led_blink_ms = 0U;
  g_laser_state = LASER_STATE_IDLE;
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_RESET);
  return 1U;
}

/* Fatal handlers leave interrupts masked; no HAL, delay or handle is needed. */
void Laser_Fatal_Shutdown(void)
{
  __disable_irq();

  /* PA9 is only driven after GPIOA has been clocked and initialized. */
  if ((RCC->AHB2ENR & RCC_AHB2ENR_GPIOAEN) != 0U)
  {
    PWM_GPIO_Port->BRR = PWM_Pin;
  }

  /* DAC1 channel 1 uses no trigger, so writing zero updates its output. */
  if ((RCC->AHB2ENR & RCC_AHB2ENR_DAC1EN) != 0U)
  {
    DAC1->DHR12R1 = 0U;
  }
  if ((RCC->AHB2ENR & RCC_AHB2ENR_GPIOCEN) != 0U)
  {
    R_EN_GPIO_Port->BRR = R_EN_Pin;
  }
  __DSB();
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_DAC1_Init();
  MX_TIM2_Init();
  MX_USART3_UART_Init();
  MX_ADC1_Init();
  MX_ADC2_Init();
  MX_TIM6_Init();
  MX_IWDG_Init();
  /* USER CODE BEGIN 2 */
  if (HAL_ADCEx_Calibration_Start(&hadc1, ADC_SINGLE_ENDED) != HAL_OK)
  {
    Error_Handler();
  }
  Laser_Hardware_Init();
  g_laser_shoot_dac_val = 0U;
  Laser_Set_Shoot_Enable(0U);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    Laser_Process_Key1_Requests();
    Laser_Process_Shoot_Requests();
    Laser_Process_Current_Sample();
    Laser_Process_Watchdog();
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1_BOOST);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_LSI|RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.LSIState = RCC_LSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV2;
  RCC_OscInitStruct.PLL.PLLN = 85;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_4) != HAL_OK)
  {
    Error_Handler();
  }

  /** Enables the Clock Security System
  */
  HAL_RCC_EnableCSS();
}

/* USER CODE BEGIN 4 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  if (htim->Instance != TIM6)
  {
    return;
  }

  Laser_Process_Shoot_Debounce();
  Laser_Process_Key1_Debounce();
  Laser_Process_Dac_Ramp();

  if ((g_laser_state == LASER_STATE_STARTING) && (g_laser_start_mask_ms > 0U))
  {
    g_laser_start_mask_ms--;

    if (g_laser_start_mask_ms == 0U)
    {
      if (HAL_GPIO_ReadPin(STOP_GPIO_Port, STOP_Pin) == GPIO_PIN_RESET)
      {
        Laser_Emergency_Kill();
      }
      else
      {
        if (Laser_Enable_Stop_EXTI() != 0U)
        {
          g_laser_state = LASER_STATE_RUNNING;
        }
        else
        {
          Laser_Emergency_Kill();
        }
      }
    }
  }

  Laser_Process_Stop_Fault();

#if LASER_BENCH_MODE != 0U
  Laser_Process_Bench();
#endif
  Laser_Process_Current_LED();
  Laser_Process_Fault_LED();
  /* Publish progress only after every TIM6 task has returned. */
  g_tim6_completed++;
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
  if (GPIO_Pin == STOP_Pin)
  {
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    Laser_Disable_Stop_EXTI();

    if (g_laser_state == LASER_STATE_RUNNING)
    {
      if (g_laser_fault_debounce_ms == 0U)
      {
        g_laser_fault_debounce_ms = LASER_FAULT_DEBOUNCE_MS;
      }
    }
    else
    {
      g_laser_fault_debounce_ms = 0U;
    }
    if (primask == 0U)
    {
      __enable_irq();
    }
  }
  else if (GPIO_Pin == SHOOT_Pin)
  {
    Laser_Disable_Shoot_EXTI();

    if (g_laser_shoot_enabled != 0U)
    {
      g_laser_shoot_debounce_ms = LASER_SHOOT_DEBOUNCE_MS;
    }
  }
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  Laser_Fatal_Shutdown();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
