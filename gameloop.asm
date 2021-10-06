org   0x0000

BITS 16
CPU 8086


; d 18A6:56B0
section .newdata start=0x56B0

orig_timer_counter: dw 0
game_timer_counter: dw 0


absolute 0x1d04 
s_game_update_0_1D04: ;ret


section .call_wrapped_0 start=0x3c97
    call wrapped_game_update

section .call_wrapped_1 start=0x3d44
    call wrapped_game_update

section .call_wrapped_2 start=0x3d71
    call wrapped_game_update


section .new_game_update start=0x3e10

wrapped_game_update:
        call near wait_for_vertical_retrace
        call near s_game_update_0_1D04
        push bx
        mov bx, 0Ah
        call near do_delay
        pop bx
        retn

%include "common.asm"
