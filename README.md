# lcd-ws0010
Library for Winstar Display Controller WS0010

Algorithm for 4-bit mode via PCF8574 in short.
## High nibble
1) Copy command byte to _var1_, shift _var1_ 4 times to the right (>>)
2) Write _var1_ to I2C bus
3) Set bit 6 (0x40) in _var1_
4) Write _var1_ to I2C bus
5) Clear bit 6 (0x40) in _var1_
6) Write _var1_ to I2C bus
## Low nibble
7) Copy command byte to _var1_, clear high nibble of _var1_
8) Write _var1_ to I2C bus
9) Set bit 6 (0x40) in _var1_
10) Write _var1_ to I2C bus
11) Clear bit 6 (0x40) in _var1_
12) Write _var1_ to I2C bus
## Check busy flag
...
