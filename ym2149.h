#ifndef __YM2149_H__
#define __YM2149_H__

#include <Arduino.h>

void YMSetClk2MHz(void);
void YMSetBusCtl();
void YMWriteData(char addr, char data);

#endif