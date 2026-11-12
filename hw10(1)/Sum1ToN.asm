// Computes R1 = 1 + 2 + ... + R0

   @i
   M=1          // i = 1 (應分配到 RAM[16])
   @sum
   M=0          // sum = 0 (應分配到 RAM[17])
(LOOP)
   @i
   D=M          // D = i
   @R0
   D=D-M        // D = i - R0
   @STOP
   D;JGT        // if i > R0 goto STOP
   @sum
   D=M
   @i
   D=D+M
   @sum
   M=D          // sum = sum + i
   @i
   M=M+1        // i = i + 1
   @LOOP
   0;JMP
(STOP)
   @sum
   D=M
   @R1
   M=D          // RAM[1] = sum
(END)
   @END
   0;JMP