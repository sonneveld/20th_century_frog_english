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
        call near vsync_wait
        call near s_game_update_0_1D04
        call near do_delay
        retn

vsync_wait:
                cli
                push dx
                push ax

                mov     dx, 3DAh        ; Video status bits:
                                        ; 3: 1=vertical sync pulse is occurring.

wait_until_no_vsync:                             
                in      al, dx          
                and     al, 8
                jnz     wait_until_no_vsync


wait_until_vsync:                               
                in      al, dx         
                and     al, 8
                jz      wait_until_vsync

                pop ax
                pop dx
                sti
                retn

do_delay:

        push ds
        push ax

        mov ax, 0xDEAD ; dseg
        mov ds, ax

        delay_loop:
        cmp word [ds:game_timer_counter], 9h
        jb      delay_loop

        mov  word [ds:game_timer_counter], 0

        pop ax
        pop ds

        retn
