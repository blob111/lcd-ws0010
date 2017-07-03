# lcd-ws0010
Library for Winstar Display Controller WS0010

I. Algorithm for 4-bit mode via PCF8574 in short.

## Write high nibble of command byte
1) Copy command byte to _var1_, shift _var1_ 4 times to the right (>>)
2) Write _var1_ to I2C bus
3) Set bit 6 (EN) in _var1_
4) Write _var1_ to I2C bus
5) Clear bit 6 (EN) in _var1_
6) Write _var1_ to I2C bus

## Write low nibble of command byte
7) Copy command byte to _var1_, clear high nibble of _var1_
8) Write _var1_ to I2C bus
9) Set bit 6 (EN) in _var1_
10) Write _var1_ to I2C bus
11) Clear bit 6 (EN) in _var1_
12) Write _var1_ to I2C bus

## Check busy flag
13) Zeroize _var1_
14) Set bit 5 (R/W) in _var1_
15) Write _var1_ to I2C bus
16) Set bit 6 (EN) in _var1_
17) Write _var1_ to I2C bus
18) Read byte from I2C bus into _var2_
19) Clear bit 6 (EN) in _var1_
20) Write _var1_ to I2C bus
21) Shift _var2_ 4 times to the left (<<)
22) Set bit 6 (EN) in _var1_
23) Write _var1_ to I2C bus
24) Read byte from I2C bus into _var3_
25) Clear bit 6 (EN) in _var1_
26) Write _var1_ to I2C bus
27) Clear high nibble of _var3_
28) Logically OR _var2_ and _var3_, save result to _var2_
29) Test bit 7 (BF, Busy Flag) in _var2_
30) If bit 7 set, sleep _WAIT_BF_, go to step 13
31) If bit 7 cleared, go further
32) Zeroize _var1_
33) Write _var1_ to I2C bus

## Steps 3-6 and 9-12 are identical and can be implemented as a separate procedure

II. Initialization sequence for 4-bit mode.

## Synchronization
1) Write 0x0 nibble __5 times__

## Function set
## Two lines (bit 3, N=1), 5x8 font size (bit 2, F=0), EN/RU character font table (bits 1 and 0, FT1=1, FT0=0)
2) Write high nibble of command byte as 0x2 (DL=0) __2 times__
3) Write low nibble of command byte as 0xA (N=1, F=0, FT1=1, FT0=0)
4) Check BF

## Display ON/OFF Control
## Display on (bit 2, D=1), cursor on (bit 1, C=1), blinking on (bit 0, B=1)
5) Write high nibble of command byte as 0x0
6) Write low nibble of command byte as 0xF (D=1, C=1, B=1)
7) Check BF

## Clear Display
8) Write high nibble of command byte as 0x0
9) Write low nibble of command byte as 0x1
10) Check BF

## Return Home
11) Write high nibble of command byte as 0x0
12) Write low nibble of command byte as 0x2
13) Check BF

## Entry Mode Set
## Increment (bit 1, I/D=1), no shift (bit 0, S=0)
14) Write high nibble of command byte as 0x0
15) Write low nibble of command byte as 0x6 (I/D=1, S=0)
16) Check BF


...
