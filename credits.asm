org   0x0000

BITS 16
CPU 8086


; d 18A6:56B0
section .newdata start=0x56B0

orig_timer_counter: dw 0
game_timer_counter: dw 0


absolute 0x1d04 
s_game_update_0_1D04: ;ret



; 3 bytes
section .call_credits_init start=0x3eb7
    call credits_init
    nop
    nop
    nop

; 3 bytes
section .call_credits_start start=0x3ecb
    call credits_start
    nop
    nop
    nop

; 4 bytes
section .call_credits_end start=0x3f71
    call credits_end
    nop
    nop
    nop
    nop




section .credits_timing start=0x4210

credits_init:
    mov  word [ds:game_timer_counter], 0

    ;; original instr
    mov     [bp-0Ah], ax
    retn

credits_start:
    call near wait_for_vertical_retrace

    ;; original instr
    mov     ax, 68h ; 'h'
    retn

credits_end:
    push bx
    mov bx, 0Ah
    call near do_delay
    pop bx

    ;; original instr
    cmp     word  [bp-0Ah], 1
    retn


%include "common.asm"
