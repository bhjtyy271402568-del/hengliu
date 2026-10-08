/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32g4xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */
typedef enum
{
  LASER_IDLE = 0,     // 空闲
  LASER_STARTING,     // 启动中, DAC缓升+屏蔽STOP
  LASER_RUNNING,      // 正常出光
  LASER_FAULT         // 故障锁存
} LaserState_t;

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */
void Laser_Init(void);
void Laser_Start(uint16_t dac);
void Laser_Stop(void);
void Laser_Fault_Lock(void);
uint8_t Laser_Fault_Clear(void);
void Laser_Force_Off(void);
void Shoot_Enable(uint8_t en);

extern volatile LaserState_t laser_state;
extern volatile uint16_t start_mask_cnt;
extern volatile uint16_t fault_cnt;
extern volatile uint16_t shoot_dac;

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define R_EN_Pin GPIO_PIN_13
#define R_EN_GPIO_Port GPIOC
#define CTRL1_Pin GPIO_PIN_4
#define CTRL1_GPIO_Port GPIOA
#define RGB_LED_Pin GPIO_PIN_5
#define RGB_LED_GPIO_Port GPIOA
#define STOP_Pin GPIO_PIN_12
#define STOP_GPIO_Port GPIOB
#define STOP_EXTI_IRQn EXTI15_10_IRQn
#define ISMON_Pin GPIO_PIN_14
#define ISMON_GPIO_Port GPIOB
#define IVINMON_Pin GPIO_PIN_15
#define IVINMON_GPIO_Port GPIOB
#define KEY1_Pin GPIO_PIN_9
#define KEY1_GPIO_Port GPIOC
#define SHOOT_Pin GPIO_PIN_8
#define SHOOT_GPIO_Port GPIOA
#define SHOOT_EXTI_IRQn EXTI9_5_IRQn
#define PWM_Pin GPIO_PIN_9
#define PWM_GPIO_Port GPIOA

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
