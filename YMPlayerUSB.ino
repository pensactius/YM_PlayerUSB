/*
 
*/
#include "ym2149.h"
#define LED PB5         // avr PB5 = Arduino D13
unsigned char data[16];


void setup() {

  Serial.begin(9600);  // Los datos se reciben por serie a 9600 bps.
  while (!Serial) {
    ;
  }
  
  DDRB |= _BV(LED);     // pinMode(LED, OUTPUT)
  
  YMSetClk2MHz ();      // Generate a 2MHz clk signal on D11
  YMSetBusCtl ();
  
  ClearRegisters();
  
}

void loop() {
    for (int i=0; i<16; i++)
    {
      while(!(Serial.available() > 0)){}
        data[i] = Serial.read();
    }
    
/* 
 Fill the "x" bits with the original chip value and set all other bits to 0.
	_________________________________________________
			      Frame register detail
		¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
		    b7 b6 b5 b4 b3 b2 b1 b0
		 r0 x  x  x  x  x  x  x  x   Period voice A
		 r1             x  x  x  x   Fine period voice A
		 r2 x  x  x  x  x  x  x  x   Period voice B
		 r3             x  x  x  x   Fine period voice B
		 r4 x  x  x  x  x  x  x  x   Period voice C
		 r5             x  x  x  x   Fine Period voice C
		 r6          x  x  x  x  x   Noise period
		 r7       x  x  x  x  x  x   Mixer control
		 r8          x  x  x  x  x   Volume control A
		 r9          x  x  x  x  x   Volume control B
		r10          x  x  x  x  x   Volume control C
		r11 x  x  x  x  x  x  x  x   Envelope high period
		r12 x  x  x  x  x  x  x  x   Envelope low period
		r13             x  x  x  x   Envelope shape
		r14			     Data of I/O port A
		r15			     Data of I/O port B
		_________________________________________________
*/
    for (int i = 0; i<14; i++)
    {      
      switch (i)
      {
        case 1:
        case 3:
        case 5:
        case 13:
          data[i] = data[i] & B00001111;
          break;
        case 6:        
        case 8:
        case 9:
        case 10:
          data[i] = data[i] & B00011111;
          break;
        case 7:
          data[i] = data[i] & B00111111;
          break;
      }
      YMWriteData(i, data[i]);
    }
    
    // Have LED blink with noise (drums)    
    if (~data[7] & 0x38) 
    {
      data[7] &= B11000111;
      PORTB |= _BV(LED);
    }
    else
    {
      PORTB &= ~_BV(LED);
    }
}

// -------------------------------------------------------------------
void ClearRegisters(void)
{
  for (int i=0; i<14; i++)
  {
    YMWriteData(i, 0);
  }
}
