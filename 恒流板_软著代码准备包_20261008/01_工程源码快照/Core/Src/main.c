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
// 测试模式 (K2 在 CubeMX 里引脚名叫 KEY1)
// 0: 按住K2出光, 松手关
// 1: 按一下开, 再按一下关
// 2: 按一下开始循环, 开1s关100ms, 再按一下停
#ifndef BENCH_MODE
#define BENCH_MODE        1
#endif
#if BENCH_MODE > 2
#error "BENCH_MODE must be 0, 1 or 2"
#endif

#define TEST_DAC_VALUE    3645    // K2测试时的DAC设定值
#define BENCH_ON_MS       1000
#define BENCH_OFF_MS      100

// SHOOT外部控制 1: 出光跟着SHOOT电平走, K2只能停  0: 不用SHOOT
#ifndef SHOOT_CTRL
#define SHOOT_CTRL        0
#endif
#define SHOOT_DAC_VALUE   TEST_DAC_VALUE  // 第一次接激光器先改成1215(约6A)

#define KEY_DEBOUNCE_MS   20      // 按键消抖
#define SHOOT_DEBOUNCE_MS 5       // SHOOT输入消抖
#define FAULT_FILTER_MS   5       // STOP连续低5ms才算故障
#define FAULT_BLINK_MS    250     // 故障时指示灯闪烁间隔

#define DAC_STEP          50      // DAC缓升, 每ms加50
#define START_MASK_EXTRA  100     // 启动屏蔽 = 缓升时间 + 100ms
#define START_MASK_MAX    200     // 屏蔽时间最长200ms

#define CUR_OK_MS         100     // 电流正常持续100ms才亮灯
#define CUR_TIMEOUT_MS    5       // 采样超过5ms没更新就不算
#define CUR_TOL_PCT       20      // 允许偏差 +-20%

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
volatile LaserState_t laser_state = LASER_IDLE;
volatile uint16_t start_mask_cnt = 0;      // 启动屏蔽倒计时
volatile uint16_t fault_cnt = 0;           // STOP低电平滤波计数
volatile uint16_t shoot_dac = 0;           // SHOOT触发用的DAC值, 0=不出光

static volatile uint16_t dac_target = 0;
static volatile uint16_t dac_now = 0;
static volatile uint16_t led_blink_cnt = 0;

static volatile uint8_t  shoot_en = 0;
static volatile uint8_t  shoot_active = 1; // 消抖后的SHOOT, 1=有信号
static volatile uint16_t shoot_cnt = 0;
static volatile uint8_t  shoot_on_req = 0;

static volatile uint16_t key_cnt = 0;
static volatile uint8_t  key_down = 0;     // 消抖后确认按下
static volatile uint8_t  key_req = 0;      // 请求主循环启动
static volatile uint8_t  key_wait_up = 0;  // 要先松开按键

// ISMON电流采样, 调试时在Watch窗口看
volatile uint16_t ismon_adc = 0;
volatile uint16_t ismon_target = 0;
volatile uint8_t  ismon_ok = 0;
static volatile uint16_t ismon_age = CUR_TIMEOUT_MS;
static volatile uint16_t ismon_good_cnt = 0;

static volatile uint32_t tim6_cnt = 0;     // TIM6任务执行次数, 喂狗用
static uint32_t wdg_last_cnt = 0;

#if BENCH_MODE != 0
static volatile uint8_t  bench_run = 0;
static volatile uint16_t bench_time = 0;
#endif

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
static void DAC_SetValue(uint16_t val);
static void TIM6_Start_1ms(void);
static void Stop_IT_Off(void);
static uint8_t Stop_IT_On(void);
static uint16_t Calc_Mask_Time(uint16_t dac);
static void DAC_Ramp(void);
static void Stop_Check(void);
static void Shoot_Debounce(void);
static void Shoot_Task(void);
static void Key_Scan(void);
static void Key_Task(void);
static void Current_Sample(void);
static void Current_LED_Update(void);
static void Fault_LED_Blink(void);
static void IWDG_Feed(void);
#if BENCH_MODE != 0
static void Bench_Task(void);
#endif

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static void DAC_SetValue(uint16_t val)
{
  if (val > 4095) val = 4095;

  if (HAL_DAC_SetValue(&hdac1, DAC_CHANNEL_1, DAC_ALIGN_12B_R, val) != HAL_OK)
  {
    Error_Handler();
  }
}

// TIM6配成1ms中断, 分频按实际PCLK1算
static void TIM6_Start_1ms(void)
{
  uint32_t clk = HAL_RCC_GetPCLK1Freq();

  // APB1有分频时定时器时钟x2
  if ((RCC->CFGR & RCC_CFGR_PPRE1) != 0)
  {
    clk *= 2;
  }

  __HAL_TIM_DISABLE(&htim6);
  __HAL_TIM_DISABLE_IT(&htim6, TIM_IT_UPDATE);
  __HAL_TIM_SET_PRESCALER(&htim6, clk / 1000000 - 1);   // 1MHz
  __HAL_TIM_SET_AUTORELOAD(&htim6, 1000 - 1);           // 1ms
  __HAL_TIM_SET_COUNTER(&htim6, 0);
  HAL_TIM_GenerateEvent(&htim6, TIM_EVENTSOURCE_UPDATE);
  __HAL_TIM_CLEAR_FLAG(&htim6, TIM_FLAG_UPDATE);

  if (HAL_TIM_Base_Start_IT(&htim6) != HAL_OK)
  {
    Error_Handler();
  }
}

static void Stop_IT_Off(void)
{
  EXTI->IMR1 &= ~(uint32_t)STOP_Pin;
  __HAL_GPIO_EXTI_CLEAR_IT(STOP_Pin);
  HAL_NVIC_ClearPendingIRQ(STOP_EXTI_IRQn);
}

// 打开STOP中断, 返回0说明STOP现在就是低电平, 没有打开
static uint8_t Stop_IT_On(void)
{
  __HAL_GPIO_EXTI_CLEAR_IT(STOP_Pin);
  HAL_NVIC_ClearPendingIRQ(STOP_EXTI_IRQn);

  if (HAL_GPIO_ReadPin(STOP_GPIO_Port, STOP_Pin) == GPIO_PIN_RESET)
  {
    return 0;
  }
  EXTI->IMR1 |= (uint32_t)STOP_Pin;
  return 1;
}


// 启动屏蔽时间: DAC缓升要的时间再加100ms, 最多200ms
static uint16_t Calc_Mask_Time(uint16_t dac)
{
  uint32_t t = ((uint32_t)dac + DAC_STEP - 1) / DAC_STEP + START_MASK_EXTRA;

  if (t > START_MASK_MAX) t = START_MASK_MAX;
  return (uint16_t)t;
}

// DAC缓升
static void DAC_Ramp(void)
{
  uint16_t next;

  if (laser_state != LASER_STARTING && laser_state != LASER_RUNNING)
    return;
  if (dac_now >= dac_target)
    return;

  next = dac_now + DAC_STEP;
  if (next < dac_now || next > dac_target)
  {
    next = dac_target;
  }
  dac_now = next;
  DAC_SetValue(next);
}

// TIM6里轮询STOP脚, 和STOP中断共用fault_cnt
// 连续5次(5ms)都是低电平才锁故障
static void Stop_Check(void)
{
  if (laser_state != LASER_RUNNING)
  {
    return;
  }

  if (HAL_GPIO_ReadPin(STOP_GPIO_Port, STOP_Pin) == GPIO_PIN_RESET)
  {
    if (fault_cnt == 0)
    {
      Stop_IT_Off();
      fault_cnt = FAULT_FILTER_MS;
    }
    fault_cnt--;
    if (fault_cnt == 0)
    {
      Laser_Fault_Lock();
    }
  }
  else if (fault_cnt != 0)
  {
    // 低电平没持续够, 当干扰处理, 重新开中断
    fault_cnt = 0;
    if (Stop_IT_On() == 0)
    {
      // 开中断时又变低了, 重新计数
      fault_cnt = FAULT_FILTER_MS;
    }
  }
}

// SHOOT 1ms读一次, 连续5ms一样才认
// 光耦TLP2761是反相的, 外部有信号时PA8是低, 断线就是高
static void Shoot_Debounce(void)
{
  uint8_t now;

  if (!shoot_en)
    return;

  now = (HAL_GPIO_ReadPin(SHOOT_GPIO_Port, SHOOT_Pin) == GPIO_PIN_RESET) ? 1 : 0;
  if (now == shoot_active)
  {
    shoot_cnt = 0;
  }
  else if (++shoot_cnt >= SHOOT_DEBOUNCE_MS)
  {
    shoot_cnt = 0;
    shoot_active = now;
    shoot_on_req = now;   // 只有 无->有 才请求启动
  }

  // 信号撤了直接关. fault_cnt不为0是STOP在滤波, 等它判完
  if (!shoot_active && fault_cnt == 0 &&
      (laser_state == LASER_STARTING || laser_state == LASER_RUNNING))
  {
    Laser_Stop();
  }
}

// 主循环里处理SHOOT启动
static void Shoot_Task(void)
{
  uint32_t irq = __get_PRIMASK();

  __disable_irq();
  if (shoot_on_req)
  {
    shoot_on_req = 0;
    // 再确认下信号还在
    if (shoot_en && shoot_active && shoot_dac > 0)
      Laser_Start(shoot_dac);
  }
  __set_PRIMASK(irq);
}

// K2按键扫描, TIM6里1ms调用一次
static void Key_Scan(void)
{
  if (HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == GPIO_PIN_RESET)
  {
    if (key_wait_up)
    {
      key_cnt = 0;
      return;
    }
    if (key_down)
      return;

    if(key_cnt < KEY_DEBOUNCE_MS)
      key_cnt++;
    if (key_cnt >= KEY_DEBOUNCE_MS)
    {
      key_down = 1;
#if SHOOT_CTRL
      shoot_on_req = 0;
      Laser_Stop();     // SHOOT控制时K2只当停止键
#elif BENCH_MODE != 0
      if (bench_run)
      {
        Laser_Stop();   // 在中断里直接关, 不等主循环
      }
      else if (laser_state == LASER_IDLE)
      {
        bench_run = 1;
        bench_time = 0;
        key_req = 1;
      }
#else
      key_req = 1;
#endif
    }
  }
  else
  {
    key_cnt = 0;
    key_wait_up = 0;
    if (key_down)
    {
      key_down = 0;
#if BENCH_MODE == 0 && SHOOT_CTRL == 0
      key_req = 0;
      Laser_Stop();     // 松手就关, 也放在中断里
#endif
    }
  }
}

static void Key_Task(void)
{
  uint32_t irq = __get_PRIMASK();

  __disable_irq();
  if (key_req)
  {
    key_req = 0;
    // 关中断后再确认一次, 防止中断里已经要停了这里又去启动
#if BENCH_MODE != 0
    if (bench_run)
#else
    if (key_down && !key_wait_up &&
        HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == GPIO_PIN_RESET)
#endif
    {
      Laser_Start(TEST_DAC_VALUE);
#if BENCH_MODE != 0
      bench_time = 0;   // 从真正出光开始计时
#endif
    }
  }
  __set_PRIMASK(irq);
}

#if BENCH_MODE != 0
static void Bench_Task(void)
{
  if (!bench_run)
    return;

#if BENCH_MODE == 2
  // 上次的启动请求主循环还没处理, 先不计时
  if (key_req)
    return;

  if(bench_time < 0xFFFF)
    bench_time++;

  if (laser_state == LASER_IDLE)
  {
    if (bench_time >= BENCH_OFF_MS)
      key_req = 1;
  }
  else if (bench_time >= BENCH_ON_MS)
  {
    // STOP还在滤波就先不关, 不然Laser_Stop会把fault_cnt清掉
    if (fault_cnt != 0)
      return;
    Laser_Stop();
    if (laser_state == LASER_IDLE)
      bench_run = 1;    // Laser_Stop会清bench_run, 正常循环要再置1
  }
#endif
}
#endif

// 主循环里每ms采一次ISMON, 轮询方式, 不放到TIM6中断里
static void Current_Sample(void)
{
  static uint32_t last_tick = 0xFFFFFFFF;
  uint32_t now = HAL_GetTick();
  uint32_t irq;
  uint16_t raw = 0;
  uint8_t ok = 0;

  if(now == last_tick)
    return;
  last_tick = now;

  if (HAL_ADC_Start(&hadc1) == HAL_OK)
  {
    if (HAL_ADC_PollForConversion(&hadc1, 1) == HAL_OK)
    {
      raw = (uint16_t)HAL_ADC_GetValue(&hadc1);
      ok = 1;
    }
  }
  if (HAL_ADC_Stop(&hadc1) != HAL_OK)
    ok = 0;

  // len = sprintf(buf, "adc=%d\r\n", raw);
  // HAL_UART_Transmit(&huart3, (uint8_t *)buf, len, 10);

  irq = __get_PRIMASK();
  __disable_irq();
  ismon_adc = raw;
  ismon_ok = ok;
  ismon_age = 0;
  if (!ok)
    ismon_good_cnt = 0;
  __set_PRIMASK(irq);
}

// 出光时电流在目标值+-20%以内持续100ms, 指示灯亮
static void Current_LED_Update(void)
{
  uint32_t meas, target;

  if (ismon_age < CUR_TIMEOUT_MS)
    ismon_age++;

  /* 换算: CTRL = 30*Rs*I, ISMON = 20*Rs*I
   * ISMON经R2/R19(10k/8.2k)分压进ADC, ADC和DAC共用VREF+
   * 目标ADC = DAC * (8.2/18.2) * (20/30) = DAC * 82 / 273
   * TODO: 按电阻标称值算的, 没有实际标定过
   */
  target = (uint32_t)dac_target * 82;
  ismon_target = (uint16_t)((target + 136) / 273);
  meas = (uint32_t)ismon_adc * 273 * 100;

  if (laser_state == LASER_RUNNING && target > 0 && fault_cnt == 0 &&
      HAL_GPIO_ReadPin(STOP_GPIO_Port, STOP_Pin) == GPIO_PIN_SET &&
      ismon_ok && ismon_age < CUR_TIMEOUT_MS &&
      meas >= target * (100 - CUR_TOL_PCT) &&
      meas <= target * (100 + CUR_TOL_PCT))
  {
    if (ismon_good_cnt < CUR_OK_MS)
      ismon_good_cnt++;
  }
  else
  {
    ismon_good_cnt = 0;
  }

  // 故障时灯给Fault_LED_Blink用
  if (laser_state != LASER_FAULT)
  {
    HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin,
                      ismon_good_cnt >= CUR_OK_MS ? GPIO_PIN_SET : GPIO_PIN_RESET);
  }
}

// 故障锁存后指示灯250ms翻转一次
static void Fault_LED_Blink(void)
{
  if (laser_state != LASER_FAULT)
    return;

  if (led_blink_cnt > 0)
    led_blink_cnt--;

  if (led_blink_cnt == 0)
  {
    HAL_GPIO_TogglePin(R_EN_GPIO_Port, R_EN_Pin);
    led_blink_cnt = FAULT_BLINK_MS;
  }
}

// TIM6任务完整跑完一次才喂一次狗
static void IWDG_Feed(void)
{
  uint32_t cnt = tim6_cnt;

  if (cnt != wdg_last_cnt)
  {
    wdg_last_cnt = cnt;
    HAL_IWDG_Refresh(&hiwdg);
  }
}

// 放在MX_xxx_Init后面调
void Laser_Init(void)
{
  laser_state = LASER_IDLE;
  start_mask_cnt = 0;
  fault_cnt = 0;
  dac_target = 0;
  dac_now = 0;
  led_blink_cnt = 0;

  shoot_en = 0;
  shoot_active = 1;
  shoot_cnt = 0;
  shoot_on_req = 0;

  key_cnt = 0;
  key_down = 0;
  key_req = 0;
  // 上电时K2就按着的话要先松开, 防止一上电就出光
  key_wait_up = (HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == GPIO_PIN_RESET) ? 1 : 0;
#if BENCH_MODE != 0
  bench_run = 0;
  bench_time = 0;
#endif

  ismon_adc = 0;
  ismon_target = 0;
  ismon_ok = 0;
  ismon_age = CUR_TIMEOUT_MS;
  ismon_good_cnt = 0;
  tim6_cnt = 0;
  wdg_last_cnt = 0;

  Stop_IT_Off();
  HAL_GPIO_WritePin(PWM_GPIO_Port, PWM_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_RESET);

  // 先写0再打开DAC输出, 避免PA4输出不确定
  DAC_SetValue(0);
  if (HAL_DAC_Start(&hdac1, DAC_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  DAC_SetValue(0);

  TIM6_Start_1ms();
}

/**
  * @brief  SHOOT外部控制 1开 0关, 故障时开不了
  * @note   上电时信号已经在的话不出光, 要撤掉再给一次
  */
void Shoot_Enable(uint8_t en)
{
  uint32_t irq = __get_PRIMASK();

  __disable_irq();
  shoot_cnt = 0;
  shoot_on_req = 0;
  shoot_active = 1;
  shoot_en = (en && laser_state != LASER_FAULT) ? 1 : 0;
  __set_PRIMASK(irq);
}

/**
  * @brief  开始出光, PWM拉高, DAC从0缓升到目标值
  * @param  dac: 目标DAC值 0~4095
  * @note   只有空闲状态能启动, 启动后屏蔽一段时间再检测STOP
  */
void Laser_Start(uint16_t dac)
{
  uint32_t irq = __get_PRIMASK();

  __disable_irq();
  if (laser_state != LASER_IDLE)
  {
    __set_PRIMASK(irq);
    return;
  }

  if (dac > 4095) dac = 4095;

  Stop_IT_Off();
  fault_cnt = 0;
  led_blink_cnt = 0;
  dac_target = dac;
  dac_now = 0;
  ismon_ok = 0;
  ismon_good_cnt = 0;
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_RESET);

  DAC_SetValue(0);
  HAL_GPIO_WritePin(PWM_GPIO_Port, PWM_Pin, GPIO_PIN_SET);

  start_mask_cnt = Calc_Mask_Time(dac);
  laser_state = LASER_STARTING;

  __set_PRIMASK(irq);
}

// 正常关断, 故障锁存时不管
void Laser_Stop(void)
{
  uint32_t irq = __get_PRIMASK();

  __disable_irq();
#if BENCH_MODE != 0
  bench_run = 0;
  bench_time = 0;
  key_req = 0;
#endif

  if (laser_state == LASER_FAULT)
  {
    __set_PRIMASK(irq);
    return;
  }

  Stop_IT_Off();

  laser_state = LASER_IDLE;
  start_mask_cnt = 0;
  fault_cnt = 0;
  led_blink_cnt = 0;
  dac_target = 0;
  dac_now = 0;

  PWM_GPIO_Port->BRR = PWM_Pin;
  DAC_SetValue(0);
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_RESET);

  __set_PRIMASK(irq);
}

/**
  * @brief  故障关断并锁存
  * @note   锁存后按键和SHOOT都不能再启动, 要Laser_Fault_Clear或者复位
  */
void Laser_Fault_Lock(void)
{
#if BENCH_MODE != 0
  bench_run = 0;
  bench_time = 0;
#endif
  Stop_IT_Off();

  PWM_GPIO_Port->BRR = PWM_Pin;
  DAC_SetValue(0);

  start_mask_cnt = 0;
  fault_cnt = 0;
  dac_target = 0;
  dac_now = 0;
  shoot_cnt = 0;
  shoot_en = 0;
  shoot_active = 1;
  shoot_on_req = 0;
  key_cnt = 0;
  key_down = 0;
  key_req = 0;
  key_wait_up = 1;
  led_blink_cnt = FAULT_BLINK_MS;
  laser_state = LASER_FAULT;

  // 先点亮, 后面TIM6里Fault_LED_Blink负责闪
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_SET);
}

/**
  * @brief  清除故障锁存, 回到空闲
  * @retval 1
  */
uint8_t Laser_Fault_Clear(void)
{
  if (laser_state != LASER_FAULT)
    return 1;

  Stop_IT_Off();

  PWM_GPIO_Port->BRR = PWM_Pin;
  DAC_SetValue(0);

  start_mask_cnt = 0;
  fault_cnt = 0;
  dac_target = 0;
  dac_now = 0;
  shoot_cnt = 0;
  shoot_en = 0;
  shoot_active = 1;
  shoot_on_req = 0;
  key_cnt = 0;
  key_down = 0;
  key_req = 0;
  key_wait_up = 1;    // 清完故障也要先松开按键

  led_blink_cnt = 0;
  laser_state = LASER_IDLE;
  HAL_GPIO_WritePin(R_EN_GPIO_Port, R_EN_Pin, GPIO_PIN_RESET);
  return 1;
}

/**
  * @brief  异常处理里用, 直接写寄存器关输出
  * @note   不调用HAL, 关中断后不再打开
  */
void Laser_Force_Off(void)
{
  __disable_irq();

  // GPIOA时钟没开说明PA9还没初始化
  if (RCC->AHB2ENR & RCC_AHB2ENR_GPIOAEN)
  {
    PWM_GPIO_Port->BRR = PWM_Pin;
  }
  // DAC没开触发, 写DHR就直接更新输出
  if (RCC->AHB2ENR & RCC_AHB2ENR_DAC1EN)
  {
    DAC1->DHR12R1 = 0;
  }
  if (RCC->AHB2ENR & RCC_AHB2ENR_GPIOCEN)
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
  Laser_Init();
#if SHOOT_CTRL
  shoot_dac = SHOOT_DAC_VALUE;
  Shoot_Enable(1);
#else
  shoot_dac = 0;
  Shoot_Enable(0);    // SHOOT外部触发暂时不用
#endif

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    Key_Task();
    Shoot_Task();
    Current_Sample();
    IWDG_Feed();
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
// TIM6 1ms中断: 消抖, DAC缓升, 启动屏蔽, STOP检测, 指示灯
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  if (htim->Instance != TIM6)
    return;

  Shoot_Debounce();
  Key_Scan();
  DAC_Ramp();

  // 屏蔽时间到, STOP正常就进入RUNNING并打开STOP中断
  if (laser_state == LASER_STARTING && start_mask_cnt > 0)
  {
    start_mask_cnt--;
    if (start_mask_cnt == 0)
    {
      if (HAL_GPIO_ReadPin(STOP_GPIO_Port, STOP_Pin) == GPIO_PIN_RESET)
        Laser_Fault_Lock();
      else if (Stop_IT_On())
        laser_state = LASER_RUNNING;
      else
        Laser_Fault_Lock();
    }
  }

  Stop_Check();
#if BENCH_MODE != 0
  Bench_Task();
#endif
  Current_LED_Update();
  Fault_LED_Blink();

  tim6_cnt++;   // 放最后, 前面全部执行完才算一次
}

// 现在只有STOP用外部中断, SHOOT改到TIM6里轮询了
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
  if (GPIO_Pin == STOP_Pin)
  {
    // STOP下降沿: 先关中断, 滤波交给TIM6里的Stop_Check
    uint32_t irq = __get_PRIMASK();
    __disable_irq();
    Stop_IT_Off();
    if (laser_state == LASER_RUNNING)
    {
      if (fault_cnt == 0)
        fault_cnt = FAULT_FILTER_MS;
    }
    else
    {
      fault_cnt = 0;
    }
    __set_PRIMASK(irq);
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
  Laser_Force_Off();
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
